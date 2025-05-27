from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import bcrypt
from urllib.parse import urljoin, urlencode
from model.user_model import (
    UserBase, Email, VerifyUser, UserCreate, UserResponse, 
    OtpResponse, EmailVerificationTemplateModel
)
from model.auth import Token, RefreshToken
from config.config import load_config, Config
from utils.logger import Logger
from utils.email_service import EmailService
from utils.otp_generator import generate_otp
from sqlalchemy.ext.asyncio import AsyncSession
from repository.user_repository import (
    UserRepository, RepositoryError, DuplicateUserError,
    UserNotFoundError, InvalidCredentialsError
)
from jose import jwt
from datetime import datetime, timedelta

class UserServiceError(Exception):
    """Base exception for user service errors"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class UserService(ABC):
    @abstractmethod
    async def validate_user_verified(self, user_id: str, db: AsyncSession) -> Tuple[bool, Optional[UserBase]]:pass

    @abstractmethod
    async def get_users(self, db: AsyncSession) -> List[UserBase]: pass

    @abstractmethod
    async def create_user(self, user: UserCreate, db: AsyncSession) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_user_by_email(self, email: str, db: AsyncSession) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str, db: AsyncSession) -> Optional[UserResponse]: pass

    @abstractmethod
    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> Optional[UserBase]: pass

    @abstractmethod
    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> Optional[OtpResponse]: pass

    @abstractmethod
    async def generate_user_registration_draft(self, user: UserBase) -> str: pass

    @abstractmethod
    async def verify_credentials(self, email: str, password: str, db: AsyncSession) -> Optional[UserResponse]: pass

    @abstractmethod
    async def verify_refresh_token(self, refresh_token: str, db: AsyncSession) -> Optional[UserResponse]: pass

class UserInteractor(UserService):
    def __init__(
        self,
        user_repo: UserRepository,
        logger: Logger,
        config: Config
    ):
        self.user_repo = user_repo
        self.logger = logger
        self.config = config

    async def validate_user_verified(self, user_id: str, db: AsyncSession) -> Tuple[bool, Optional[UserBase]]:
        try:
            return await self.user_repo.validate_user_verified(user_id, db)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def get_users(self, db: AsyncSession) -> List[UserBase]:
        try:
            return await self.user_repo.get_users(db)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def create_user(self, user: UserCreate, db: AsyncSession) -> Optional[UserResponse]:
        try:
            return await self.user_repo.create_user(user, db)
        except DuplicateUserError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def get_user_by_email(self, email: str, db: AsyncSession) -> Optional[UserResponse]:
        try:
            return await self.user_repo.get_user_by_email(email, db)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def get_user_by_id(self, user_id: str, db: AsyncSession) -> Optional[UserResponse]:
        try:
            return await self.user_repo.get_user_by_id(user_id, db)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> Optional[UserBase]:
        try:
            return await self.user_repo.verify_user_by_email(user_info, db)
        except (UserNotFoundError, InvalidCredentialsError) as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> Optional[OtpResponse]:
        try:
            return await self.user_repo.get_otp_by_email(email, db)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

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

    async def verify_credentials(self, email: str, password: str, db: AsyncSession) -> Optional[UserResponse]:
        try:
            # Get user with password from repository
            user_with_password = await self.user_repo.get_user_by_email_with_password(email, db)
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user_with_password['password'].encode('utf-8')):
                raise UserServiceError(
                    self.config.ApplicationMessages.en.InvalidCredentials.Message,
                    self.config.ApplicationMessages.en.InvalidCredentials.Key
                )

            # Return user without password
            return await self.get_user_by_email(email, db)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def verify_refresh_token(self, refresh_token: str, db: AsyncSession) -> Optional[UserResponse]:
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                self.config.JWT_REFRESH_SECRET_KEY,
                algorithms=[self.config.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise UserServiceError(
                    self.config.ApplicationMessages.en.InvalidToken.Message,
                    self.config.ApplicationMessages.en.InvalidToken.Key
                )

            # Get user by ID
            return await self.get_user_by_id(user_id, db)
        except jwt.ExpiredSignatureError:
            raise UserServiceError(
                self.config.ApplicationMessages.en.TokenExpired.Message,
                self.config.ApplicationMessages.en.TokenExpired.Key
            )
        except jwt.JWTError:
            raise UserServiceError(
                self.config.ApplicationMessages.en.InvalidToken.Message,
                self.config.ApplicationMessages.en.InvalidToken.Key
            )
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

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
        """Create a new access token for the user"""
        expires_delta = timedelta(minutes=self.config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + expires_delta
        }
        return jwt.encode(
            to_encode,
            self.config.JWT_SECRET_KEY,
            algorithm=self.config.JWT_ALGORITHM
        )

    async def create_refresh_token(self, user: UserResponse) -> str:
        """Create a new refresh token for the user"""
        expires_delta = timedelta(days=self.config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + expires_delta
        }
        return jwt.encode(
            to_encode,
            self.config.JWT_REFRESH_SECRET_KEY,
            algorithm=self.config.JWT_ALGORITHM
        ) 