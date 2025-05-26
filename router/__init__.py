from fastapi import APIRouter
from .auth_router import get_auth_router

# Create main router
api_router = APIRouter()

# Note: The auth router is now included in main.py using dependency injection
# This prevents circular imports and provides better control over dependencies 