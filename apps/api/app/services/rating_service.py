from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Rating, Movie

def upsert_rating(db:Session, user_id:int, movie_id:int, rating_value:float):
    movie_exists = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie_exists:
        raise ValueError("Movie not found")

    existing = db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == movie_id).first()

    if existing:
        existing.rating = rating_value
        existing.updated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return existing

    new_rating = Rating(user_id = user_id, movie_id = movie_id, rating = rating_value)
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating

def get_user_ratings(db:Session, user_id:int)->list[Rating]:
    return db.query(Rating).filter(Rating.user_id==user_id).order_by(Rating.updated_at.desc()).all()

def get_user_rating_for_movie(db:Session, user_id:int, movie_id)->Rating|None:
    return db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == movie_id).first()

def delete_rating(db:Session, user_id:int, movie_id:int)->bool:
    existing = db.query(Rating).filter(Rating.user_id== user_id, Rating.movie_id==movie_id).first()

    if not existing:
        return False

    db.delete(existing)
    db.commit()
    return True