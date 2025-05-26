from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
from config.config import load_config
from utils.logger import Logger
from repository.user_repository import UserRepository
from model.user_model import UserResponse

security = HTTPBearer()
config = load_config("config/config.yml")
logger = Logger(name="auth_middleware")

async def auth_middleware(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Middleware to authenticate requests using JWT tokens.
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials containing the JWT token
        
    Returns:
        Dictionary containing user information from the token
        
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    try:
        # Decode and verify the token
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        
        # Add user info to request state
        request.state.user = {
            "id": payload["sub"],
            "email": payload["email"]
        }
        
        return request.state.user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.TokenExpired.Message
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

async def auth_verified_middleware(
    request: Request,
    user_repo: UserRepository,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=400,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
    except JWTError as e:
        if isinstance(e, jwt.ExpiredSignatureError):
            raise HTTPException(
                status_code=401,
                detail=config.ApplicationMessages.en.TokenExpired.Message
            )
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    is_verified, user_details = await user_repo.validate_user_verified(user_id)
    if not is_verified:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.UserNotVerified.Message
        )

    request.state.header_id = {
        "user_id": user_details.id,
        "user_email": user_details.email,
        "user_phone_no": user_details.phone_no
    }
    return request.state.header_id 