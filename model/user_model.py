from pydantic import EmailStr, Field
from typing import Optional, List
from datetime import datetime
from model.schemas.base import CustomBaseModel

class UserBase(CustomBaseModel):
    """Base model for user data"""
    first_name: str = Field(..., min_length=2, description="User's first name")
    last_name: str = Field(..., min_length=2, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    phone_no: str = Field(..., description="User's phone number")
    profile_picture: Optional[str] = Field(None, description="User's profile picture")

class UserCreate(UserBase):
    """Model for user creation request"""
    password: str = Field(..., min_length=6, description="User's password")
    verification_token: Optional[str] = Field(None, description="User's verification token")

class UserResponse(CustomBaseModel):
    """Model for user response data"""
    id: str = Field(..., description="User's unique identifier")
    is_active: bool = Field(..., description="User's active status")


    class Config:
        from_attributes = True

class CreateUserResponse(CustomBaseModel):
    """Model for user creation response data"""
    id: str = Field(..., description="User's unique identifier")
    is_verified: bool = Field(..., description="User's verification status")

class TermsSubContent(CustomBaseModel):
    """Model for each sub-section of the Terms of Service"""
    title: str = Field(..., description="Title of the sub content section")
    content: str = Field(..., description="Content of the sub content section")


class TermsOfService(CustomBaseModel):
    """Model for the complete Terms of Service with sub-content"""
    title: str = Field(..., description="Main title of the Terms of Service")
    subtitle: Optional[str] = Field(None, description="Subtitle of the Terms of Service")
    content: str = Field(..., description="Main content of the Terms of Service")
    sub_content: List[TermsSubContent] = Field(default_factory=list, description="List of sub-sections")

# class VerifyUser(CustomBaseModel):
#     email: EmailStr = Field(..., description="User's email address")
#     otp: str = Field(..., min_length=6, max_length=6, description="One-time password")

# class OtpResponse(CustomBaseModel):
#     email: EmailStr = Field(..., description="User's email address")
#     otp: str = Field(..., description="Generated OTP")
#     created_at: datetime = Field(..., description="OTP creation timestamp")
#     is_verified: bool = Field(..., description="OTP verification status")

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

class CurrentUser(CustomBaseModel):
    id: str = Field(..., description="User's ID")
    email: str = Field(..., description="User's email")

