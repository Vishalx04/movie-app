from app.db.models import User
from app.services.rating_service import upsert_rating

def test_rate_movie_requires_authentication(client, test_movie):
    response = client.post("/api/v1/ratings/", json= {
        "movie_id" : test_movie.id,
        "rating" : 4.0
    })

    assert response.status_code == 401

def test_rate_movie_succeeds_when_authenticated(client, test_movie, auth_headers):
    response = client.post("/api/v1/ratings", json={
        "movie_id" : test_movie.id,
        "rating" : 4.0
    },
    headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["movie_id"] == test_movie.id
    assert body["rating"] == 4.0

def test_rate_movie_upserts_on_second_call(client, test_movie, auth_headers):
    client.post("/api/v1/ratings", json={
        "movie_id" : test_movie.id,
        "rating" : 2.0
    }, 
    headers=auth_headers
    )

    response = client.post("/api/v1/ratings", json={
        "movie_id" : test_movie.id,
        "rating": 4.0
    }, 
    headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["rating"] == 4.0

    all_ratings = client.get("/api/v1/ratings/me", headers= auth_headers).json()

    assert len(all_ratings) == 1

def test_rate_nonexistent_movie_returns_404(client, auth_headers):
    response = client.post("/api/v1/ratings/", json={
        "movie_id" : 234567,
        "rating" : 4.8
    }, headers= auth_headers)

    assert response.status_code == 404

def test_rate_movie_rejects_out_of_range_value(client, test_movie, auth_headers):
    response = client.post("/api/v1/ratings", json={
        "movie_id" : test_movie.id,
        "rating" :7.0
    }, headers=auth_headers)

    assert response.status_code == 422

def test_get_my_ratings_only_returns_own_ratings(client, db, test_movie, auth_headers):
    other_user = User(email= "other@example.com", username = "othername")
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    upsert_rating(db,other_user.id, test_movie.id, 1.4)

    client.post("/api/v1/ratings/", json={
        "movie_id" : test_movie.id,
        "rating" : 3.4
    }, headers= auth_headers)

    response = client.get("/api/v1/ratings/me/", headers= auth_headers)
    ratings = response.json()

    assert len(ratings) == 1
    assert ratings[0]["rating"] == 3.4


def test_get_rating_for_unrated_movie_returns_404(client, test_movie, auth_headers):
    response = client.get(f"/api/v1/ratings/movie/{test_movie.id}", headers= auth_headers)

    assert response.status_code == 404

def test_delete_rating_removes_it(client, test_movie, auth_headers):
    client.post("/api/v1/ratings", json = {
        "movie_id" : test_movie.id,
        "rating" : 5.0
    }, headers= auth_headers)

    delete_response = client.delete(f"/api/v1/ratings/movie/{test_movie.id}", headers= auth_headers)
    get_response = client.get(f"/api/ratings/movie/{test_movie.id}", headers= auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
