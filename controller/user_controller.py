from fastapi import HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from model.user_model import (
    Email, Id, VerifyUser, UserInfo, UserCreate, UserResponse,
    OtpResponse
)
from model.response_model import create_success_response, create_error_response, ApiResponse
from config.config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from service.user_service import UserInteractor
from middleware.auth_middleware import auth_middleware

class UserController:
    """
    UserController class handles all user-related operations.
    It manages user CRUD operations, verification, and profile management.
    """
    
    def __init__(
        self,
        user_service: UserInteractor,
        config: Config,
        logger: Logger,
        cache_handler: CacheHandler
    ):
        self.user_service = user_service
        self.config = config
        self.logger = logger
        self.cache_handler = cache_handler

    async def get_users(self, db: AsyncSession) -> List[UserResponse]:
        """Retrieves all users from the database."""
        try:
            users = await self.user_service.get_users(db)
            return users
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_user(self, user: UserCreate, db: AsyncSession) -> UserResponse:
        """Creates a new user in the system."""
        try:
            result = await self.user_service.create_user(user, db)
            if not result:
                raise HTTPException(status_code=400, detail="Failed to create user")
            return result
        except Exception as e:
            self.logger.error(f"Error in create_user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_by_email(self, email: Email, db: AsyncSession) -> UserResponse:
        """Retrieves a user by their email address."""
        try:
            user = await self.user_service.get_user_by_email(email, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages.en.UserNotFound.Message
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_otp_by_email(self, email: Email, db: AsyncSession) -> OtpResponse:
        """Generates and sends OTP to user's email for verification."""
        try:
            otp = await self.user_service.get_otp_by_email(email, db)
            if not otp:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages.en.UserNotFound.Message
                )
            return otp
        except HTTPException:
            raise
        except Exception as e:
            if "USER_ALREADY_VERIFIED" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail=self.config.ApplicationMessages.en.UserAlreadyVerified.Message
                )
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_user_by_email(self, user_info: VerifyUser, db: AsyncSession) -> UserResponse:
        """Verifies a user's email using OTP."""
        try:
            user = await self.user_service.verify_user_by_email(user_info, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )
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

    async def get_user(self, db: AsyncSession, current_user: dict = Depends(auth_middleware)) -> UserResponse:
        """Retrieves the current user's information."""
        try:
            user = await self.user_service.get_user_by_id(current_user["id"], db)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error in get_user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 