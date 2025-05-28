from fastapi import APIRouter, Depends
from typing import AsyncGenerator
from model.user_model import UserCreate, UserResponse
from model.auth import Token, TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from controller.auth_controller import AuthController
from controller.user_controller import UserController
from model.response_model import ApiResponse

def get_auth_router(auth_controller: AuthController, user_controller: UserController) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Authentication"])


    @router.post("/signup", response_model=ApiResponse) 
    async def signup(user: UserCreate):
        return await auth_controller.signup(user)

    @router.post("/login", response_model=ApiResponse)  # noqa
    async def login(token_data: TokenData):
        return await auth_controller.login(token_data)

    @router.post("/refresh", response_model=ApiResponse)  # noqa
    async def refresh_token(refresh_token: RefreshToken):
        return await auth_controller.refresh_token(refresh_token)

    @router.get("/user", response_model=UserResponse)  # noqa
    async def get_user(current_user: dict = Depends(auth_middleware)):
        return await user_controller.get_user(current_user)

    return router 