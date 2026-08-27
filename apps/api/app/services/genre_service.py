from sqlalchemy.orm import Session
from app.db.models import Genre
from app.schemas.genre import GenreCreate
import logging
logger = logging.getLogger(__name__)

def get_all_genres(db:Session)->list[Genre]:
    logger.info("Fetching all genres")
    return db.query(Genre).order_by(Genre.name).all()

def create_genre(db: Session, payload: GenreCreate) -> Genre:
    logger.info("Creating genre: %s", payload.name)
    try:
        genre = Genre(name=payload.name, slug=payload.slug)
        db.add(genre)
        db.commit()
        db.refresh(genre)
        logger.info("Genre created: %s (id=%s)", genre.name, genre.id)
        return genre
    except Exception:
        db.rollback()
        raise