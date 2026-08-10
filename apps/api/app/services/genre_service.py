from sqlalchemy.orm import Session
from app.db.models import Genre
from app.schemas.genre import GenreCreate

def get_all_genres(db:Session)->list[Genre]:
    return db.query(Genre).order_by(Genre.name).all()


def create_genre(db:Session, payload:GenreCreate)->Genre:
    genre = Genre(name = payload.name, slug = payload.slug)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre