from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar: Optional[str] = Field(None, max_length=50)


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
    avatar: str = Field(..., max_length=50, description="Nuevo nombre de avatar (debe ser único)")


class UserPasswordUpdate(BaseModel):
    password: str = Field(..., min_length=6, max_length=128, description="Nueva contraseña")


class UserPasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico para enviar el enlace de recuperación")


class CurrentUser(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Token de renovación válido")
