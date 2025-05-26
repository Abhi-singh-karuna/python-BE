from fastapi import APIRouter, Depends
from model.user_model import UserCreate, UserResponse
from model.auth import Token, TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from typing import AsyncGenerator
from config.database import get_connection, release_connection

# Create router instance
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database dependency
async def get_db() -> AsyncGenerator:
    """Database dependency that handles connection lifecycle"""
    conn = None
    try:
        conn = await get_connection()
        yield conn
    finally:
        if conn:
            await release_connection(conn)

# Auth routes
@router.post("/signup", response_model=Token)
async def signup(user: UserCreate, db=Depends(get_db)):
    """Handle user signup"""
    from main import user_controller  # Import here to avoid circular imports
    return await user_controller.signup(user, db)

@router.post("/login", response_model=Token)
async def login(token_data: TokenData, db=Depends(get_db)):
    """Handle user login"""
    from main import user_controller
    return await user_controller.login(token_data, db)

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: RefreshToken, db=Depends(get_db)):
    """Handle token refresh"""
    from main import user_controller
    return await user_controller.refresh_token(refresh_token, db)

@router.get("/user", response_model=UserResponse)
async def get_user(db=Depends(get_db),current_user: dict = Depends(auth_middleware)
):
    """Get current user information"""
    from main import user_controller
    return await user_controller.get_user(db, current_user) 