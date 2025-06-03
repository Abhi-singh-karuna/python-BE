from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from database import DatabaseConnection
from config.config import load_config
from utils.logger import Logger
from repository.user_repository import UserRepository
from service.user_service import UserInteractor
from controller.user_controller import UserController
from middleware.cors_middleware import default_cors_config, CORSMiddleware
from middleware.logging_middleware import LoggingMiddleware
from router.user_router import get_user_router
from model.schemas.base import validation_exception_handler
from router.user_router import get_user_router

# Create an instance of the FastAPI application
app = FastAPI(title="PolicyPro Service")

# Load configuration
config = load_config("config/config.yml")

# Configure CORS using the middleware configuration
app.add_middleware(CORSMiddleware, **default_cors_config.get_middleware())

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add custom validation exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Initialize application dependencies
logger = Logger(name="policy_pro_app")

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
    global user_repo, user_service, user_controller, auth_controller
    user_repo = UserRepository(logger=logger, config=config)
    user_service = UserInteractor(user_repo=user_repo, logger=logger, config=config)
    user_controller = UserController(user_service=user_service, config=config, logger=logger)
    # auth_controller = AuthController(user_service=user_service, config=config, logger=logger)
    
    # Include routers with their respective controllers
    app.include_router(get_user_router(user_controller))
    
    logger.info("Application startup complete")

    # TODO: {REMOVE} printlogger for checking the config
    logger.info(f"Application startup - check logger :{config.ApplicationMessages[config.current_lang].UserNotFound.Key} --  {config.ApplicationMessages[config.current_lang].UserNotFound.Message}")

    # TODO: {REMOVE} printlogger for checking the databse config
    logger.info(f"Application startup - check database config : HOST : {config.general.sql.write.host} -- PORT : {config.general.sql.write.port} -- USER : {config.general.sql.write.user} -- PASSWORD : {config.general.sql.write.password} -- DATABASE : {config.general.sql.write.database}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application on shutdown"""
    await DatabaseConnection.close_pool()
    logger.info("Application shutdown complete") 

# Run the application using Uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.general.router.port)