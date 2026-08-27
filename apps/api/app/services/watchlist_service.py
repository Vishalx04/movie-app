from datetime import datetime, timezone
from app.db.models import Movie, WatchlistStatus, WatchlistItem
from sqlalchemy.orm import Session, joinedload
from app.services.movie_service import attach_image_urls
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


def _attach_movie_urls(item: WatchlistItem) -> WatchlistItem:
    if item.movie:
        attach_image_urls(item.movie)
    return item


def add_to_watchlist(db: Session, user_id: int, movie_id: int) -> WatchlistItem:
    movie_exists = db.query(Movie.id).filter(Movie.id == movie_id).first()
    if not movie_exists:
        raise NotFoundError("Movie not found")
    existing = (
        db.query(WatchlistItem)
        .options(joinedload(WatchlistItem.movie))
        .filter(WatchlistItem.movie_id == movie_id, WatchlistItem.user_id == user_id)
        .first()
    )
    if existing:
        logger.info("Movie already in watchlist - user=%s movie=%s", user_id, movie_id)
        return _attach_movie_urls(existing)
    try:
        logger.info("Adding to watchlist - user=%s movie=%s", user_id, movie_id)
        item = WatchlistItem(user_id=user_id, movie_id=movie_id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return _attach_movie_urls(item)
    except Exception:
        db.rollback()
        raise


def update_status(
    db: Session, user_id: int, movie_id: int, new_status: WatchlistStatus
) -> WatchlistItem:
    item = (
        db.query(WatchlistItem)
        .options(joinedload(WatchlistItem.movie))
        .filter(WatchlistItem.movie_id == movie_id, WatchlistItem.user_id == user_id)
        .first()
    )
    if not item:
        raise NotFoundError("Movie is not in your watchlist")
    try:
        logger.info(
            "Updating watchlist status - user=%s movie=%s status=%s",
            user_id,
            movie_id,
            new_status,
        )
        item.status = new_status
        if new_status == WatchlistStatus.watched and item.watched_at is None:
            item.watched_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return _attach_movie_urls(item)
    except Exception:
        db.rollback()
        raise


def get_user_watchlist(
    db: Session, user_id: int, status: WatchlistStatus | None = None
) -> list[WatchlistItem]:
    query = (
        db.query(WatchlistItem)
        .options(joinedload(WatchlistItem.movie))
        .filter(WatchlistItem.user_id == user_id)
    )

    if status is not None:
        query = query.filter(WatchlistItem.status == status)

    return [
        _attach_movie_urls(item)
        for item in query.order_by(WatchlistItem.added_at.desc()).all()
    ]


def get_watchlist_item_for_movie(db: Session, user_id: int, movie_id: int) -> WatchlistItem:
    item = (
        db.query(WatchlistItem)
        .options(joinedload(WatchlistItem.movie))
        .filter(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
        .first()
    )
    if not item:
        raise NotFoundError("Movie is not on your watchlist")
    return _attach_movie_urls(item)


def remove_from_watchlist(db: Session, user_id: int, movie_id: int) -> None:
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
        .first()
    )
    if not item:
        raise NotFoundError("Movie is not on your watchlist")
    try:
        db.delete(item)
        db.commit()
        logger.info("Removed from watchlist - user=%s movie=%s", user_id, movie_id)
    except Exception:
        db.rollback()
        raise