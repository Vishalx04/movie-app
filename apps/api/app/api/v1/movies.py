from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import movie_service
from app.schemas.movie import MovieListItem, MovieResponse, MovieCreate
from app.db.models import User
from app.core.dependencies import require_admin
router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=list[MovieListItem])
def list_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100, ge=1),
    q: str | None = Query(None, description="search by movie title"),
    genre_id: int | None = Query(None, description="filter by genre id"),
    db: Session = Depends(get_db),
):
    return movie_service.get_all_movies(db, skip, limit, q, genre_id)


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    return movie_service.get_movie_by_id(db, movie_id)


@router.post("/", response_model=MovieResponse)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return movie_service.create_movie(db, payload)
