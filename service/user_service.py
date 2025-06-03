from abc import ABC, abstractmethod
from typing import Optional
import bcrypt
from model.user_model import ( UserCreate, UserResponse, TermsOfService, TokenData, Token, RefreshToken)
from config.config import Config
from utils.logger import Logger
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
    async def check_health(self) -> dict: pass

    @abstractmethod
    async def create_user(self, user: UserCreate) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]: pass

    @abstractmethod
    async def verify_credentials(self, email: str, password: str) -> Optional[UserResponse]: pass

    @abstractmethod
    async def verify_refresh_token(self, refresh_token: str) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_terms_of_service(self) -> Optional[TermsOfService]: pass

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

    async def check_health(self) -> dict:
        try:
            is_db_healthy = await self.user_repo.check_database_health()
            
            if not is_db_healthy:
                return {
                    "status": "error",
                    "message": "database unreachable"
                }
            
            return {
                "status": "ok"
            }
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return {
                "status": "error",
                "message": "internal server error"
            } 

    async def create_user(self, user: UserCreate) -> Optional[UserResponse]:
        try:
            return await self.user_repo.create_user(user)
        except DuplicateUserError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        try:
            return await self.user_repo.get_user_by_email(email)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)
        
    async def get_terms_of_service(self) -> Optional[TermsOfService]:
        try:
            return await self.user_repo.get_terms_of_service()
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def verify_credentials(self, email: str, password: str) -> Optional[UserResponse]:
        try:
            user_with_password = await self.user_repo.get_user_by_email_with_password(email)
            if not user_with_password:
                raise UserServiceError(
                    self.config.ApplicationMessages.en.InvalidCredentials.Message,
                    self.config.ApplicationMessages.en.InvalidCredentials.Key
                )
            if not bcrypt.checkpw(password.encode('utf-8'), user_with_password['password_hash'].encode('utf-8')):
                raise UserServiceError(
                    self.config.ApplicationMessages.en.InvalidCredentials.Message,
                    self.config.ApplicationMessages.en.InvalidCredentials.Key
                )
            return await self.get_user_by_email(email)
        except UserNotFoundError as e:
            raise UserServiceError(e.message, e.code)
        except RepositoryError as e:
            raise UserServiceError(e.message, e.code)

    async def verify_refresh_token(self, refresh_token: str) -> Optional[UserResponse]:
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
            return await self.get_user_by_id(user_id)
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

    async def login_for_access_token(self, email: str, password: str) -> Token:
        # Get user by email
        user = await self.user_repo.get_user_by_email(email)
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

    async def refresh_token(self, refresh_token: RefreshToken) -> Token:
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
            user = await self.user_repo.get_user_by_id(user_id)
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