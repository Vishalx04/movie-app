import pytest
from app.services import auth_service
from app.core.exceptions import ConflictError, UnauthorizedError
from app.schemas.user import UserSignup

def make_signup_payload(email = "newuser@gmail.com", password = "new12@A1", username = "newuser"):
    return UserSignup(email=email, username=username, name="newuser", password=password)

def test_signup_creates_user_and_credentials(db):
    user = auth_service.signup(db, make_signup_payload())

    assert user.id is not None
    assert user.email == "newuser@gmail.com"
    assert user.credentials is not None
    assert user.credentials.password_hash!="new12@A1"

def test_signup_raises_conflict_for_duplicate_email(db):
    auth_service.signup(db, make_signup_payload(email="dupe@example.com", username="user1"))

    with pytest.raises(ConflictError):
        auth_service.signup(db, make_signup_payload(email="dupe@example.com", username="user2"))

def test_signup_raises_conflict_for_duplicate_username(db):
    auth_service.signup(db, make_signup_payload(email="first@gmail.com", username="user1"))

    with pytest.raises(ConflictError):
        auth_service.signup(db, make_signup_payload(email="second@mail.com", username="user1"))

def test_authenticate_user_succeeds_with_correct_credentials(db):
    auth_service.signup(db, make_signup_payload())

    user = auth_service.authenticate_user(db, email="newuser@gmail.com", password="new12@A1")

    assert user.email == "newuser@gmail.com"

def test_authenticate_user_raises_for_wrong_password(db):
    auth_service.signup(db, make_signup_payload())

    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_user(db, "newuser@gmail.com", "wrongP12@")

def test_authenticate_user_raises_for_nonexistent_email(db):
    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_user(db, "nobody@mail.com", "Whatevr1@")

def test_login_returns_access_and_refresh_tokens(db):
    auth_service.signup(db, make_signup_payload())

    access_token, refresh_token = auth_service.login(db, email = "newuser@gmail.com", password = "new12@A1")

    assert access_token
    assert refresh_token
    assert access_token!=refresh_token

def test_login_raises_for_invalid_credentials(db):
    with pytest.raises(UnauthorizedError):
        auth_service.login(db, "nobody@mail.com", "Whatever@1")

def test_rotate_refresh_token_returns_new_pair(db):
    auth_service.signup(db, make_signup_payload(email="rotate@example.com", username="rotateuser"))
    _, original_refresh = auth_service.login(db, email="rotate@example.com", password="new12@A1")

    new_access, new_refresh = auth_service.rotate_refresh_token(db, original_refresh)

    assert new_access
    assert new_refresh
    assert new_refresh!=original_refresh

def test_rotate_refresh_token_rejects_reuse_of_rotated_token(db):
    auth_service.signup(db, make_signup_payload(email="reuse@example.com", username="reuseuser"))
    _, original_refresh = auth_service.login(db, email="reuse@example.com", password="new12@A1")

    auth_service.rotate_refresh_token(db, original_refresh)

    with pytest.raises(UnauthorizedError):
        auth_service.rotate_refresh_token(db,original_refresh)

def test_rotate_refresh_token_raises_for_garbage_token(db):
    with pytest.raises(UnauthorizedError):
        auth_service.rotate_refresh_token(db, "not-a-real-token")

def test_revoke_refresh_token_prevents_future_rotation(db):
    auth_service.signup(db, make_signup_payload())
    _, refresh_token = auth_service.login(db, email = "newuser@gmail.com", password = "new12@A1")

    auth_service.revoke_refresh_token(db, refresh_token)

    with pytest.raises(UnauthorizedError):
        auth_service.rotate_refresh_token(db, refresh_token)

def test_revoke_refresh_token_is_safe_on_nonexistent_token(db):
    # Should not raise — logout is idempotent even against a token that
    # was never valid or already gone.

    auth_service.revoke_refresh_token(db, "made-up-token")

