from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from jose import jwt

class UserBase(BaseModel):
    """Base model for user data"""
    name: str
    email: EmailStr
    phone_no: int

class UserCreate(UserBase):
    """Model for user creation request"""
    password: str
    otp: Optional[str] = None

class UserResponse(UserBase):
    """Model for user response data"""
    id: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VerifyUser(BaseModel):
    email: EmailStr
    otp: str

class OtpResponse(BaseModel):
    email: EmailStr
    otp: str
    created_at: datetime
    is_verified: bool

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class Email(BaseModel):
    email: EmailStr = Field(..., description="User's email address")

class Id(BaseModel):
    id: str = Field(..., description="User's ID")

class JwtCustomClaims(BaseModel):
    id: str
    email: str
    exp: Optional[int] = None
    iat: Optional[int] = None

class JwtCustomRefreshClaims(BaseModel):
    id: str
    email: str
    exp: Optional[int] = None
    iat: Optional[int] = None

class ErrorMessage(BaseModel):
    message: str

class HeaderId(BaseModel):
    user_id: str
    user_email: str
    user_phone_no: str
    user_name: Optional[str] = None

class StandardResponse(BaseModel):
    """Standard response model for API responses"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None

class ErrorInfo(BaseModel):
    """Model for error information"""
    code: str
    message: str
    details: Optional[str] = None

class MetaInfo(BaseModel):
    """Model for metadata information"""
    timestamp: datetime
    version: str = "1.0"
    trace_id: Optional[str] = None

class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    is_verified: bool

class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    expires_at: datetime
    device_info: Optional[str] = None
    ip_address: Optional[str] = None

class LoginResponse(BaseModel):
    user: UserInfo
    tokens: TokenInfo
    last_login: datetime
    session_info: SessionInfo

class EmailVerificationTemplateModel(BaseModel):
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")

def new_success_response(message: str, data: Optional[dict] = None) -> StandardResponse:
    """Helper function to create a success response"""
    return StandardResponse(
        success=True,
        message=message,
        data=data,
        meta=MetaInfo(
            timestamp=datetime.now(),
            version="1.0"
        )
    )

def new_error_response(code: str, message: str, details: Optional[str] = None) -> StandardResponse:
    """Helper function to create an error response"""
    return StandardResponse(
        success=False,
        message=message,
        error=ErrorInfo(
            code=code,
            message=message,
            details=details
        ),
        meta=MetaInfo(
            timestamp=datetime.now(),
            version="1.0"
        )
    ) 