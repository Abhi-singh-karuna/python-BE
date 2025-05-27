# Import necessary libraries and modules
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from database import DatabaseConnection
from database.redis import RedisConnection
from config.config import load_config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from repository.user_repository import UserRepository
from service.user_service import UserInteractor
from controller.user_controller import UserController
from controller.auth_controller import AuthController
from middleware.cors_middleware import default_cors_config, CORSMiddleware
from middleware.logging_middleware import LoggingMiddleware
from router.auth_router import get_auth_router
from model.schemas.base import validation_exception_handler

# Create an instance of the FastAPI application
app = FastAPI(title="Authentication API")

# Load configuration
config = load_config("config/config.yml")

# Configure CORS using the middleware configuration
app.add_middleware(CORSMiddleware, **default_cors_config.get_middleware())

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add custom validation exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Initialize application dependencies
logger = Logger(name="auth_app")
cache_handler = None  # Will be initialized in startup

# Initialize the user repository with dependencies
user_repo = None  # Will be initialized in startup

# Initialize the user service with the repository and other dependencies
user_service = None  # Will be initialized in startup

# Initialize the controllers with the service and other dependencies
user_controller = None  # Will be initialized in startup
auth_controller = None  # Will be initialized in startup

# Define startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await DatabaseConnection.init_db()
    global cache_handler, user_repo, user_service, user_controller, auth_controller
    redis_client = await RedisConnection.get_instance()
    cache_handler = CacheHandler(redis_client=redis_client)
    user_repo = UserRepository(logger=logger, config=config, redis_client=cache_handler)
    user_service = UserInteractor(user_repo=user_repo, logger=logger, config=config)
    user_controller = UserController(user_service=user_service, config=config, logger=logger, cache_handler=cache_handler)
    auth_controller = AuthController(user_service=user_service, config=config, logger=logger, cache_handler=cache_handler)
    
    # Include routers with their respective controllers
    app.include_router(get_auth_router(auth_controller, user_controller))
    
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application on shutdown"""
    await DatabaseConnection.close_pool()
    await RedisConnection.close()  # Close Redis connection
    logger.info("Application shutdown complete")

# Run the application using Uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.general.router.port)