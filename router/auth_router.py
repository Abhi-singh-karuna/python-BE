from fastapi import APIRouter, Depends
from typing import AsyncGenerator
from model.user_model import UserCreate, UserResponse, StandardResponse
from model.auth import Token, TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from database import DatabaseConnection
from controller.auth_controller import AuthController
from controller.user_controller import UserController

def get_auth_router(auth_controller: AuthController, user_controller: UserController) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Authentication"])

    # Database dependency
    async def get_db() -> AsyncGenerator:
        """Database dependency that handles connection lifecycle"""
        conn = await DatabaseConnection.get_connection()
        try:
            yield conn
        finally:
            await DatabaseConnection.release_connection(conn)

    @router.post("/signup", response_model=StandardResponse)  # noqa
    async def signup(user: UserCreate, db=Depends(get_db)):
        return await auth_controller.signup(user, db)

    @router.post("/login", response_model=StandardResponse)  # noqa
    async def login(token_data: TokenData, db=Depends(get_db)):
        return await auth_controller.login(token_data, db)

    @router.post("/refresh", response_model=StandardResponse)  # noqa
    async def refresh_token(refresh_token: RefreshToken, db=Depends(get_db)):
        return await auth_controller.refresh_token(refresh_token, db)

    @router.get("/user", response_model=UserResponse)  # noqa
    async def get_user(db=Depends(get_db), current_user: dict = Depends(auth_middleware)):
        return await user_controller.get_user(db, current_user)

    return router 