
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from app.schemas.genre import GenreResponse

class MovieCreate(BaseModel):
    tmdb_id: str
    imdb_id: str | None = None
    movielens_id: int | None = None

    title: str
    original_title: str | None = None
    tagline: str | None = None
    description: str | None = None

    runtime: int | None = None
    released_on: date | None = None

    poster_path: str | None = None
    backdrop_path: str | None = None
    original_language: str | None = None

    status: str = "Released"

    budget: int | None = None
    revenue: int | None = None
    adult: bool = False

    tmdb_vote_average: float | None = None
    tmdb_vote_count: int | None = None
    trailer_link: str | None = None

    genre_ids: list[int] = []

class MovieListItem(BaseModel):
    """Lighter shape for list views — no description, cast, platforms."""
    id: int
    tmdb_id: str
    title: str
    poster_url: str | None = None
    released_on: date | None = None
    tmdb_vote_average: float | None = None

    model_config = ConfigDict(from_attributes=True)

class MovieResponse(BaseModel):
    """Full shape for a single movie detail view."""
    id: int
    tmdb_id: str
    imdb_id: str | None
    movielens_id: int | None

    title: str
    original_title: str | None
    tagline: str | None
    description: str | None

    runtime: int | None
    released_on: date | None

    poster_url: str | None = None
    backdrop_url: str | None = None
    original_language: str | None

    status: str

    budget: int | None
    revenue: int | None
    adult: bool

    tmdb_vote_average: float | None
    tmdb_vote_count: int | None
    trailer_link: str | None

    genres: list[GenreResponse] = []

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)