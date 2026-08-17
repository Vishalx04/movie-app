from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

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


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def signup(db: Session, payload: UserSignup) -> User:
    user = User(email=payload.email, username=payload.username, name=payload.name)
    db.add(user)
    db.flush()
    credentials = UserCredentials(
        user_id=user.id, password_hash=hash_password(payload.password)
    )
    db.add(credentials)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not user.credentials:
        return None
    if not verify_password(password, user.credentials.password_hash):
        return None
    return user


def create_refresh_token_for_user(db: Session, user_id: int) -> str:
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


def login(db: Session, email: str, password: str) -> tuple[str, str] | None:
    user = authenticate_user(db, email, password)
    if not user:
        return None
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token_for_user(db, user.id)
    return access_token, refresh_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, str] | None:
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
        return None
    existing.revoked_at = datetime.now(timezone.utc)
    db.commit()
    new_access_token = create_access_token({"sub": str(existing.user_id)})
    new_refresh_token = create_refresh_token_for_user(db, existing.user_id)
    return new_access_token, new_refresh_token


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hash_refresh_token(raw_token)
    existing = (
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    )
    if existing:
        existing.revoked_at = datetime.now(timezone.utc)
        db.commit()
