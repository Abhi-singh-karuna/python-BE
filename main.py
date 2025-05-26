# Import necessary libraries and modules
from fastapi import FastAPI
from config.database import init_db, close_pool
from config import Config
from utils.logger import Logger
from utils.cache_handler import CacheHandler
from repository.user_repository import UserRepository
from service.user_service import UserInteractor
from controller.user_controller import UserController
from middleware.request_middleware import RequestMiddleware
from middleware.cors_middleware import default_cors_config, CORSMiddleware
from router import api_router

# Create an instance of the FastAPI application
app = FastAPI(title="Authentication API")

# Configure CORS using the middleware configuration
app.add_middleware(CORSMiddleware, **default_cors_config.get_middleware())

# Add request middleware for tracing and monitoring
app.add_middleware(RequestMiddleware, slow_request_threshold=1.0)

# Initialize application dependencies
config = Config()
logger = Logger(name="auth_app")

# Configure Redis for caching
redis_conf = config.get('redis')['write']
redis_url = f"redis://:{redis_conf['password']}@{redis_conf['host']}:{redis_conf['port']}/{redis_conf['database']}"
cache_handler = CacheHandler(redis_url=redis_url)

# Initialize the user repository with dependencies
user_repo = UserRepository(logger=logger, config=config, redis_client=cache_handler)

# Initialize the user service with the repository and other dependencies
user_service = UserInteractor(user_repo=user_repo, logger=logger, config=config)

# Initialize the user controller with the service and other dependencies
user_controller = UserController(user_service=user_service, config=config, logger=logger, cache_handler=cache_handler)

# Include API routes
app.include_router(api_router)

# Define startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await init_db()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application on shutdown"""
    await close_pool()
    logger.info("Application shutdown complete")

# Run the application using Uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)