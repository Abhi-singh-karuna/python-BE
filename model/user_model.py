from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime
from jose import jwt
from model.schemas.base import CustomBaseModel
from model.response_model import ApiResponse, ResponseMeta, ResponseError

class UserBase(CustomBaseModel):
    """Base model for user data"""
    name: str = Field(..., min_length=2, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    phone_no: str = Field(..., description="User's phone number")

class UserCreate(UserBase):
    """Model for user creation request"""
    password: str = Field(..., min_length=6, description="User's password")
    otp: Optional[str] = Field(None, description="One-time password for verification")

class UserResponse(UserBase):
    """Model for user response data"""
    id: str = Field(..., description="User's unique identifier")
    password: str = Field(..., description="User's hashed password")
    is_verified: bool = Field(..., description="User's verification status")
    is_active: bool = Field(True, description="User's active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class VerifyUser(CustomBaseModel):
    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="One-time password")

class OtpResponse(CustomBaseModel):
    email: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., description="Generated OTP")
    created_at: datetime = Field(..., description="OTP creation timestamp")
    is_verified: bool = Field(..., description="OTP verification status")

class LoginRequest(CustomBaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password")

class Email(CustomBaseModel):
    email: EmailStr = Field(..., description="User's email address")

class Id(CustomBaseModel):
    id: str = Field(..., description="User's ID")

class JwtCustomClaims(CustomBaseModel):
    id: str = Field(..., description="User's ID")
    email: str = Field(..., description="User's email")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    iat: Optional[int] = Field(None, description="Token issued at timestamp")

class JwtCustomRefreshClaims(CustomBaseModel):
    id: str = Field(..., description="User's ID")
    email: str = Field(..., description="User's email")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    iat: Optional[int] = Field(None, description="Token issued at timestamp")

class ErrorMessage(CustomBaseModel):
    message: str = Field(..., description="Error message")

class HeaderId(CustomBaseModel):
    user_id: str = Field(..., description="User's ID")
    user_email: str = Field(..., description="User's email")
    user_phone_no: str = Field(..., description="User's phone number")
    user_name: Optional[str] = Field(None, description="User's name")

class UserInfo(CustomBaseModel):
    id: str = Field(..., description="User's ID")
    email: str = Field(..., description="User's email")
    name: str = Field(..., description="User's name")
    is_verified: bool = Field(..., description="User's verification status")

class TokenInfo(CustomBaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class SessionInfo(CustomBaseModel):
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")

class LoginResponse(CustomBaseModel):
    user: UserInfo = Field(..., description="User information")
    tokens: TokenInfo = Field(..., description="Authentication tokens")
    last_login: datetime = Field(..., description="Last login timestamp")
    session_info: SessionInfo = Field(..., description="Session information")

class EmailVerificationTemplateModel(CustomBaseModel):
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")

