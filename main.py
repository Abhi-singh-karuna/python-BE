# Import necessary libraries and modules
from fastapi import FastAPI, Depends  # FastAPI framework for building APIs
from fastapi.middleware.cors import CORSMiddleware  # Middleware for handling CORS
from config.database import get_connection, init_db  # Database connection utilities
from config import Config  # Configuration management
from utils.logger import Logger  # Logger utility for logging events
from utils.cache_handler import CacheHandler  # Cache handler for Redis
from repository.user_repository import UserRepository  # User repository for database operations
from service.user_service import UserInteractor  # Service layer for user-related business logic
from controller.user_controller import UserController  # Controller for handling user-related API requests
from model.user_model import UserCreate, UserResponse  # Importing user-related data models
from model.auth import Token, TokenData, RefreshToken  # Importing authentication-related models
from middleware.auth_middleware import auth_middleware  # Import auth middleware for protected routes

# Create an instance of the FastAPI application
app = FastAPI(title="Authentication API")

# Configure CORS (Cross-Origin Resource Sharing) to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow credentials to be included in requests
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize application dependencies
config = Config()  # Load application configuration
logger = Logger(name="auth_app")  # Create a logger instance for the application

# Configure Redis for caching
redis_conf = config.get('redis')['write']  # Get Redis configuration from the settings
redis_url = f"redis://:{redis_conf['password']}@{redis_conf['host']}:{redis_conf['port']}/{redis_conf['database']}"  # Construct Redis URL
cache_handler = CacheHandler(redis_url=redis_url)  # Create a cache handler instance

# Initialize the user repository with dependencies
user_repo = UserRepository(logger=logger, config=config, redis_client=cache_handler)  # Create a user repository instance

# Initialize the user service with the repository and other dependencies
user_service = UserInteractor(
    user_repo=user_repo,  # Pass the user repository
    logger=logger,  # Pass the logger
    config=config,  # Pass the configuration
)

# Initialize the user controller with the service and other dependencies
user_controller = UserController(
    user_service=user_service,  # Pass the user service
    config=config,  # Pass the configuration
    logger=logger,  # Pass the logger
    cache_handler=cache_handler  # Pass the cache handler
)

# Define a startup event to initialize the database when the application starts
@app.on_event("startup")
async def startup_event():
    await init_db()  # Initialize the database connection

# Define an API endpoint for user signup
@app.post("/auth/signup", response_model=Token)
async def signup(user: UserCreate, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.signup(user, db)  # Call the controller method to sign up user

# Define an API endpoint for user login
@app.post("/auth/login", response_model=Token)
async def login(token_data: TokenData, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.login(token_data, db)  # Call the controller method to log in user

# Define an API endpoint to refresh the access token
@app.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: RefreshToken, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.refresh_token(refresh_token, db)  # Call the controller method to refresh token

# Define an API endpoint to get user information
@app.get("/auth/user", response_model=UserResponse)
async def get_user(
    db=Depends(get_connection),
    current_user: dict = Depends(auth_middleware)
):  # Use dependency injection for the database and auth middleware
    return await user_controller.get_user(db, current_user)  # Call the controller method to get user info

# Run the application using Uvicorn server
if __name__ == "__main__":
    import uvicorn  # Import Uvicorn for running the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Start the server on host 0.0.0.0 and port 8000