from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from config.config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from datetime import datetime
from model.user_model import UserCreate, UserResponse, VerifyUser, OtpResponse
from database import DatabaseConnection
import bcrypt
from .queries import *
from utils.token_generator import generate_secure_token


DATE_FORMAT_RFC3339 = "%Y-%m-%dT%H:%M:%S.%fZ" 

class RepositoryError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DuplicateUserError(RepositoryError):
    pass

class UserNotFoundError(RepositoryError):
    pass

class InvalidCredentialsError(RepositoryError):
    pass

class Repository(ABC):
    @abstractmethod
    async def get_users(self) -> List[UserResponse]: pass

    @abstractmethod
    async def create_user(self, user: UserCreate) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]: pass

    @abstractmethod
    async def verify_user_by_email(self, verify_user: VerifyUser) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_otp_by_email(self, email: str) -> Optional[OtpResponse]: pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Tuple[bool, Optional[UserResponse], Optional[str]]: pass

class UserRepository(Repository):
    def __init__(self, logger: Logger, config: Config, redis_client: CacheHandler):
        self.logger = logger
        self.config = config
        self.redis_client = redis_client

    async def get_users(self) -> List[UserResponse]:
        try:
            rows = await DatabaseConnection.fetch(GET_ALL_USERS)
            users = []

            for row in rows:
                try:
                    created_at = datetime.strptime(row["created_at"], DATE_FORMAT_RFC3339)
                    updated_at = datetime.strptime(row["updated_at"], DATE_FORMAT_RFC3339)
                except Exception as e:
                    self.logger.error(f"Date parsing error: {e}")
                    created_at = updated_at = None

                user = UserResponse(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    phone_no=row["phone_no"],
                    is_verified=row["is_verified"],
                    is_active=row["is_active"],
                    created_at=created_at,
                    updated_at=updated_at,
                )
                users.append(user)

            self.logger.debug(f"User list: {users}")
            return users
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            raise

    async def create_user(self, user: UserCreate) -> Optional[UserResponse]:
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, user.email)
            if row:
                raise DuplicateUserError("User already exists.", "DUPLICATE_USER")

            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            verification_token = generate_secure_token()

            await DatabaseConnection.execute( CREATE_USER,
                user.first_name,
                user.last_name,
                user.email,
                hashed_password.decode('utf-8'),
                user.phone_no,
                user.profile_picture,
                verification_token
            )
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, user.email)
            if not row:
                return None

            # Map the tuple to field names (must match order in GET_USER_BY_EMAIL)
            user_dict = {
                "id": row[0],
                "is_active": row[2],
            }

            return UserResponse(**user_dict)
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, email)
            if not row:
                return None

            # Map the tuple to field names (must match order in GET_USER_BY_EMAIL)
            user_dict = {
                "id": row[0],
                # "password": row[1],
                "is_active": row[2],
                # "is_active": row[3],
                # "created_at": row[3],
                # "updated_at": row[4],
            }

            return UserResponse(**user_dict)
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise


    async def verify_user_by_email(self, verify_user: VerifyUser) -> Optional[UserResponse]:
        try:
            otp = await DatabaseConnection.fetchrow(VERIFY_USER_OTP, verify_user.email, verify_user.otp)
            if not otp:
                return None

            now = datetime.utcnow()
            await DatabaseConnection.execute(UPDATE_USER_VERIFICATION, now, verify_user.email)
            await DatabaseConnection.execute(MARK_OTP_USED, verify_user.email, verify_user.otp)

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
                otp=row["otp"],
                created_at=row["created_at"]
            )
        except Exception as e:
            self.logger.error(f"Error getting OTP: {str(e)}")
            raise

    async def get_user_by_id(self, user_id: str) -> Tuple[bool, Optional[UserResponse], Optional[str]]:
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_ID, user_id)
            if not row:
                return False, None, "User not found"
            return True, UserResponse(**row), None
        except Exception as e:
            self.logger.error(f"Error getting user by id: {str(e)}")
            return False, None, str(e)

    async def get_user_by_email_with_password(self, email: str) -> Optional[dict]:
        try:
            row = await DatabaseConnection.fetchrow(GET_USER_BY_EMAIL, email)
            return row
        except Exception as e:
            self.logger.error(f"Error getting user by email with password: {str(e)}")
            raise

async def get_connection():
    return await DatabaseConnection.get_connection()
