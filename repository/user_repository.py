from abc import ABC, abstractmethod
from typing import Optional
from config.config import Config
from utils.logger import Logger
from model.user_model import UserCreate, UserResponse, TermsOfService, TermsSubContent
from database import DatabaseConnection
import bcrypt
from .database_queries.queries import *
from utils.token_generator import generate_secure_token


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
    async def check_database_health(self) -> bool: pass

    @abstractmethod
    async def create_user(self, user: UserCreate) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]: pass

    @abstractmethod
    async def get_terms_of_service(self) -> Optional[TermsOfService]: pass


class UserRepository(Repository):
    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config

    # Check database health
    async def check_database_health(self) -> bool:
        try:
            # Execute a simple query to check database connectivity
            await DatabaseConnection.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False


    async def create_user(self, user: UserCreate) -> Optional[UserResponse]:
        try:
            row = await DatabaseConnection.fetchrow(QUERY_GET_USER_BY_EMAIL, user.email)
            if row:
                raise DuplicateUserError(self.config.ApplicationMessages[self.config.current_lang].DuplicateUser.Message, self.config.ApplicationMessages[self.config.current_lang].DuplicateUser.Key)

            hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
            verification_token = generate_secure_token()

            await DatabaseConnection.execute(QUERY_CREATE_USER,
                user.first_name,
                user.last_name,
                user.email,
                hashed_password.decode('utf-8'),
                user.phone_no,
                user.profile_picture,
                verification_token,
                user.ip_address,
                user.tos_accept_datetime
            )
            row = await DatabaseConnection.fetchrow(QUERY_GET_USER_BY_EMAIL, user.email)
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
            row = await DatabaseConnection.fetchrow(QUERY_GET_USER_BY_EMAIL, email)
            if not row:
                return None

            # Map the tuple to field names (must match order in GET_USER_BY_EMAIL)
            user_dict = {
                "id": row[0],
                "is_active": row[2],
            }

            return UserResponse(**user_dict)
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise

    async def get_terms_of_service(self) -> Optional[TermsOfService]:
        try:
            rows = await DatabaseConnection.fetch(QUERY_GET_TERMS_OF_SERVICE)

            if not rows:
                return None

            # Build main Terms of Service data from the first row
            first_row = rows[0]
            terms_data = {
                # "id": first_row["terms_id"],
                "title": first_row["terms_title"],
                "subtitle": first_row["terms_subtitle"],
                "content": first_row["terms_content"],
                "sub_content": []
            }

           # Collect sub_content rows without duplicates
            sub_contents = []
            seen_sub_ids = set()

            for row in rows:
                sub_id = row["sub_id"]
                if sub_id and sub_id not in seen_sub_ids:
                    sub_contents.append(
                        TermsSubContent(
                            # id=sub_id,
                            title=row["sub_title"],
                            content=row["sub_content"],
                            # sort_order=row["sort_order"]
                        )
                    )
                    seen_sub_ids.add(sub_id)

            terms_data["sub_content"] = sub_contents
            return TermsOfService(**terms_data)

        except Exception as e:
            self.logger.error(f"Error fetching Terms of Service: {str(e)}")
            raise


# Get database connection
async def get_connection():
    return await DatabaseConnection.get_connection()

