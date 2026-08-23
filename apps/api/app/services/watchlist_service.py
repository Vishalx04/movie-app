from datetime import datetime
from app.db.models import Movie, WatchlistStatus, WatchlistItem
from sqlalchemy.orm import Session


def add_to_watchlist(db:Session, user_id:int, movie_id: int)->WatchlistItem:
    movie_exists = db.query(Movie.id).filter(Movie.id == movie_id).first()
    if not movie_exists:
        raise ValueError("Movie not found")

    existing = db.query(WatchlistItem).filter(WatchlistItem.movie_id == movie_id, WatchlistItem.user_id== user_id).first()

    if existing:
        return existing

    item = WatchlistItem(user_id = user_id, movie_id = movie_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def update_status(db:Session, user_id:int, movie_id:int, new_status:WatchlistStatus)->WatchlistItem:
    item = db.query(WatchlistItem).filter(WatchlistItem.movie_id==movie_id, WatchlistItem.user_id==user_id).first()

    if not item:
        raise ValueError("Movie is not in your watchlist")

    item.status = new_status
    if new_status == WatchlistStatus.watched and item.watched_at is None:
        item.watched_at = datetime.now()

    db.commit()
    db.refresh(item)
    return item


def get_user_watchlist(db:Session, user_id:int, status:WatchlistStatus | None = None)->list[WatchlistItem]:
    query = db.query(WatchlistItem).filter(WatchlistItem.user_id==user_id)

    if status is not None:
        query = query.filter(WatchlistItem.status==status)

    return query.order_by(WatchlistItem.added_at.desc()).all()


def get_watchlist_item_for_movie(db:Session, user_id:int, movie_id:int)-> WatchlistItem | None:
    return db.query(WatchlistItem).filter(WatchlistItem.user_id==user_id, WatchlistItem.movie_id==movie_id).first()

def remove_from_watchlist(db: Session, user_id: int, movie_id: int) -> bool:
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True