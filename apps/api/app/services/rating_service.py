from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Rating, Movie
from app.core.exceptions import NotFoundError
import logging
logger = logging.getLogger(__name__)

def upsert_rating(db: Session, user_id: int, movie_id: int, rating_value: float) -> Rating:
    movie_exists = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie_exists:
        raise NotFoundError("Movie not found")
    try:
        existing = db.query(Rating).filter(
            Rating.user_id == user_id, Rating.movie_id == movie_id
        ).first()
        if existing:
            logger.info("Updating rating - user=%s movie=%s rating=%s", user_id, movie_id, rating_value)
            existing.rating = rating_value
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
        logger.info("Creating rating - user=%s movie=%s rating=%s", user_id, movie_id, rating_value)
        new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating_value)
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        return new_rating
    except Exception:
        db.rollback()
        raise

def get_user_ratings(db: Session, user_id: int) -> list[Rating]:
    return db.query(Rating).filter(Rating.user_id == user_id).order_by(Rating.updated_at.desc()).all()

def get_user_rating_for_movie(db: Session, user_id: int, movie_id: int) -> Rating:
    rating = db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == movie_id).first()
    if not rating:
        raise NotFoundError("You haven't rated this movie")
    return rating

def delete_rating(db: Session, user_id: int, movie_id: int) -> None:
    existing = db.query(Rating).filter(
        Rating.user_id == user_id, Rating.movie_id == movie_id
    ).first()
    if not existing:
        raise NotFoundError("Rating not found")
    try:
        db.delete(existing)
        db.commit()
        logger.info("Rating deleted - user=%s movie=%s", user_id, movie_id)
    except Exception:
        db.rollback()
        raise