def test_signup_creates_user(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "new@example.com", "username": "newuser", "password": "Password123!"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert "password" not in response.json()  # never leak credentials in response


def test_signup_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "username": "user1", "password": "Password123!"}
    client.post("/api/v1/auth/signup", json=payload)

    payload["username"] = "user2"
    response = client.post("/api/v1/auth/signup", json=payload)

    assert response.status_code == 409


def test_login_sets_refresh_cookie(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "login@example.com", "username": "loginuser", "password": "Password123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies

    cookie = response.cookies["refresh_token"]
    assert cookie  # present and non-empty


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "wrongpw@example.com", "username": "wrongpwuser", "password": "Password123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "WrongOne!"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code in (401, 403)  # TestClient with no Authorization header


def test_me_returns_current_user(client, test_user, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == test_user.id
    assert response.json()["email"] == test_user.email


def test_refresh_without_cookie_returns_401(client):
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


def test_refresh_flow_end_to_end(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "refresh@example.com", "username": "refreshuser", "password": "Password123!"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password123!"},
    )

    refresh_response = client.post("/api/v1/auth/refresh")

    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    original_access_token = login_response.json()["access_token"]
    assert new_access_token != original_access_token


def test_reused_refresh_token_is_rejected(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "reuse@example.com", "username": "reuseuser", "password": "Password123!"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": "reuse@example.com", "password": "Password123!"},
    )
    old_cookie_value = client.cookies.get("refresh_token")

    client.post("/api/v1/auth/refresh")  # first use — rotates, old cookie now dead

    # Manually replay the OLD cookie value, simulating a stolen/replayed token.
    client.cookies.set("refresh_token", old_cookie_value)
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


def test_logout_clears_cookie_and_revokes_token(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "logout@example.com", "username": "logoutuser", "password": "Password123!"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "Password123!"},
    )

    logout_response = client.post("/api/v1/auth/logout")
    refresh_after_logout = client.post("/api/v1/auth/refresh")

    assert logout_response.status_code == 204
    assert refresh_after_logout.status_code == 401