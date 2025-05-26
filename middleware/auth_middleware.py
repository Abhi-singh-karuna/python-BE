from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
from config import Config
from utils.logger import Logger
from repository.user_repository import UserRepository
from model.user_model import UserResponse

security = HTTPBearer()
config = Config()
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
            detail="No token provided"
        )

    try:
        # Decode and verify the token
        payload = jwt.decode(
            token,
            config.get("JWT_SECRET_KEY"),
            algorithms=[config.get("JWT_ALGORITHM")]
        )
        
        # Add user info to request state
        request.state.user = {
            "id": payload["id"],
            "email": payload["email"]
        }
        
        return request.state.user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
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
            detail=config.ApplicationMessages[config.CurrentLanguage]["EmptyTokenError"]["Message"]
        )

    try:
        claims = JwtCustomClaims()
        payload = jwt.decode(
            token,
            config.AccessTokenSecret,
            algorithms=["HS256"]
        )
        claims.__dict__.update(payload)
    except JWTError as e:
        if isinstance(e, jwt.ExpiredSignatureError):
            raise HTTPException(
                status_code=401,
                detail=config.ApplicationMessages[config.CurrentLanguage]["ExpireTokenError"]["Message"]
            )
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages[config.CurrentLanguage]["InvalidTokenError"]["Message"]
        )

    user_id = claims.id
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages[config.CurrentLanguage]["UserIdEmptyError"]["Message"]
        )

    is_verified, user_details = await user_repo.validate_user_verified(user_id)
    if not is_verified:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages[config.CurrentLanguage]["UserNotVerified"]["Message"]
        )

    request.state.header_id = HeaderId(
        user_id=user_details.id,
        user_email=user_details.email,
        user_phone_no=user_details.email
    )
    return request.state.header_id 