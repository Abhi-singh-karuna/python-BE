from fastapi import APIRouter
from .auth_routes import router as auth_router

# Create main router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router) 