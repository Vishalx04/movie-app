import pytest
from app.services import rating_service
from app.core.exceptions import NotFoundError

def test_upsert_rating_creates_new_rating(db,test_user, test_movie):
    rating = rating_service.upsert_rating(db, test_user.id, test_movie.id, 4.5)

    assert rating.id is not None
    assert rating.user_id == test_user.id
    assert rating.movie_id == test_movie.id
    assert rating.rating == 4.5

def test_upsert_rating_updates_existing_rating(db, test_user, test_movie):
    first = rating_service.upsert_rating(db, test_user.id, test_movie.id, 3.0)
    second = rating_service.upsert_rating(db, test_user.id, test_movie.id, 5.0)

    assert first.id == second.id
    assert second.rating ==5.0

    all_ratings = rating_service.get_user_ratings(db, test_user.id)
    assert len(all_ratings) == 1

def test_upsert_rating_raises_for_nonexistent_movie(db,test_user):
    with pytest.raises(NotFoundError):
        rating_service.upsert_rating(db, test_user.id,movie_id=9999999, rating_value=4.0)

def test_get_user_rating_for_movie_returns_rating(db, test_user, test_movie):
    rating_service.upsert_rating(db, test_user.id, test_movie.id,4.0)
    result = rating_service.get_user_rating_for_movie(db, test_user.id, test_movie.id)
    assert result.movie_id == test_movie.id
    assert result.rating == 4.0

def test_get_user_rating_for_movie_raises_when_not_rated(db, test_user, test_movie):
    with pytest.raises(NotFoundError):
        rating_service.get_user_rating_for_movie(db, test_user.id, test_movie.id)

def test_get_user_ratings_orders_by_most_recently_updated(db, test_user, test_movie):
    from app.db.models import Movie, MovieStatus

    second_movie = Movie(tmdb_id="888888", title="Second Movie", status=MovieStatus.released, adult=False)
    db.add(second_movie)
    db.commit()
    db.refresh(second_movie)

    rating_service.upsert_rating(db, test_user.id, test_movie.id,3.0)
    rating_service.upsert_rating(db, test_user.id, second_movie.id,4.0)

    result = rating_service.get_user_ratings(db, test_user.id)

    assert len(result) == 2
    assert result[0].movie_id == second_movie.id

def test_delete_rating_removes_it(db, test_user, test_movie):
    rating_service.upsert_rating(db, test_user.id, test_movie.id,4.0)

    rating_service.delete_rating(db, test_user.id, test_movie.id)

    with pytest.raises(NotFoundError):
        rating_service.get_user_rating_for_movie(db, test_user.id, test_movie.id)

def test_delete_rating_raises_when_nothing_to_delete(db, test_user, test_movie):
    with pytest.raises(NotFoundError):
        rating_service.delete_rating(db, test_user.id, test_movie.id)
