from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Genre
from app.schemas.genre import GenreCreate

def get_all_genres(db:Session)->list[Genre]:
    return db.query(Genre).order_by(Genre.name).all()


def create_genre(db:Session, payload:GenreCreate)->Genre:
    genre = Genre(name = payload.name, slug = payload.slug)
    db.add(genre)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Genre name or slug already exists")
    db.refresh(genre)
    return genre