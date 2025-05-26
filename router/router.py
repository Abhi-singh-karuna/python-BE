from fastapi import APIRouter, Depends
from controller.user_controller import UserController
from middleware.auth_middleware import auth_middleware
from database import Database
from config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler

router = APIRouter()

# Initialize dependencies
db = Database()
config = Config()
logger = Logger()
cache_handler = CacheHandler()

# Initialize controller
user_controller = UserController(
    db=db,
    config=config,
    logger=logger,
    cache_handler=cache_handler
)

# Auth routes
router.post("/auth/signup")(user_controller.signup)
router.post("/auth/login")(user_controller.login)
router.post("/auth/refresh")(user_controller.refresh_token)
router.get("/auth/user", dependencies=[Depends(auth_middleware)])(user_controller.get_user) 