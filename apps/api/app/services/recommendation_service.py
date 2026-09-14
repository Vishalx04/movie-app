from sqlalchemy.orm import Session
from statistics import mean
from functools import lru_cache
from sqlalchemy.orm import joinedload
from app.db.database import sessionLocal
from app.core.exceptions import NotFoundError
from app.db.models import Movie
from app.ml.model_loader import get_cf_model
from app.services.movie_service import attach_image_urls, _enriched_only
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer

_embedding_model = None

CONTENT_CACHE_PATH = Path(__file__).resolve().parent.parent / "ml" / "models" / "content_matrix_cache.pkl"


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


@lru_cache(maxsize=1)
def _get_content_matrix():
    if CONTENT_CACHE_PATH.exists():
        with open(CONTENT_CACHE_PATH, "rb") as f:
            return pickle.load(f)

    db = sessionLocal()
    try:
        movies = (
            _enriched_only(db.query(Movie)).options(joinedload(Movie.genres)).all()
        )

        overviews = [m.description or "" for m in movies]
        model = _get_embedding_model()
        embeddings = model.encode(overviews, show_progress_bar=True, batch_size=64)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        all_genre_names = sorted({g.name for m in movies for g in m.genres})
        genre_index = {name: i for i, name in enumerate(all_genre_names)}
        genre_matrix = np.zeros((len(movies), len(all_genre_names)))
        for row, m in enumerate(movies):
            for g in m.genres:
                genre_matrix[row, genre_index[g.name]] = 1.0
        genre_norms = np.linalg.norm(genre_matrix, axis=1, keepdims=True)
        genre_norms[genre_norms == 0] = 1.0
        genre_matrix = genre_matrix / genre_norms

        movie_ids = [m.id for m in movies]
        id_to_index = {movie_id: idx for idx, movie_id in enumerate(movie_ids)}

        result = (embeddings, genre_matrix, movie_ids, id_to_index)

        CONTENT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTENT_CACHE_PATH, "wb") as f:
            pickle.dump(result, f)

        return result
    finally:
        db.close()

def get_similar_movies(
    db: Session, movie_id: int, n: int = 10, semantic_weight: float = 0.6
) -> list[Movie]:
    movie_exists = db.query(Movie.id).filter(Movie.id == movie_id).first()
    if not movie_exists:
        raise NotFoundError("Movie not found")

    embeddings, genre_matrix, movie_ids, id_to_idx = _get_content_matrix()

    if movie_id not in id_to_idx:
        return []

    idx = id_to_idx[movie_id]

    semantic_scores = embeddings @ embeddings[idx]
    genre_scores = genre_matrix @ genre_matrix[idx]

    genre_weight = 1.0 - semantic_weight
    combined_scores = semantic_scores * semantic_weight + genre_weight * genre_scores

    ranked_indices = combined_scores.argsort()[::-1]
    top_indices = [i for i in ranked_indices if movie_ids[i] != movie_id][:n]
    top_movie_ids = [movie_ids[i] for i in top_indices]

    movies = _enriched_only(db.query(Movie)).filter(Movie.id.in_(top_movie_ids)).all()

    score_by_id = {movie_ids[i]: combined_scores[i] for i in top_indices}
    movies.sort(key=lambda m: score_by_id.get(m.id, 0), reverse=True)

    return [attach_image_urls(m) for m in movies]


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

def get_hybrid_recommendations(
    db: Session, movielens_user_id: int, n: int = 10, cf_weight: float = 0.5
) -> tuple[bool, list[Movie]]:
  
    is_cf_personalized, cf_movies = get_cf_recommendations(db, movielens_user_id, n=n * 3)

    if not is_cf_personalized or not cf_movies:
        return False, []

    embeddings, genre_matrix, movie_ids, id_to_index = _get_content_matrix()

    model = get_cf_model()
    trainset = model.trainset
    inner_uid = trainset.to_inner_uid(movielens_user_id)
    rated = trainset.ur[inner_uid]
    if not rated:
        return False, []

    best_inner_iid, _ = max(rated, key=lambda x: x[1])
    best_movielens_id = trainset.to_raw_iid(best_inner_iid)

    anchor_movie = db.query(Movie).filter(Movie.movielens_id == best_movielens_id).first()
    if not anchor_movie or anchor_movie.id not in id_to_index:
        return True, cf_movies[:n]

    anchor_idx = id_to_index[anchor_movie.id]
    anchor_semantic = embeddings[anchor_idx]
    anchor_genre = genre_matrix[anchor_idx]

    def content_score(movie: Movie) -> float:
        if movie.id not in id_to_index:
            return 0.0
        idx = id_to_index[movie.id]
        semantic_sim = float(embeddings[idx] @ anchor_semantic)
        genre_sim = float(genre_matrix[idx] @ anchor_genre)
        return 0.6 * semantic_sim + 0.4 * genre_sim

    scored = [
        (movie, cf_weight * (1.0 - (rank / len(cf_movies))) + (1 - cf_weight) * content_score(movie))
        for rank, movie in enumerate(cf_movies)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    top_movies = [movie for movie, _ in scored[:n]]
    return True, top_movies