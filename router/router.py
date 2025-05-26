from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel
from controller.user_controller import UserController
from middleware.auth_middleware import auth_middleware, auth_verified_middleware
from database import Database
from config import Config
from utils.logger import Logger
from utils.email_service import EmailService
from utils.cache_handler import CacheHandler

router = APIRouter()

# Initialize dependencies
db = Database()
config = Config()
logger = Logger()
email_service = EmailService()
cache_handler = CacheHandler()

# Initialize controller
user_controller = UserController(
    db=db,
    config=config,
    logger=logger,
    email_service=email_service,
    cache_handler=cache_handler
)

# Public routes
router.post("/signup")(user_controller.signup)
router.post("/otp")(user_controller.get_otp_by_email)
router.post("/user/verify")(user_controller.verify_user_by_email)
router.post("/login")(user_controller.login)
router.post("/refresh")(user_controller.refresh_token)

# Protected routes (Auth middleware)
router.get("/users", dependencies=[Depends(auth_verified_middleware)])(user_controller.get_users)
router.post("/user/email", dependencies=[Depends(auth_verified_middleware)])(user_controller.get_user_by_email)
router.post("/user")(user_controller.create_user) 