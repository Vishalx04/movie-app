from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
import secrets
import hashlib
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password :str)->str:
    print("PASSWORD:", repr(password))
    print("BYTES:", len(password.encode("utf-8")))
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password:str)->str:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data:dict)->str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp" : expire, "jti" : secrets.token_urlsafe(16)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token:str)->dict|None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None

def generate_refresh_token()->str:
    return secrets.token_urlsafe(64)

def hash_refresh_token(token:str)->str:
    return hashlib.sha256(token.encode()).hexdigest()