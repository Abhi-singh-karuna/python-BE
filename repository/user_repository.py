from abc import ABC, abstractmethod
from typing import List, Optional
from config.config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
import uuid
from datetime import datetime
from model.user_model import UserCreate, UserResponse, VerifyUser, OtpResponse
from database import DatabaseConnection
import bcrypt
from .queries import (
    GET_ALL_USERS,
    GET_USER_BY_EMAIL,
    GET_USER_BY_ID,
    CREATE_USER,
    GET_OTP_BY_EMAIL,
    VERIFY_USER_OTP,
    UPDATE_USER_VERIFICATION,
    MARK_OTP_USED
)

class RepositoryError(Exception):
    """Base exception for repository errors"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DuplicateUserError(RepositoryError):
    """Raised when attempting to create a user that already exists"""
    pass

class UserNotFoundError(RepositoryError):
    """Raised when a user cannot be found"""
    pass

class InvalidCredentialsError(RepositoryError):
    """Raised when user credentials are invalid"""
    pass

class Repository(ABC):
    @abstractmethod
    async def get_users(self) -> List[UserResponse]:pass
    @abstractmethod
    async def create_user(self, user: UserCreate) -> Optional[UserResponse]:pass
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:pass
    @abstractmethod
    async def verify_user_by_email(self, verify_user: VerifyUser) -> Optional[UserResponse]:pass
    @abstractmethod
    async def get_otp_by_email(self, email: str) -> Optional[OtpResponse]:pass
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:pass

class UserRepository(Repository):
    def __init__(self, logger: Logger, config: Config, redis_client: CacheHandler):
        self.logger = logger
        self.config = config
        self.redis_client = redis_client

    async def get_users(self) -> List[UserResponse]:
        try:
            rows = await DatabaseConnection.fetch(GET_ALL_USERS)
            return [UserResponse(**user) for user in rows]
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            raise

    async def create_user(self, user: UserCreate) -> Optional[UserResponse]:
        """
        Creates a new user in the database.
        
        Args:
            user: UserCreate object containing user details
            db: Database connection (kept for interface compatibility)
            
        Returns:
            UserResponse object if user is created successfully, None otherwise
        """
        try:
            # Check if user already exists
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, user.email)
            if row:
                raise DuplicateUserError("User already exists.", "DUPLICATE_USER")

            # Hash password
            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

            # Create user
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            await DatabaseConnection.execute(
                CREATE_USER,
                user_id,
                user.name,
                user.email,
                hashed_password.decode('utf-8'),
                user.phone_no,
                True,  # Auto-verify for simplicity
                True,
                now,
                now
            )

            # Fetch the created user
            created_user = await DatabaseConnection.fetchrow(GET_USER_BY_ID, user_id)
            return UserResponse(**created_user) if created_user else None
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Retrieves a user by their email address.
        
        Args:
            email: User's email address
            db: Database connection (kept for interface compatibility)
            
        Returns:
            UserResponse object if user is found, None otherwise
        """
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, email)
            return UserResponse(**row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise

    async def verify_user_by_email(self, verify_user: VerifyUser) -> Optional[UserResponse]:
        try:
            # First verify the OTP
            otp = await DatabaseConnection.fetchrow(VERIFY_USER_OTP, verify_user.email, verify_user.otp)
            if not otp:
                return None

            # Update user verification status
            now = datetime.utcnow()
            await DatabaseConnection.execute(UPDATE_USER_VERIFICATION, now, verify_user.email)

            # Mark OTP as used
            await DatabaseConnection.execute(MARK_OTP_USED, verify_user.email, verify_user.otp)

            # Fetch and return updated user
            user = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, verify_user.email)
            return UserResponse(**user) if user else None
        except Exception as e:
            self.logger.error(f"Error verifying user: {str(e)}")
            raise

    async def get_otp_by_email(self, email: str) -> Optional[OtpResponse]:
        try:
            row = await DatabaseConnection.fetchrow(GET_OTP_BY_EMAIL, email)
            if not row:
                return None
            return OtpResponse(
                email=email,
                otp=row['otp'],
                created_at=row['created_at']
            )
        except Exception as e:
            self.logger.error(f"Error getting OTP: {str(e)}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Retrieves a user by their ID.
        
        Args:
            user_id: User's ID
            db: Database connection (kept for interface compatibility)
            
        Returns:
            UserResponse object if user is found, None otherwise
        """
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_ID, user_id)
            return UserResponse(**row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting user by id: {str(e)}")
            raise

    async def get_user_by_email_with_password(self, email: str) -> Optional[dict]:
        """
        Retrieves a user by their email address, including password.
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary containing user data including password if user is found, None otherwise
        """
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, email)
            return row
        except Exception as e:
            self.logger.error(f"Error getting user by email with password: {str(e)}")
            raise

async def get_connection():
    return await DatabaseConnection.get_connection() 
        
