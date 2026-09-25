from collections import defaultdict
from sqlalchemy.orm import Session

from app.db.models import Movie, Rating, Notification
from app.services.recommendation_service import _get_content_matrix

RELEVANCE_THRESHOLD = 0.55


def get_pending_movies(db: Session, limit: int = 100) -> list[Movie]:
    return (
        db.query(Movie)
        .filter(
            Movie.poster_path.isnot(None),
            Movie.poster != "",
            Movie.notified_at.is_(None),
        )
        .limit(limit)
        .all()
    )


def find_interested_users(
    db: Session, movie: Movie, min_rating: float = 4.0
) -> list[int]:
    embeddings, genre_matrix, movie_ids, id_to_index = _get_content_matrix()

    if movie.id not in id_to_index:
        return []
    movie_idx = id_to_index[movie.id]

    user_ratings = (
        db.query(Rating.user_id, Rating.movie_id)
        .filter(Rating.rating >= min_rating)
        .all()
    )

    ratings_by_user = defaultdict(list)

    for user_id, rated_movie_id in user_ratings:
        ratings_by_user[user_id].append(rated_movie_id)

    interested = []

    for user_id, rated_movie_ids in ratings_by_user.items():
        relevant_indices = [
            id_to_index[mid] for mid in rated_movie_ids if mid in id_to_index
        ]
        if not relevant_indices:
            continue

        semantic_scores = [
            float(embeddings[i] @ embeddings[movie_idx]) for i in relevant_indices
        ]
        genre_scores = [
            float(genre_matrix[i] @ genre_matrix[movie_idx]) for i in relevant_indices
        ]
        best_scores = max(
            0.6 * s + 0.4 * g for s, g in zip(semantic_scores, genre_scores)
        )

        if best_scores >= RELEVANCE_THRESHOLD:
            interested.append(user_id)

    return interested


def notification_exists(db: Session, user_id: int, movie_id: int) -> bool:
    return (
        db.query(Notification.id)
        .filter(Notification.user_id == user_id, Notification.movie_id == movie_id)
        .first()
        is not None
    )
