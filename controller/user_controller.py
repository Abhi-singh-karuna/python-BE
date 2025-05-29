from sqlalchemy.ext.asyncio import AsyncSession
from model.user_model import ( Email, VerifyUser, UserCreate, CurrentUser)
from model.response_model import create_success_response, create_error_response, ApiResponse
from config.config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from service.user_service import UserInteractor, UserServiceError

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

    async def get_users(self, db) -> ApiResponse:
        """Retrieves all users from the database."""
        try:
            users = await self.user_service.get_users(db)
            return create_success_response(
                message="Users retrieved successfully",
                data={"users": [user.model_dump() for user in users]}
            )
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            return create_error_response(
                code="GET_USERS_ERROR",
                message=str(e)
            )

    async def create_user(self, user: UserCreate, db) -> ApiResponse:
        """Creates a new user in the system."""
        try:
            result = await self.user_service.create_user(user, db)
            if not result:
                return create_error_response(
                    code="CREATE_USER_ERROR",
                    message="Failed to create user"
                )
            return create_success_response(
                message="User created successfully",
                data=result.model_dump()
            )
        except UserServiceError as e:
            self.logger.error(f"Error in create_user: {str(e)}")
            return create_error_response(
                code=e.code,
                message=e.message
            )
        except Exception as e:
            self.logger.error(f"Error in create_user: {str(e)}")
            return create_error_response(
                code="CREATE_USER_ERROR",
                message=str(e)
            )

    async def get_user_by_email(self, email: Email) -> ApiResponse:
        """Retrieves a user by their email address."""
        try:
            user = await self.user_service.get_user_by_email(email.email)
            if not user:
                return create_error_response(
                    code="USER_NOT_FOUND",
                    message=self.config.ApplicationMessages.en.UserNotFound.Message
                )
            return create_success_response(
                message="User retrieved successfully",
                data=user.model_dump()
            )
        except UserServiceError as e:
            return create_error_response(
                code=e.code,
                message=e.message
            )
        except Exception as e:
            return create_error_response(
                code="GET_USER_ERROR",
                message=str(e)
            )

    async def get_otp_by_email(self, email: Email, db) -> ApiResponse:
        """Generates and sends OTP to user's email for verification."""
        try:
            otp = await self.user_service.get_otp_by_email(email, db)
            if not otp:
                return create_error_response(
                    code="USER_NOT_FOUND",
                    message=self.config.ApplicationMessages.en.UserNotFound.Message
                )
            return create_success_response(
                message="OTP generated successfully",
                data=otp.model_dump()
            )
        except UserServiceError as e:
            if "USER_ALREADY_VERIFIED" in str(e):
                return create_error_response(
                    code="USER_ALREADY_VERIFIED",
                    message=self.config.ApplicationMessages.en.UserAlreadyVerified.Message
                )
            return create_error_response(
                code=e.code,
                message=e.message
            )
        except Exception as e:
            return create_error_response(
                code="GET_OTP_ERROR",
                message=str(e)
            )

    async def verify_user_by_email(self, user_info: VerifyUser, db) -> ApiResponse:
        """Verifies a user's email using OTP."""
        try:
            user = await self.user_service.verify_user_by_email(user_info, db)
            if not user:
                return create_error_response(
                    code="USER_NOT_FOUND",
                    message=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserNotFound"]["Message"]
                )
            return create_success_response(
                message="User verified successfully",
                data=user.model_dump()
            )
        except UserServiceError as e:
            if "USER_ALREADY_VERIFIED" in str(e):
                return create_error_response(
                    code="USER_ALREADY_VERIFIED",
                    message=self.config.ApplicationMessages[self.config.CurrentLanguage]["UserAlreadyVerified"]["Message"]
                )
            if "OTP_UN_MATCH_ERROR" in str(e):
                return create_error_response(
                    code="OTP_UN_MATCH_ERROR",
                    message=self.config.ApplicationMessages[self.config.CurrentLanguage]["OtpUnMatchError"]["Message"]
                )
            return create_error_response(
                code=e.code,
                message=e.message
            )
        except Exception as e:
            return create_error_response(
                code="VERIFY_USER_ERROR",
                message=str(e)
            )

    async def get_user(self, current_user: CurrentUser) -> ApiResponse:
        """Retrieves the current user's information."""
        success, user, error = await self.user_service.get_user_by_id(current_user.id)
        if not success:
            return create_error_response(
                code="USER_NOT_FOUND",
                message=error
            )
        return create_success_response(
            message="User retrieved successfully",
            data=user.model_dump()
        )
