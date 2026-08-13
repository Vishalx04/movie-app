from sqlalchemy.orm import Session
from app.schemas.user import UserSignup
from app.db.models import User, UserCredentials
from app.core.security import verify_password, hash_password, create_access_token

def get_user_by_email(db : Session, email:str)->User |None:
    return db.query(User).filter(User.email==email).first()

def signup(db:Session, payload:UserSignup) ->User:
    user = User(email = payload.email, username= payload.username, name = payload.name)
    db.add(user)
    db.flush()

    credentials = UserCredentials(user_id = user.id, password_hash = hash_password(payload.password) )

    db.add(credentials)

    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db:Session, email:str, password: str)->User|None:
    user = get_user_by_email(db, email)
    if not user or not user.credentials:
        return None
    if not verify_password(password, user.credentials.password_hash):
        return None
    return user

def login(db: Session, email : str, password : str)-> str|None:
    user = authenticate_user(db, email, password)
    if not user:
        return None
    return create_access_token({"sub": str(user.id)})

