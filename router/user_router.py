from fastapi import APIRouter, Depends, Request, HTTPException
from model.user_model import UserCreate, CurrentUser
from model.user_model import TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from controller.user_controller import UserController , Email
from utils.ip import get_client_ip
from model.response.response_model import ApiResponse

def get_user_router(user_controller: UserController) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["User"])

    @router.get("/healthz")
    async def health_check():
        return await user_controller.check_health()
        
    @router.post("/signup", response_model=ApiResponse) 
    async def signup(user: UserCreate, request: Request):
        user.ip_address = get_client_ip(request)
        return await user_controller.signup(user)

    @router.post("/login", response_model=ApiResponse)  
    async def login(token_data: TokenData):
        return await user_controller.login(token_data)

    @router.post("/refresh", response_model=ApiResponse)  
    async def refresh_token(refresh_token: RefreshToken):
        return await user_controller.refresh_token(refresh_token)

    @router.get("/user", response_model=ApiResponse)  
    async def get_user(current_user: CurrentUser = Depends(auth_middleware)):
        return await user_controller.get_user(current_user)
    
    @router.get("/users/email", response_model=ApiResponse)  
    async def get_user_by_email(email: Email):
        return await user_controller.get_user_by_email(email)
    
    @router.get("/terms-of-service", response_model=ApiResponse)  
    async def get_terms_of_service():
        return await user_controller.get_terms_of_service()
    
    @router.post("/verify-user", response_model=ApiResponse)
    async def verify_user(user: UserCreate):
        return await user_controller.verify_user(user)
    
    return router 