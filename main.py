# Import necessary libraries and modules
from fastapi import FastAPI, Depends  # FastAPI framework for building APIs
from fastapi.middleware.cors import CORSMiddleware  # Middleware for handling CORS
from config.database import get_connection, init_db  # Database connection utilities
from config import Config  # Configuration management
from utils.logger import Logger  # Logger utility for logging events
from utils.cache_handler import CacheHandler  # Cache handler for Redis
from utils.email_service import EmailService  # Email service for sending emails
from repository.user_repository import Database  # User repository for database operations
from service.user_service import UserInteractor  # Service layer for user-related business logic
from controller.user_controller import UserController  # Controller for handling user-related API requests
from model.user_model import (  # Importing user-related data models
    UserBase, UserCreate, UserResponse, VerifyUser,
    OtpResponse, Email
)
from model.auth import Token, TokenData, RefreshToken  # Importing authentication-related models
from typing import List  # For type hinting lists

# Create an instance of the FastAPI application
app = FastAPI(title="Activity App API")

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
logger = Logger(name="activity_app")  # Create a logger instance for the application

# Configure Redis for caching
redis_conf = config.get('redis')['write']  # Get Redis configuration from the settings
redis_url = f"redis://:{redis_conf['password']}@{redis_conf['host']}:{redis_conf['port']}/{redis_conf['database']}"  # Construct Redis URL
cache_handler = CacheHandler(redis_url=redis_url)  # Create a cache handler instance

# Configure email service using SendGrid
api_key = config.get('SendGridAPIKey')  # Get SendGrid API key from configuration
from_email = config.get('SendGridFromEmail')  # Get sender email from configuration
from_name = config.get('SendGridFromName')  # Get sender name from configuration
email_service = EmailService(api_key, from_email, from_name)  # Create an email service instance

# Initialize the user repository with dependencies
user_repo = Database(logger=logger, config=config, redis_client=cache_handler)  # Create a user repository instance

# Initialize the user service with the repository and other dependencies
user_service = UserInteractor(
    user_repo=user_repo,  # Pass the user repository
    logger=logger,  # Pass the logger
    config=config,  # Pass the configuration
    email_service=email_service  # Pass the email service
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

# Define an API endpoint to get all users
@app.get("/users", response_model=List[UserResponse])
async def get_users(db=Depends(get_connection)):  # Use dependency injection to get the database connection
    return await user_controller.get_users(db)  # Call the controller method to get users

# Define an API endpoint to create a new user
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db=Depends(get_connection)):  # Use dependency injection for the database
    print(f"Creating user in main.py: {user}")  # Log the user creation attempt
    return await user_controller.create_user(user, db)  # Call the controller method to create a user

# Define an API endpoint to get a user by their email
@app.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.get_user_by_email(Email(email=email), db)  # Call the controller method to get user by email

# Define an API endpoint to get an OTP by email
@app.get("/users/otp/{email}", response_model=OtpResponse)
async def get_otp_by_email(email: str, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.get_otp_by_email(Email(email=email), db)  # Call the controller method to get OTP

# Define an API endpoint to verify a user by email and OTP
@app.post("/users/verify", response_model=UserResponse)
async def verify_user_by_email(verify_user: VerifyUser, db=Depends(get_connection)):  # Use dependency injection for the database
    return await user_controller.verify_user_by_email(verify_user, db)  # Call the controller method to verify user

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

# Run the application using Uvicorn server
if __name__ == "__main__":
    import uvicorn  # Import Uvicorn for running the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Start the server on host 0.0.0.0 and port 8000