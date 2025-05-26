from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timedelta
import bcrypt
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from model.user_model import (
    Email, Id, VerifyUser, LoginRequest,
    LoginResponse, UserInfo, TokenInfo, SessionInfo,
    StandardResponse, ErrorInfo, MetaInfo, UserCreate, UserResponse, OtpResponse
)
from model.auth import Token, RefreshToken, TokenData
from config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from service.user_service import UserInteractor

class UserController:
    """
    UserController class handles all user-related operations and API endpoints.
    It acts as a bridge between the API routes and the business logic (UserService).
    """
    
    def __init__(
        self,
        user_service: UserInteractor,
        config: Config,
        logger: Logger,
        cache_handler: CacheHandler
    ):
        """
        Initialize the UserController with required dependencies.
        
        Args:
            user_service: Handles business logic for user operations
            config: Application configuration
            logger: For logging operations
            cache_handler: For handling Redis cache operations
        """
        self.user_service = user_service
        self.config = config
        self.logger = logger
        self.cache_handler = cache_handler

    def send_success_response(self, message: str, data: Optional[dict] = None) -> StandardResponse:
        """
        Creates a standardized success response.
        
        Args:
            message: Success message
            data: Optional data to include in response
            
        Returns:
            StandardResponse object with success status
        """
        return StandardResponse(
            success=True,
            message=message,
            data=data,
            meta=MetaInfo(
                timestamp=datetime.now(),
                version="1.0"
            )
        )

    def send_error_response(self, code: str, message: str, details: Optional[str] = None) -> StandardResponse:
        """
        Creates a standardized error response.
        
        Args:
            code: Error code
            message: Error message
            details: Optional detailed error information
            
        Returns:
            StandardResponse object with error status
        """
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

    async def get_users(self, db: AsyncSession) -> List[UserResponse]:
        """
        Retrieves all users from the database.
        
        Args:
            db: Database session
            
        Returns:
            List of UserResponse objects
            
        Raises:
            HTTPException: If there's an error retrieving users
        """
        try:
            users = await self.user_service.get_users(db)
            return users
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_user(self, user: UserCreate, db: AsyncSession) -> UserResponse:
        """
        Creates a new user in the system.
        
        Args:
            user: UserCreate object containing user details
            db: Database session
            
        Returns:
            UserResponse object for the created user
            
        Raises:
            HTTPException: If user creation fails
        """
        print(f"Creating user in controller: {user}")
        try:
            result = await self.user_service.create_user(user, db)
            if not result:
                print(f"Failed to create user in controller: {result}")
                raise HTTPException(status_code=400, detail="Failed to create user")
            return result
        except Exception as e:
            print(f"Error in create_user: {str(e)}")
            self.logger.error(f"Error in create_user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_by_email(self, email: Email, db: AsyncSession) -> UserResponse:
        """
        Retrieves a user by their email address.
        
        Args:
            email: Email object containing user's email
            db: Database session
            
        Returns:
            UserResponse object for the found user
            
        Raises:
            HTTPException: If user not found or other errors occur
        """
        try:
            user = await self.user_service.get_user_by_email(email, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )
            self.logger.info(f"User Data: {user}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> OtpResponse:
        """
        Generates and sends OTP to user's email for verification.
        
        Args:
            email: Email object containing user's email
            db: Database session
            
        Returns:
            OtpResponse object containing OTP information
            
        Raises:
            HTTPException: If user not found or already verified
        """
        try:
            otp = await self.user_service.get_otp_by_email(email, db)
            if not otp:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )
            self.logger.info(f"OTP sent successfully: {otp}")
            return otp
        except HTTPException:
            raise
        except Exception as e:
            if "USER_ALREADY_VERIFIED" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserAlreadyVerified"]["Message"]
                )
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> UserResponse:
        """
        Verifies a user's email using OTP.
        
        Args:
            user_info: VerifyUser object containing email and OTP
            db: Database session
            
        Returns:
            UserResponse object for the verified user
            
        Raises:
            HTTPException: If verification fails or user not found
        """
        try:
            user = await self.user_service.verify_user_by_email(user_info, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )
            self.logger.info(f"User verified successfully: {user}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            if "USER_ALREADY_VERIFIED" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserAlreadyVerified"]["Message"]
                )
            if "OTP_UN_MATCH_ERROR" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["OtpUnMatchError"]["Message"]
                )
            raise HTTPException(status_code=500, detail=str(e))

    async def signup(self, user: UserCreate, db: AsyncSession) -> Token:
        """
        Handles user signup process and returns authentication tokens.
        
        Args:
            user: UserCreate object containing user details
            db: Database session
            
        Returns:
            Token object containing access and refresh tokens
            
        Raises:
            HTTPException: If signup fails or user already exists
        """
        try:
            created_user = await self.user_service.create_user(user, db)
            access_token = await self.create_access_token(created_user)
            refresh_token = await self.create_refresh_token(created_user)

            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600
            )
        except Exception as e:
            if "DUPLICATE_USER" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["DuplicateUser"]["Message"]
                )
            raise HTTPException(status_code=500, detail=str(e))

    async def login(self, token_data: TokenData, db: AsyncSession) -> Token:
        """
        Handles user login and returns authentication tokens.
        
        Args:
            token_data: TokenData object containing email and password
            db: Database session
            
        Returns:
            Token object containing access and refresh tokens
            
        Raises:
            HTTPException: If login fails, user not found, or not verified
        """
        try:
            existing_user = await self.user_service.get_user_by_email(Email(email=token_data.email), db)
            if not existing_user:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )

            if not existing_user.is_verified:
                raise HTTPException(
                    status_code=403,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotVerified"]["Message"]
                )

            if not bcrypt.checkpw(
                token_data.password.encode('utf-8'),
                existing_user.password.encode('utf-8')
            ):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["PasswordMismatch"]["Message"]
                )

            access_token = await self.create_access_token(existing_user)
            refresh_token = await self.create_refresh_token(existing_user)

            # Store tokens in Redis for session management
            await self.cache_handler.set(f"accessToken_{existing_user.id}", access_token, 3600)
            await self.cache_handler.set(f"refreshToken_{existing_user.id}", refresh_token, 86400)

            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_user(self, email: str, otp: str, db: AsyncSession) -> OtpResponse:
        """
        Verifies user's OTP for email verification.
        
        Args:
            email: User's email address
            otp: One-time password
            db: Database session
            
        Returns:
            OtpResponse object containing verification status
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            result = await self.user_service.verify_user(email, otp, db)
            if not result:
                raise HTTPException(status_code=400, detail="Invalid OTP or email")
            return result
        except Exception as e:
            self.logger.error(f"Error in verify_user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def login_for_access_token(self, email: str, password: str, db: AsyncSession) -> Token:
        """
        Alternative login method that returns only access token.
        
        Args:
            email: User's email address
            password: User's password
            db: Database session
            
        Returns:
            Token object containing access token
            
        Raises:
            HTTPException: If login fails
        """
        try:
            result = await self.user_service.login_for_access_token(email, password, db)
            if not result:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            return result
        except Exception as e:
            self.logger.error(f"Error in login_for_access_token: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def refresh_token(self, refresh_token: RefreshToken, db: AsyncSession) -> Token:
        """
        Generates new access token using refresh token.
        
        Args:
            refresh_token: RefreshToken object
            db: Database session
            
        Returns:
            Token object containing new access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            result = await self.user_service.refresh_token(refresh_token, db)
            if not result:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            return result
        except Exception as e:
            self.logger.error(f"Error in refresh_token: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_access_token(self, user: UserResponse) -> str:
        """
        Creates JWT access token for user authentication.
        
        Args:
            user: UserResponse object containing user details
            
        Returns:
            JWT access token string
        """
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
        """
        Creates JWT refresh token for token renewal.
        
        Args:
            user: UserResponse object containing user details
            
        Returns:
            JWT refresh token string
        """
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