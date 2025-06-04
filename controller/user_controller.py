from model.user_model import ( Email, UserCreate)
from model.response.response_model import create_success_response, create_error_response, ApiResponse
from config.config import Config
from utils.logger import Logger
from service.user_service import UserInteractor, UserServiceError
from datetime import datetime, timedelta
from jose import jwt
from model.user_model import TokenData, RefreshToken, UserResponse

class UserController:
    """
    UserController class handles all user-related operations.
    It manages user CRUD operations, verification, and profile management.
    """
    
    def __init__(
        self,
        user_service: UserInteractor,
        config: Config,
        logger: Logger
    ):
        self.user_service = user_service
        self.config = config
        self.logger = logger


    async def check_health(self) -> ApiResponse:
        """Checks the health of the user service."""
        try:
            result = await self.user_service.check_health() 
            # return create_success_response(
            #     message="User service is healthy",
            #     data={"status": "ok"}
            # )
            return {"status": "ok"}
        except UserServiceError as e:
            return create_error_response(
                code=e.code,
                message=e.message
            )
        

    async def signup(self, user: UserCreate) -> ApiResponse:
        """Handles user signup process and returns authentication tokens."""
        try:
            # Create user in database and return the user details
            created_user = await self.user_service.create_user(user)

            return create_success_response(
                message=self.config.ApplicationMessages[self.config.current_lang].CreateUserSuccess.Message,
                data = created_user.model_dump()
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
                message=self.config.ApplicationMessages[self.config.current_lang].RefreshTokenSuccess.Message,
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
    

    async def create_user(self, user: UserCreate, db) -> ApiResponse:
        """Creates a new user in the system."""
        try:
            result = await self.user_service.create_user(user, db)
            if not result:
                return create_error_response(
                    code=self.config.ApplicationMessages[self.config.current_lang].CreateUserError.Key,
                    message=self.config.ApplicationMessages[self.config.current_lang].CreateUserError.Message
                )
            return create_success_response(
                message=self.config.ApplicationMessages[self.config.current_lang].CreateUserSuccess.Message,
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
                code=self.config.ApplicationMessages[self.config.current_lang].CreateUserError.Key,
                message=str(e)
            )

    async def get_user_by_email(self, email: Email) -> ApiResponse:
        """Retrieves a user by their email address."""
        try:
            user = await self.user_service.get_user_by_email(email.email)
            if not user:
                return create_error_response(
                    code=self.config.ApplicationMessages[self.config.current_lang].UserNotFound.Key,
                    message=self.config.ApplicationMessages[self.config.current_lang].UserNotFound.Message
                )
            return create_success_response(
                message=self.config.ApplicationMessages[self.config.current_lang].GetUserSuccess.Message,
                data=user.model_dump()
            )
        except UserServiceError as e:
            return create_error_response(
                code=e.code,
                message=e.message
            )
        except Exception as e:
            return create_error_response(
                code=self.config.ApplicationMessages[self.config.current_lang].GetUserError.Key,
                message=str(e)
            )
        
    async def get_terms_of_service(self) -> ApiResponse:
        """Retrieves the complete Terms of Service with sub-content."""
        try:
            terms = await self.user_service.get_terms_of_service()
            return create_success_response(
                message=self.config.ApplicationMessages[self.config.current_lang].GetTermsOfServiceSuccess.Message,
                data=terms.model_dump()
            )
        except UserServiceError as e:
            return create_error_response(
                code=e.code,
                message=e.message
            )   
        