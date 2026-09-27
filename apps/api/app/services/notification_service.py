from collections import defaultdict
from sqlalchemy.orm import Session

from app.db.models import Movie, Rating, Notification, MovieStatus
from app.services.recommendation_service import _get_content_matrix

from openai import OpenAI
from app.core.config import settings

from datetime import date, timedelta


RELEVANCE_THRESHOLD = 0.55
RECENT_RELEASE_WINDOW_DAYS = 30


def get_pending_movies(db: Session, limit: int = 100) -> list[Movie]:
    today = date.today()
    cutoff = today - timedelta(days=RECENT_RELEASE_WINDOW_DAYS)

    return (
        db.query(Movie)
        .filter(
            Movie.poster_path.isnot(None),
            Movie.poster_path != "",
            Movie.notified_at.is_(None),
            Movie.released_on >= cutoff,
            Movie.released_on <= today,
            Movie.status == MovieStatus.released,
        )
        .order_by(Movie.released_on.desc())
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

    interested = {}

    for user_id, rated_movie_ids in ratings_by_user.items():
        candidates = [
            (rated_id, id_to_index[rated_id])
            for rated_id in rated_movie_ids
            if rated_id in id_to_index
        ]

        if not candidates:
            continue

        best_movie_id = None
        best_score = -1.0

        for rated_id, idx in candidates:
            semantic = float(embeddings[idx] @ embeddings[movie_idx])
            genre = float(genre_matrix[idx] @ genre_matrix[movie_idx])
            score = 0.6 * semantic + 0.4 * genre 

            if score > best_score:
                best_score = score
                best_movie_id = rated_id

        if best_score >= RELEVANCE_THRESHOLD:
            interested[user_id] = best_movie_id

    return interested


def notification_exists(db: Session, user_id: int, movie_id: int) -> bool:
    return (
        db.query(Notification.id)
        .filter(Notification.user_id == user_id, Notification.movie_id == movie_id)
        .first()
        is not None
    )

_llm_client = None


def _get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return _llm_client


def generate_notification_text(liked_movie_title: str, new_movie_title: str) -> str:
    client = _get_llm_client()

    prompt = (
        f"Write one short, friendly sentence (under 20 words) telling a movie fan "
        f"that a new movie called \"{new_movie_title}\" just released, and that it's "
        f"a good match because they loved \"{liked_movie_title}\". "
        f"No hashtags, no emojis, no exclamation marks. Just the sentence."
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""