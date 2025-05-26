from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TokenData(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class RefreshToken(BaseModel):
    refresh_token: str 