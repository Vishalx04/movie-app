from app.core.config import settings
from app.db.models import Movie, Genre
from sqlalchemy.orm import Session, joinedload
from app.schemas.movie import MovieCreate
from app.core.exceptions import NotFoundError
import logging
logger = logging.getLogger(__name__)

def _build_image_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{settings.TMDB_IMAGE_BASE_URL}{path}"


def attach_image_urls(movie: Movie):
    movie.backdrop_url = _build_image_url(movie.backdrop_path)
    movie.poster_url = _build_image_url(movie.poster_path)
    return movie

def _enriched_only(query):
    return query.filter(Movie.poster_path.isnot(None), Movie.poster_path != "")

def get_all_movies(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    q: str | None = None,
    genre_id: int | None = None,
) -> list[Movie]:
    logger.info("Fetching movies skip=%s limit=%s q=%s genre_id=%s", skip, limit, q, genre_id)
    query = _enriched_only(db.query(Movie))
    if q:
        query = query.filter(Movie.title.ilike(f"%{q}%"))

    if genre_id:
        query = query.join(Movie.genres).filter(Genre.id == genre_id)

    movies = query.offset(skip).limit(limit).all()

    return [attach_image_urls(m) for m in movies]


def get_movie_by_id(db: Session, movie_id: int) -> Movie:
    query = _enriched_only(
        db.query(Movie)
        .options(joinedload(Movie.genres))
        .filter(Movie.id == movie_id)
    )
    movie = query.first()

    if not movie:
        logger.info("Movie not found: id=%s", movie_id)
        raise NotFoundError("Movie not found")
    attach_image_urls(movie)
    return movie


def create_movie(db: Session, payload: MovieCreate) -> Movie:
    logger.info("Creating movie: %s", payload.title)
    try:
        data = payload.model_dump(exclude={"genre_ids"})
        movie = Movie(**data)
        if payload.genre_ids:
            genres = db.query(Genre).filter(Genre.id.in_(payload.genre_ids)).all()
            movie.genres = genres
        db.add(movie)
        db.commit()
        db.refresh(movie)
        logger.info("Movie created: %s (id=%s)", movie.title, movie.id)
        return attach_image_urls(movie)
    except Exception:
        db.rollback()
        raise