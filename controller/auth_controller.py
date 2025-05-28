from datetime import datetime, timedelta
from jose import jwt
from model.user_model import UserCreate, UserResponse
from model.auth import TokenData, RefreshToken
from model.response_model import ApiResponse, create_success_response, create_error_response
from config.config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from service.user_service import UserInteractor, UserServiceError

class AuthController:
    """
    AuthController class handles all authentication-related operations.
    It manages user signup, login, token generation and refresh.
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

    async def signup(self, user: UserCreate) -> ApiResponse:
        """Handles user signup process and returns authentication tokens."""
        try:
            # Create user in database
            created_user = await self.user_service.create_user(user)

            # Generate tokens
            access_token = await self.create_access_token(created_user)
            refresh_token = await self.create_refresh_token(created_user)

            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }

            return create_success_response(
                message="User created successfully",
                data=token_data
            )
        except UserServiceError as e:
            self.logger.error(f"Error in signup: {str(e)}")
            return create_error_response(
                code=e.code,
                message=e.message,
                details=e.message
            )

    async def login(self, token_data: TokenData) -> ApiResponse:
        """Handles user login and returns authentication tokens."""
        try:
            # Verify credentials and get user
            user = await self.user_service.verify_credentials(token_data.email, token_data.password)

            # Generate tokens
            access_token = await self.create_access_token(user)
            refresh_token = await self.create_refresh_token(user)

            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }

            return create_success_response(
                message="Login successful..",
                data=token_data
            )
        except UserServiceError as e:
            self.logger.error(f"Error in login: {str(e)}")
            return create_error_response(
                code=e.code,
                message=e.message,
                details=e.message
            )

    async def refresh_token(self, refresh_token: RefreshToken) -> ApiResponse:
        """Refreshes the access token using a valid refresh token."""
        try:
            # Verify refresh token and get user
            user = await self.user_service.verify_refresh_token(refresh_token.refresh_token)

            # Generate new tokens
            access_token = await self.create_access_token(user)
            new_refresh_token = await self.create_refresh_token(user)

            token_data = {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }

            return create_success_response(
                message="Token refreshed successfully",
                data=token_data
            )
        except UserServiceError as e:
            self.logger.error(f"Error in refresh_token: {str(e)}")
            return create_error_response(
                code=e.code,
                message=e.message,
                details=e.message
            )

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