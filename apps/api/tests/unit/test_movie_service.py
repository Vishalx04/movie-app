import pytest
from app.services import movie_service
from app.core.exceptions import NotFoundError
from app.schemas.movie import MovieCreate
from app.db.models import Genre

def test_get_all_movies_excludes_unenriched(db, test_movie):
    results = movie_service.get_all_movies(db)
    assert test_movie.id not in [m.id for m in results]

def test_get_all_movies_includes_enriched(db, enriched_movie):
    results = movie_service.get_all_movies(db)
    assert enriched_movie.id in [m.id for m in results]

def test_get_all_movies_attaches_image_urls(db, enriched_movie):
    results = movie_service.get_all_movies(db)
    found = next(m for m in results if m.id == enriched_movie.id)

    assert found.poster_url is not None
    assert found.poster_url.endswith("/fake-poster.jpg")

def test_search_matches_title_containing_query_not_just_prefix(db, enriched_movie):
    enriched_movie.title = "The Matrix"
    db.commit()

    results = movie_service.get_all_movies(db, q="atrix")
    assert any(m.id == enriched_movie.id for m in results)

def test_search_is_case_insensitive(db, enriched_movie):
    enriched_movie.title = "The matrix"
    db.commit()

    results = movie_service.get_all_movies(db, q="MATRIX")
    assert any(m.id == enriched_movie.id for m in results)

def test_genre_filter_returns_only_matching_movies(db, enriched_movie):
    action = Genre(name="Action", slug = "action")
    drama = Genre(name="Drama", slug = "drama")

    db.add_all([action, drama])
    db.commit()
    db.refresh(action)
    db.refresh(drama)

    enriched_movie.genres = [action]
    db.commit()

    action_results = movie_service.get_all_movies(db, genre_id=action.id)
    drama_results = movie_service.get_all_movies(db, genre_id=drama.id)

    assert any(m.id == enriched_movie.id for m in action_results)
    assert all(m.id != enriched_movie.id for m in drama_results)

def test_get_movie_by_id_returns_enriched_movie(db, enriched_movie):
    result = movie_service.get_movie_by_id(db, enriched_movie.id)
    assert result.id == enriched_movie.id
    assert result.poster_url is not None

def test_get_movie_by_id_raises_for_unenriched_movie(db, test_movie):
    with pytest.raises(NotFoundError):
        movie_service.get_movie_by_id(db, test_movie.id)

def test_get_movie_by_id_raises_for_nonexistent_id(db):
    with pytest.raises(NotFoundError):
        movie_service.get_movie_by_id(db, 9999999)

def test_create_movie_with_genres_succeeds(db):
    genre = Genre(name= "Comedy", slug = "comedy")
    db.add(genre)
    db.commit()
    db.refresh(genre)

    payload = MovieCreate(
        tmdb_id="1234",
        title= "new movie",
        genre_ids=[genre.id],
    )

    movie = movie_service.create_movie(db, payload=payload)

    assert movie.id is not None
    assert movie.title == "new movie"
    assert len(movie.genres) == 1
    assert movie.genres[0].id == genre.id

def test_create_movie_without_genres_succeeds(db):
    payload = MovieCreate(tmdb_id="1234", title="new movie", genre_ids=[])

    movie = movie_service.create_movie(db, payload)

    assert movie.id is not None
    assert movie.genres == []

