from sqlalchemy.orm import Session
from statistics import mean
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import joinedload
from app.db.database import sessionLocal
from app.core.exceptions import NotFoundError
from app.db.models import Movie
from app.ml.model_loader import get_cf_model
from app.services.movie_service import attach_image_urls, _enriched_only

def _build_soup(movie: Movie) -> str:
    genre_names = [g.name for g in movie.genres]
    genre_text = " ".join(genre_names * 3)
    overview_text = movie.description or ""
    return f"{genre_text} {overview_text}".strip()

@lru_cache(maxsize=1)
def _get_content_matrix():
    db = sessionLocal()
    try:
        movies = (
            _enriched_only(db.query(Movie)).options(joinedload(Movie.genres)).all()
        )

        soups = [_build_soup(m) for m in movies]
        movie_ids = [m.id for m in movies]

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(soups)

        id_to_idx = {
            movie_id : idx for idx, movie_id in enumerate(movie_ids)
        }

        return matrix, movie_ids, id_to_idx

    finally:
        db.close()

def get_cf_recommendations(
    db: Session, movielens_user_id: int, n: int = 10
) -> tuple[bool, list[Movie]]:
    model = get_cf_model()

    trainset = model.trainset

    try:
        inner_uid = trainset.to_inner_uid(movielens_user_id)
    except ValueError:
        return False, []

    already_rated_inner_ids = {inner_iid for inner_iid, _ in trainset.ur[inner_uid]}
    already_rated_raw_ids = {
        trainset.to_raw_iid(iid) for iid in already_rated_inner_ids
    }

    all_raw_item_ids = set(trainset.all_items())
    all_raw_item_ids = {trainset.to_raw_iid(iid) for iid in all_raw_item_ids}
    candidate_movielens_ids = all_raw_item_ids - already_rated_raw_ids

    scored = [
        (movielens_id, model.predict(movielens_user_id, movielens_id).est)
        for movielens_id in candidate_movielens_ids
    ]

    scored.sort(key=lambda x: x[1], reverse=True)
    top_movielens_ids = [movielens_id for movielens_id, _ in scored[: n * 3]]

    movies = (
        _enriched_only(db.query(Movie))
        .filter(Movie.movielens_id.in_(top_movielens_ids))
        .all()
    )

    score_by_movielens_id = dict(scored)
    movies.sort(
        key=lambda m: score_by_movielens_id.get(m.movielens_id, 0), reverse=True
    )

    top_movies = [attach_image_urls(m) for m in movies[:n]]
    return True, top_movies


def get_popular_movies(
    db: Session, n: int = 10, min_votes_percentile: float = 0.60
) -> list[Movie]:
    """using imdb's weighted rating formula

    WR = (v / (v+m)) * R + (m / (v+m)) * C
    R = movie's own average rating
    v = movie's own vote count
    C = mean rating across the whole (enriched) catalog
    m = minimum-votes threshold, derived from the data itself

    """

    candidates = (
        _enriched_only(db.query(Movie))
        .filter(Movie.tmdb_vote_count.isnot(None), Movie.tmdb_vote_average.isnot(None))
        .all()
    )

    if not candidates:
        return []

    vote_counts = sorted(m.tmdb_vote_count for m in candidates)
    C = mean(m.tmdb_vote_average for m in candidates)
    m_threshold = vote_counts[int(len(candidates) * min_votes_percentile)]

    def weighted_rating(movie: Movie) -> float:
        v = movie.tmdb_vote_count
        R = movie.tmdb_vote_average
        return (v / (v + m_threshold)) * R + (m_threshold / (v + m_threshold)) * C

    scored = [(movie, weighted_rating(movie)) for movie in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    top_movies = [attach_image_urls(movie) for movie, _ in scored[:n]]
    return top_movies


def get_similar_movies(db: Session, movie_id: int, n:int = 10) ->list[Movie]:
    movie_exists =  db.query(Movie.id).filter(Movie.id==movie_id).first()
    if not movie_exists:
        raise NotFoundError("Movie not found")

    matrix, movie_ids, id_to_index = _get_content_matrix()

    if movie_id not in id_to_index:
        return []

    idx = id_to_index[movie_id]

    similarities = cosine_similarity(matrix[idx], matrix).flatten()

    ranked_indices = similarities.argsort()[::-1]
    top_indices = [i for i in ranked_indices if movie_ids[i] != movie_id][:n]
    top_movie_ids = [movie_ids[i] for i in top_indices]

    movies = _enriched_only(db.query(Movie)).filter(Movie.id.in_(top_movie_ids)).all()

    similarity_by_id = {movie_ids[i]: similarities[i] for i in top_indices}
    movies.sort(key=lambda m: similarity_by_id.get(m.id, 0), reverse=True)

    return [attach_image_urls(m) for m in movies]


