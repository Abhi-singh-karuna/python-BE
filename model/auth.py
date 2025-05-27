from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime
from model.schemas.base import CustomBaseModel

class TokenData(CustomBaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")

class Token(CustomBaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Token expiration time in seconds")

class RefreshToken(CustomBaseModel):
    refresh_token: str = Field(..., description="JWT refresh token") 