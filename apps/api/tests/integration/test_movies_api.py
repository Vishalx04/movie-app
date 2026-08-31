def test_list_movies_returns_only_enriched(client, enriched_movie, test_movie):
    response = client.get("/api/v1/movies/")

    assert response.status_code == 200
    ids = [m["id"] for m in response.json()]
    assert enriched_movie.id in ids

def test_get_movie_by_id_returns_200_for_enriched(client, enriched_movie):
    response = client.get(f"/api/v1/movies/{enriched_movie.id}")

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == enriched_movie.id
    assert body["poster_url"] is not None

def test_get_movie_by_id_returns_404_for_nonexistent(client):
    response = client.get("/api/v1/movies/999999")

    assert response.status_code == 404
    assert "detail" in response.json()

def test_get_movie_by_id_returns_404_for_unenriched(client, test_movie):
    response = client.get(f"/api/v1/movies/{test_movie.id}")

    assert response.status_code == 404

def test_create_movie_requires_authentication(client):
    response = client.post("/api/v1/movies/", json={
        "tmdb_id" : "1",
        "title" : "new movie"
    })

    assert response.status_code == 401

def test_create_movie_requires_admin_role(client, auth_headers):
    response = client.post("/api/v1/movies/" , json={
        "tmdb_id": "1",
        "title" : "new"
    }, headers= auth_headers)

    assert response.status_code == 403

def test_create_movie_succeeds_for_admin(client, admin_auth_headers):
    response = client.post("/api/v1/movies", json={
        "tmdb_id" : "1234",
        "title" : "admin movie",
        "genre_ids": []
    },
    headers= admin_auth_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "admin movie"

def test_search_query_param_works_end_to_end(client, enriched_movie):
    enriched_movie.title = "The Matrix"

    response = client.get("/api/v1/movies/?q=atrix")
    ids = [m["id"] for m in response.json()]
    assert enriched_movie.id in ids