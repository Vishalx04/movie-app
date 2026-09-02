from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.db.database import get_db
from app.schemas.user import UserSignup, UserLogin, UserResponse, Token
from app.services import auth_service
from app.core.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    return auth_service.signup(db, payload)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    access_token, refresh_token = auth_service.login(db, payload.email, payload.password)
    _set_refresh_cookie(response, refresh_token)
    return Token(access_token=access_token)


@router.post("/refresh", response_model=Token)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise UnauthorizedError("Refresh token missing")
    new_access_token, new_refresh_token = auth_service.rotate_refresh_token(db, raw_token)
    _set_refresh_cookie(response, new_refresh_token)
    return Token(access_token=new_access_token)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        auth_service.revoke_refresh_token(db, raw_token)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user