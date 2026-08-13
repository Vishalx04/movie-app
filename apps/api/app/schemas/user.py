from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
import re

class UserSignup(BaseModel):
    email : EmailStr
    username: str
    name : str | None = None
    password : str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v:str)->str:
        if len(v) < 8:
            raise ValueError("Minimum 8 characters")

        if not any(c.isupper() for c in v):
            raise ValueError("Must contain one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Must contain one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Must contain one digit")

        if not any(c in "!@#$%^&*" for c in v):
            raise ValueError("Must contain one special character")

        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()

        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")

        if len(v) > 30:
            raise ValueError("Username cannot exceed 30 characters")

        if " " in v:
            raise ValueError("Username cannot contain spaces")

        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )

        return v

class UserLogin(BaseModel):
    email:EmailStr
    password : str


class UserResponse(BaseModel):
    id:int
    email: str
    username : str
    name : str | None
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type : str = "bearer"