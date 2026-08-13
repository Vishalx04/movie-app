from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserLogin
from app.db.database import get_db
from app.schemas.user import UserSignup, UserResponse, Token
from app.services import auth_service
from app.core.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=201 )
def signup( payload : UserSignup,db:Session = Depends(get_db)):
    return auth_service.signup(db, payload)

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    access_token = auth_service.login(db, payload.email, payload.password)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user : User = Depends(get_current_user)):
    return current_user
