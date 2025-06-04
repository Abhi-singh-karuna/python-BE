from fastapi import APIRouter, Depends, Request
from model.user_model import UserCreate, CurrentUser
from model.auth import TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from controller.auth_controller import AuthController
from controller.user_controller import UserController , Email
from model.response.response_model import ApiResponse
from utils.ip import get_client_ip
from datetime import datetime

def get_auth_router(auth_controller: AuthController, user_controller: UserController) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Authentication"])

    @router.post("/signup", response_model=ApiResponse) 
    async def signup(user: UserCreate, request: Request):
        # Capture IP address and timestamp for terms acceptance
        client_ip = get_client_ip(request)
        user.ip_address = client_ip
        user.accepted_at = datetime.utcnow()
        
        return await auth_controller.signup(user)

    @router.post("/login", response_model=ApiResponse)  
    async def login(token_data: TokenData, request: Request):
        # You can also log IP for login attempts
        client_ip = get_client_ip(request)
        # Pass IP to controller if needed for logging/security
        return await auth_controller.login(token_data, client_ip=client_ip)

    @router.post("/refresh", response_model=ApiResponse)  
    async def refresh_token(refresh_token: RefreshToken, request: Request):
        client_ip = get_client_ip(request)
        return await auth_controller.refresh_token(refresh_token, client_ip=client_ip)

    @router.get("/user", response_model=ApiResponse)  
    async def get_user(current_user: CurrentUser = Depends(auth_middleware)):
        return await user_controller.get_user(current_user)
    
    @router.get("/users/email", response_model=ApiResponse)  
    async def get_user_by_email(email: Email):
        return await user_controller.get_user_by_email(email)
    
    @router.get("/terms-of-service", response_model=ApiResponse)  
    async def get_terms_of_service():
        return await user_controller.get_terms_of_service()
    
    return router 