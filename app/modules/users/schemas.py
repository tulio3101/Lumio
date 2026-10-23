import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(
        description="Correo electrónico de la cuenta.", examples=["ana@example.com"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Contraseña en texto plano; se almacena solo como hash.",
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(description="ID token emitido por Google al cliente.")


class RefreshRequest(BaseModel):
    refresh_token: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="Segundos de vigencia del access token.", examples=[900])
