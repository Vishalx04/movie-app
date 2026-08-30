from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import ConflictError, UnauthorizedError
from app.db.models import User, UserCredentials, RefreshToken
from app.schemas.user import UserSignup
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
import logging

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def signup(db: Session, payload: UserSignup) -> User:
    logger.info("New user signup attempt: %s", payload.email)
    try:
        user = User(email=payload.email, username=payload.username, name=payload.name)
        db.add(user)
        db.flush()
        credentials = UserCredentials(
            user_id=user.id, password_hash=hash_password(payload.password)
        )
        db.add(credentials)
        db.commit()
        db.refresh(user)
        logger.info("User signed up successfully: %s", payload.email)
        return user
    except IntegrityError as e:
        db.rollback()
        logger.warning("Signup conflict for %s: %s", payload.email, e)
        if "email" in str(e.orig):
            raise ConflictError("An account with this email already exists")
        if "username" in str(e.orig):
            raise ConflictError("This username is already taken")
        raise ConflictError("Account could not be created")


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.credentials:
        logger.warning("Login failed - user not found: %s", email)
        raise UnauthorizedError("Invalid email or password")
    if not verify_password(password, user.credentials.password_hash):
        logger.warning("Login failed - wrong password: %s", email)
        raise UnauthorizedError("Invalid email or password")
    logger.info("User authenticated: %s", email)
    return user


def create_refresh_token_for_user(db: Session, user_id: int) -> str:
    try:
        raw_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
        )
        db.add(refresh_token)
        db.commit()
        return raw_token
    except Exception:
        db.rollback()
        logger.error(
            "Failed to create refresh token for user_id: %s", user_id, exc_info=True
        )
        raise


def login(db: Session, email: str, password: str) -> tuple[str, str]:
    user = authenticate_user(db, email, password)
    logger.info("User logged in: %s", email)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token_for_user(db, user.id)
    return access_token, refresh_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_token)
    existing = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None)
        )
        .first()
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not existing or existing.expires_at < now:
        logger.warning("Refresh token invalid or expired")
        raise UnauthorizedError("Invalid or expired refresh token")

    try:
        existing.revoked_at = datetime.now(timezone.utc)
        raw_new_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_token = RefreshToken(
            user_id=existing.user_id,
            token_hash=hash_refresh_token(raw_new_token),
            expires_at=expires_at,
        )
        db.add(new_token)
        db.commit()
        logger.info("Refresh token rotated for user_id: %s", existing.user_id)
        new_access_token = create_access_token({"sub": str(existing.user_id)})
        return new_access_token, raw_new_token
    except Exception:
        db.rollback()
        logger.error(
            "Failed to rotate refresh token for user_id: %s",
            existing.user_id,
            exc_info=True,
        )
        raise


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    try:
        token_hash = hash_refresh_token(raw_token)
        existing = (
            db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        )
        if existing:
            existing.revoked_at = datetime.now(timezone.utc)
            db.commit()
            logger.info("Refresh token revoked for user_id: %s", existing.user_id)
        else:
            logger.warning("Attempted to revoke non-existent refresh token")
    except Exception:
        db.rollback()
        logger.error("Failed to revoke refresh token", exc_info=True)
        raise
