from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import bcrypt
from urllib.parse import urljoin, urlencode
from jinja2 import Environment, FileSystemLoader
from model.user_model import (
    UserBase, Email, Id, VerifyUser, UserCreate, UserResponse, 
    OtpResponse, EmailVerificationTemplateModel
)
from model.auth import Token, TokenData, RefreshToken
from repository import Repository
from config import Config
from utils.logger import Logger
from utils.email_service import EmailService
from utils.otp_generator import generate_otp
from sqlalchemy.ext.asyncio import AsyncSession
from repository.user_repository import Database
from jose import jwt
from datetime import datetime, timedelta

class UserServiceError(Exception):
    """Base exception for user service errors"""
    def __init__(self, message: str, code: str = "USER_SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class UserNotFoundError(UserServiceError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")

class InvalidCredentialsError(UserServiceError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, "INVALID_CREDENTIALS")

class UserAlreadyVerifiedError(UserServiceError):
    def __init__(self, message: str = "User already verified"):
        super().__init__(message, "USER_ALREADY_VERIFIED")

class InvalidOtpError(UserServiceError):
    def __init__(self, message: str = "Invalid OTP"):
        super().__init__(message, "INVALID_OTP")

class UserService(ABC):
    @abstractmethod
    async def validate_user_verified(self, user_id: str, db: AsyncSession) -> Tuple[bool, Optional[UserBase]]:
        pass

    @abstractmethod
    async def get_users(self, db: AsyncSession) -> List[UserBase]:
        pass

    @abstractmethod
    async def create_user(self, user: UserCreate, db: AsyncSession) -> Optional[UserResponse]:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: Email, db: AsyncSession) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: Id, db: AsyncSession) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> Optional[OtpResponse]:
        pass

    @abstractmethod
    async def generate_user_registration_draft(self, user: UserBase) -> str:
        pass

class UserInteractor(UserService):
    def __init__(
        self,
        user_repo: Database,
        logger: Logger,
        config: Config,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.logger = logger
        self.config = config
        self.email_service = email_service
        self.template_env = Environment(
            loader=FileSystemLoader('templates')
        )

    async def validate_user_verified(self, user_id: str, db: AsyncSession) -> Tuple[bool, Optional[UserBase]]:
        return await self.user_repo.validate_user_verified(user_id, db)

    async def get_users(self, db: AsyncSession) -> List[UserBase]:
        return await self.user_repo.get_users(db)

    async def create_user(self, user: UserCreate, db: AsyncSession) -> Optional[UserResponse]:
        print(f"Creating user in service: {user}")
        # Hash password
        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        
        # Create user object
        new_user = UserCreate(
            name=user.name,
            email=user.email,
            password=hashed_password.decode(),
            phone_no=user.phone_no
        )
        
        # Save user to database
        print(f"Creating user in service:-------------------------------- 1ST")
        created_user = await self.user_repo.create_user(new_user, db)
        print(f"Creating user in service:-------------------------------- 2ND")
        if not created_user:
            return None
            
        # Send verification email
        await self.email_service.send_email(
            to_email=user.email,
            subject="Verify your email",
            body=f"Your verification code is: {created_user.otp}"
        )
        
        return UserResponse(
            id=created_user.id,
            name=created_user.name,
            email=created_user.email,
            phone_no=created_user.phone_no,
            is_verified=created_user.is_verified
        )

    async def get_user_by_email(self, email: Email, db: AsyncSession) -> Optional[UserBase]:
        user = await self.user_repo.get_user_by_email(email, db)
        if not user or not user.id:
            raise UserNotFoundError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Key"])
        return user

    async def get_user_by_id(self, user_id: Id, db: AsyncSession) -> Optional[UserBase]:
        user = await self.user_repo.get_user_by_id(user_id, db)
        if not user:
            raise UserNotFoundError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Key"])
        return user

    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> Optional[UserBase]:
        user = await self.user_repo.verify_user_by_email(user_info, db)
        if not user or not user.email:
            raise UserNotFoundError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Key"])
        if user.is_verified:
            raise UserAlreadyVerifiedError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserAlreadyVerified"]["Key"])
        if user.otp != user_info.otp:
            raise InvalidOtpError(self.config.ApplicationMessages[self.config.CurrentLanguage]["OtpUnMatchError"]["Key"])
        return user

    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> Optional[OtpResponse]:
        user = await self.user_repo.get_otp_by_email(email, db)
        if not user or not user.id:
            raise UserNotFoundError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Key"])
        if user.is_verified:
            raise UserAlreadyVerifiedError(self.config.ApplicationMessages[self.config.CurrentLanguage]["UserAlreadyVerified"]["Key"])
        return user

    async def generate_user_registration_draft(self, user: UserBase) -> str:
        template = self.template_env.get_template('user_pdf.html')
        return template.render(
            name=user.name,
            email=user.email
        )

    async def prepare_verification_email_body(self, user_email: str, otp_code: str) -> str:
        template = self.template_env.get_template('verification_email.html')
        
        # Generate verification link
        verify_url = urljoin(self.config.WebURL, "/verify-email")
        params = {
            "email": user_email,
            "otp": otp_code
        }
        verify_url = f"{verify_url}?{urlencode(params)}"

        # Create template data
        data = EmailVerificationTemplateModel(
            user_email=user_email,
            verification_link=verify_url,
            otp_code=otp_code
        )

        return template.render(data=data)

    async def verify_user(self, email: str, otp: str, db: AsyncSession) -> OtpResponse:
        # Get user by email
        user = await self.user_repo.get_user_by_email(email, db)
        if not user:
            return None
            
        # Get OTP for user
        otp_info = await self.user_repo.get_otp_by_email(email, db)
        if not otp_info or otp_info.otp != otp:
            return None
            
        # Verify user
        verified_user = await self.user_repo.verify_user_by_email(
            VerifyUser(email=email, otp=otp),
            db
        )
        if not verified_user:
            return None
            
        return OtpResponse(
            message="User verified successfully",
            is_verified=True
        )

    async def login_for_access_token(self, email: str, password: str, db: AsyncSession) -> Token:
        # Get user by email
        user = await self.user_repo.get_user_by_email(email, db)
        if not user:
            raise UserNotFoundError("User not found")
            
        # Verify password
        if not bcrypt.checkpw(password.encode(), user.password.encode()):
            raise InvalidCredentialsError("Invalid password")
            
        # Create access token
        access_token = await self.create_access_token(user)
        
        # Create refresh token
        refresh_token = await self.create_refresh_token(user)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_token(self, refresh_token: RefreshToken, db: AsyncSession) -> Token:
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token.refresh_token,
                self.config.RefreshTokenSecret,
                algorithms=["HS256"]
            )
            user_id = payload.get("id")
            if not user_id:
                return None
                
            # Get user by ID
            user = await self.user_repo.get_user_by_id(user_id, db)
            if not user:
                return None
                
            # Create new access token
            access_token = await self.create_access_token(user)
            
            # Create new refresh token
            new_refresh_token = await self.create_refresh_token(user)
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )
        except jwt.JWTError:
            return None

    async def create_access_token(self, user: UserResponse) -> str:
        expires_delta = timedelta(minutes=15)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "id": user.id,
            "email": user.email,
            "exp": expire
        }
        
        return jwt.encode(
            to_encode,
            self.config.AccessTokenSecret,
            algorithm="HS256"
        )

    async def create_refresh_token(self, user: UserResponse) -> str:
        expires_delta = timedelta(days=7)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "id": user.id,
            "email": user.email,
            "exp": expire
        }
        
        return jwt.encode(
            to_encode,
            self.config.RefreshTokenSecret,
            algorithm="HS256"
        ) 