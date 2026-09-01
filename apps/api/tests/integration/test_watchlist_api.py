from app.db.models import Movie, MovieStatus

def test_add_to_watchlist_requires_authentication(client, test_movie):
    response = client.post("/api/v1/watchlist/", json={
        "movie_id" : test_movie.id, 
    })

    assert response.status_code == 401


def test_add_to_watchlist_succeeds(client, test_movie, auth_headers):
    response = client.post("/api/v1/watchlist/", json = { "movie_id" : test_movie.id}, headers= auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["movie_id"] == test_movie.id
    assert body["status"] == "want_to_watch"

def test_add_to_watchlist_twice_is_idempotent(client, test_movie, auth_headers):
    first = client.post("/api/v1/watchlist/", json = { "movie_id" : test_movie.id }, headers=auth_headers)
    second = client.post("/api/v1/watchlist/", json = { "movie_id" : test_movie.id }, headers=auth_headers)

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] == second.json()["id"]

def test_add_nonexistent_movie_returns_404(client, auth_headers):
    response = client.post("/api/v1/watchlist/", json= { "movie_id" : 23456}, headers= auth_headers)

    assert response.status_code == 404

def test_update_status_to_watched_sets_watched_at(client, test_movie, auth_headers):
    client.post("/api/v1/watchlist/", json={"movie_id" : test_movie.id}, headers = auth_headers)

    response = client.patch(f"/api/v1/watchlist/movie/{test_movie.id}", json={"status" : "watched"}, headers = auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "watched"
    assert body["watched_at"] is not None

def test_update_status_for_movie_not_on_watchlist_returns_404(client, test_movie, auth_headers):
    response = client.patch(f"/api/v1/watchlist/movie/{test_movie.id}", json={"status" : "watched"}, headers = auth_headers)

    assert response.status_code == 404

def test_get_watchlist_filters_by_status(client, db, test_movie, auth_headers):

    second_movie = Movie(tmdb_id = "234567", title = "second", status = MovieStatus.released, adult = False)
    db.add(second_movie)
    db.commit()
    db.refresh(second_movie)

    client.post("/api/v1/watchlist", json = {"movie_id" : second_movie.id}, headers= auth_headers)
    client.post("/api/v1/watchlist", json = {"movie_id" : test_movie.id}, headers= auth_headers)

    client.patch(f"/api/v1/watchlist/movie/{test_movie.id}", json = {"status": "watched"}, headers = auth_headers)

    watched = client.get("/api/v1/watchlist/me?status=watched", headers = auth_headers).json()
    pending = client.get("/api/v1/watchlist/me?status=want_to_watch", headers = auth_headers).json()

    assert len(watched) == 1
    assert len(pending) == 1

    assert watched[0]["movie_id"] == test_movie.id
    assert pending[0]["movie_id"] == second_movie.id

def test_remove_from_watchlist(client, test_movie, auth_headers):
    client.post("/api/v1/watchlist/", json={"movie_id": test_movie.id}, headers=auth_headers)

    delete_response = client.delete(f"/api/v1/watchlist/movie/{test_movie.id}", headers=auth_headers)
    get_response = client.get(f"/api/v1/watchlist/movie/{test_movie.id}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404