from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
from config import Config
from utils.logger import Logger
from repository.user_repository import UserRepository
from model.user_model import JwtCustomClaims, HeaderId

security = HTTPBearer()
config = Config()
logger = Logger()

AUTH_HEADER = "IDToken"
HEADER_ID = "HeaderId"

def parse_message(error_message: str) -> dict:
    return {"message": error_message}

async def auth_middleware(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
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
        request.state.user = claims
        return claims
    except JWTError:
        raise HTTPException(
            status_code=400,
            detail=config.ApplicationMessages[config.CurrentLanguage]["InvalidTokenError"]["Message"]
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