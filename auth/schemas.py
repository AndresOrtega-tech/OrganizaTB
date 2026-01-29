from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    updated_at: str


class UserAvatarUpdate(BaseModel):
    avatar_url: str = Field(..., description="Nueva URL del avatar (debe ser única)")


class CurrentUser(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
