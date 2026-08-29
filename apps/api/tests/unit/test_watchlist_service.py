import pytest
from app.services import watchlist_service
from app.core.exceptions import NotFoundError
from app.db.models import Movie, MovieStatus, WatchlistStatus


def test_add_to_watchlist_creates_entry(db, test_user, test_movie):
    item = watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    assert item.id is not None
    assert item.user_id == test_user.id
    assert item.movie_id == test_movie.id
    assert item.status == WatchlistStatus.want_to_watch
    assert item.watched_at is None


def test_add_to_watchlist_is_idempotent(db, test_user, test_movie):
    first = watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)
    second = watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    assert first.id == second.id

    all_items = watchlist_service.get_user_watchlist(db, test_user.id)
    assert len(all_items) == 1


def test_add_to_watchlist_raises_for_nonexistent_movie(db, test_user):
    with pytest.raises(NotFoundError):
        watchlist_service.add_to_watchlist(db, test_user.id, movie_id=9999)


def test_get_watchlist_item_for_movie_raises_when_not_present(
    db, test_user, test_movie
):
    with pytest.raises(NotFoundError):
        watchlist_service.get_watchlist_item_for_movie(db, test_user.id, test_movie.id)


def test_get_watchlist_item_for_movie_returns_item_when_present(
    db, test_user, test_movie
):
    watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    item = watchlist_service.get_watchlist_item_for_movie(
        db, test_user.id, test_movie.id
    )
    assert item.movie_id == test_movie.id


def test_update_status_raises_when_not_on_watchlist(db, test_user, test_movie):
    with pytest.raises(NotFoundError):
        watchlist_service.update_status(
            db, test_user.id, test_movie.id, WatchlistStatus.watched
        )


def test_update_status_to_watched_sets_watched_at(db, test_user, test_movie):
    watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    updated = watchlist_service.update_status(
        db, test_user.id, test_movie.id, WatchlistStatus.watched
    )

    assert updated.status == WatchlistStatus.watched
    assert updated.watched_at is not None


def test_watched_at_is_not_overwritten_on_repeat_transitions(db, test_user, test_movie):
    watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    first_updated = watchlist_service.update_status(
        db, test_user.id, test_movie.id, WatchlistStatus.watched
    )
    first_watched_at = first_updated.watched_at
    watchlist_service.update_status(
        db, test_user.id, test_movie.id, WatchlistStatus.want_to_watch
    )
    second_update = watchlist_service.update_status(
        db, test_user.id, test_movie.id, WatchlistStatus.watched
    )

    assert second_update.watched_at == first_watched_at


def test_get_user_watchlist_filters_by_status(db, test_user, test_movie):
    second_movie = Movie(
        tmdb_id="7777777",
        title="another movie",
        status=MovieStatus.released,
        adult=False,
    )
    db.add(second_movie)
    db.commit()
    db.refresh(second_movie)

    watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)
    watchlist_service.add_to_watchlist(db, test_user.id, second_movie.id)

    watchlist_service.update_status(
        db, test_user.id, test_movie.id, WatchlistStatus.watched
    )
    watched_only = watchlist_service.get_user_watchlist(
        db, test_user.id, WatchlistStatus.watched
    )
    want_to_watch_only = watchlist_service.get_user_watchlist(
        db, test_user.id, WatchlistStatus.want_to_watch
    )

    assert len(watched_only) == 1
    assert watched_only[0].movie_id == test_movie.id
    assert len(want_to_watch_only) == 1
    assert want_to_watch_only[0].movie_id == second_movie.id


def test_remove_from_watchlist_deletes_entry(db, test_user, test_movie):
    watchlist_service.add_to_watchlist(db, test_user.id, test_movie.id)

    watchlist_service.remove_from_watchlist(db, test_user.id, test_movie.id)

    with pytest.raises(NotFoundError):
        watchlist_service.get_watchlist_item_for_movie(db, test_user.id, test_movie.id)


def test_remove_from_watchlist_raises_when_nothing_to_remove(db, test_user, test_movie):
    with pytest.raises(NotFoundError):
        watchlist_service.remove_from_watchlist(db, test_user.id, test_movie.id)
