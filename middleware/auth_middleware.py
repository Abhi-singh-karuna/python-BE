from fastapi import HTTPException, Request, Header
from jose import jwt, JWTError , ExpiredSignatureError
from typing import Optional
from config.config import load_config
from utils.logger import Logger
from repository.user_repository import UserRepository
from model.user_model import CurrentUser

config = load_config("config/config.yml")
logger = Logger(name="auth_middleware")

async def auth_middleware(request: Request) -> CurrentUser:
    """
    Middleware to authenticate requests using JWT tokens passed directly in the Authorization header (no Bearer prefix).
    """
    auth_header: Optional[str] = request.headers.get("Authorization")

    logger.info(f"Authorization Header: {auth_header}")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    token = auth_header.strip()  # token directly, no "Bearer" prefix

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        logger.info(f"Decoded JWT Payload: {payload}")

        current_user = CurrentUser(id=payload["sub"], email=payload["email"])
        request.state.user = current_user
        return current_user

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.TokenExpired.Message
        )
    except JWTError as e:
        logger.error(f"JWT decoding failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

async def auth_verified_middleware(
    request: Request,
    user_repo: UserRepository,
    authorization: Optional[str] = Header(None)
):
    """
    Middleware to authenticate and verify user using token (no 'Bearer' prefix).
    """
    logger.info(f"Incoming request for verification: {request.method} {request.url}")  # Log the request method and URL

    if not authorization:
        logger.warning("Authorization header is missing.")  # Log a warning if the header is missing
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    token = authorization.strip()

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        logger.info("JWT token decoded successfully for verification.")  # Log successful decoding of the token
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired during verification.")  # Log an error if the token has expired
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.TokenExpired.Message
        )
    except JWTError:
        logger.error("Invalid JWT token during verification.")  # Log an error for invalid token
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.error("User ID is missing in the token payload.")  # Log an error if user ID is missing
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.InvalidToken.Message
        )

    is_verified, user_details = await user_repo.validate_user_verified(user_id)
    if not is_verified:
        logger.warning(f"User with ID {user_id} is not verified.")  # Log a warning if the user is not verified
        raise HTTPException(
            status_code=401,
            detail=config.ApplicationMessages.en.UserNotVerified.Message
        )

    request.state.header_id = {
        "user_id": user_details.id,
        "user_email": user_details.email,
        "user_phone_no": user_details.phone_no
    }
    logger.info(f"User verified: {request.state.header_id}")  # Log the verified user details

    return request.state.header_id
