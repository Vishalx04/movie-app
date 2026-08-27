from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.db.models import WatchlistStatus, User
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistStatusUpdate,
    WatchlistResponse,
)
from app.services import watchlist_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("/", response_model=WatchlistResponse, status_code=201)
def add_movie(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return watchlist_service.add_to_watchlist(db, current_user.id, payload.movie_id)


@router.get("/me", response_model=list[WatchlistResponse])
def get_my_watchlist(
    status: WatchlistStatus | None = Query(None, description="filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return watchlist_service.get_user_watchlist(db, current_user.id, status=status)


@router.get("/movie/{movie_id}", response_model=WatchlistResponse)
def get_watchlist_status_for_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return watchlist_service.get_watchlist_item_for_movie(db, current_user.id, movie_id)


@router.patch("/movie/{movie_id}", response_model=WatchlistResponse)
def update_movie_status(
    movie_id: int,
    payload: WatchlistStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return watchlist_service.update_status(db, current_user.id, movie_id=movie_id, new_status=payload.status)


@router.delete("/movie/{movie_id}", status_code=204)
def remove_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist_service.remove_from_watchlist(db, current_user.id, movie_id)