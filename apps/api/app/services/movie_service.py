from app.core.config import settings
from app.db.models import Movie, Genre
from sqlalchemy.orm import Session, joinedload
from app.schemas.movie import MovieCreate


def _build_image_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{settings.TMDB_IMAGE_BASE_URL}{path}"


def _attach_url(movie: Movie):
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

    query = _enriched_only(db.query(Movie))
    if q:
        query = query.filter(Movie.title.ilike(f"{q}%"))

    if genre_id:
        query = query.join(Movie.genres).filter(Genre.id == genre_id)

    movies = query.offset(skip).limit(limit).all()

    return [_attach_url(m) for m in movies]


def get_movie_by_id(db: Session, movie_id: int) -> Movie | None:
    query = _enriched_only(
        db.query(Movie)
        .options(joinedload(Movie.genres))
        .filter(Movie.id == movie_id)
    )
    movie = query.first()

    if movie:
        _attach_url(movie)
    return movie


def create_movie(db: Session, payload: MovieCreate) -> Movie:
    data = payload.model_dump(exclude="genre_ids")
    movie = Movie(**data)

    if payload.genre_ids:
        genres = db.query(Genre).filter(Genre.id.in_(payload.genre_ids)).all()
        movie.genres = genres

    db.add(movie)
    db.commit()
    db.refresh(movie)
    return _attach_url(movie)
