from abc import ABC, abstractmethod
from typing import List, Optional
from config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
import uuid
from datetime import datetime
from model.user_model import UserBase, UserCreate, UserResponse, VerifyUser, OtpResponse
from config.database import get_connection
import aiomysql

class Repository(ABC):
    @abstractmethod
    async def get_users(self, db) -> List[UserResponse]:
        pass

    @abstractmethod
    async def create_user(self, user: UserCreate, db) -> Optional[UserResponse]:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str, db) -> Optional[UserResponse]:
        pass

    @abstractmethod
    async def verify_user_by_email(self, verify_user: VerifyUser, db) -> Optional[UserResponse]:
        pass

    @abstractmethod
    async def get_otp_by_email(self, email: str, db) -> Optional[OtpResponse]:
        pass

class Database(Repository):
    def __init__(self, logger: Logger, config: Config, redis_client: CacheHandler):
        self.logger = logger
        self.config = config
        self.redis_client = redis_client

    async def get_users(self, db) -> List[UserResponse]:
        try:
            async with db.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users")
                users = await cursor.fetchall()
                return [UserResponse(**user) for user in users]
        except Exception as e:
            self.logger.error(f"Error getting users: {str(e)}")
            raise

    async def create_user(self, user: UserCreate, db) -> Optional[UserResponse]:
        print(f"Creating user in repository: {user}")
        try:
            async with db.cursor(aiomysql.DictCursor) as cursor:
                user_id = str(uuid.uuid4())
                now = datetime.utcnow()
                query = """
                    INSERT INTO users (
                        id, name, email, password, phone_no, is_verified,
                        is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(
                    query,
                    (
                        user_id,
                        user.name,
                        user.email,
                        user.password,
                        user.phone_no,
                        False,
                        True,
                        now,
                        now
                    )
                )
                await db.commit()

                # Fetch the created user
                await cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                created_user = await cursor.fetchone()
                return UserResponse(**created_user) if created_user else None
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise

    async def get_user_by_email(self, email: str, db) -> Optional[UserResponse]:
        try:
            async with db.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = await cursor.fetchone()
                return UserResponse(**user) if user else None
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise

    async def verify_user_by_email(self, verify_user: VerifyUser, db) -> Optional[UserResponse]:
        try:
            async with db.cursor(aiomysql.DictCursor) as cursor:
                # First verify the OTP
                await cursor.execute(
                    "SELECT * FROM otps WHERE email = %s AND otp = %s AND is_used = 0",
                    (verify_user.email, verify_user.otp)
                )
                otp = await cursor.fetchone()
                if not otp:
                    return None

                # Update user verification status
                now = datetime.utcnow()
                await cursor.execute(
                    """
                    UPDATE users 
                    SET is_verified = 1, updated_at = %s 
                    WHERE email = %s
                    """,
                    (now, verify_user.email)
                )

                # Mark OTP as used
                await cursor.execute(
                    "UPDATE otps SET is_used = 1 WHERE email = %s AND otp = %s",
                    (verify_user.email, verify_user.otp)
                )

                await db.commit()

                # Fetch and return updated user
                await cursor.execute("SELECT * FROM users WHERE email = %s", (verify_user.email,))
                user = await cursor.fetchone()
                return UserResponse(**user) if user else None
        except Exception as e:
            self.logger.error(f"Error verifying user: {str(e)}")
            raise

    async def get_otp_by_email(self, email: str, db) -> Optional[OtpResponse]:
        try:
            async with db.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """
                    SELECT otp, created_at 
                    FROM otps 
                    WHERE email = %s AND is_used = 0 
                    ORDER BY created_at DESC 
                    LIMIT 1
                    """,
                    (email,)
                )
                result = await cursor.fetchone()
                if not result:
                    return None
                return OtpResponse(
                    email=email,
                    otp=result['otp'],
                    created_at=result['created_at']
                )
        except Exception as e:
            self.logger.error(f"Error getting OTP: {str(e)}")
            raise 
        
