from app.core.config import settings
from app.db.models import Movie
from sqlalchemy.orm import Session, joinedload


def _build_image_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{settings.TMDB_IMAGE_BASE_URL}{path}"


def _attach_url(movie: Movie):
    movie.backdrop_url = _build_image_url(movie.backdrop_path)
    movie.poster_url = _build_image_url(movie.poster_path)


def get_all_movies(db: Session, skip: int = 0, limit: int = 20) -> list[Movie]:
    movies = db.query(Movie).offset(skip).limit(limit).all()

    return [_attach_url(m) for m in movies]


def get_movie_by_id(db: Session, movie_id: int) -> Movie | None:
    movie = (
        db.query(Movie)
        .options(joinedload(Movie.genres))
        .filter(Movie.id == movie_id)
        .first()
    )

    if movie:
        _attach_url(movie)
    return movie

