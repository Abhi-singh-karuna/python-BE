from fastapi import APIRouter, Depends, Request
from model.user_model import UserCreate, CurrentUser, TokenData, RefreshToken
from middleware.auth_middleware import auth_middleware
from controller.user_controller import UserController, Email
from utils.ip import get_client_ip
from model.response.response_model import ApiResponse

def get_user_routers(user_controller: UserController):

    # Health check router
    common_router = APIRouter(prefix="", tags=["Common"])

    @common_router.get("/healthz")
    async def health_check():
        return await user_controller.check_health()

    @common_router.get("/terms-of-service", response_model=ApiResponse)
    async def get_terms_of_service():
        return await user_controller.get_terms_of_service()

    # Router for /auth
    auth_router = APIRouter(prefix="/auth", tags=["Auth"])

    @auth_router.post("/signup", response_model=ApiResponse)
    async def signup(user: UserCreate, request: Request):
        user.ip_address = get_client_ip(request)
        return await user_controller.signup(user)

    # @auth_router.post("/login", response_model=ApiResponse)
    # async def login(token_data: TokenData):
    #     return await user_controller.login(token_data)

    # @auth_router.post("/refresh", response_model=ApiResponse)
    # async def refresh_token(refresh_token: RefreshToken):
    #     return await user_controller.refresh_token(refresh_token)

    # @auth_router.post("/verify-user", response_model=ApiResponse)
    # async def verify_user(user: UserCreate):
    #     return await user_controller.verify_user(user)

    # Router for /user
    user_router = APIRouter(prefix="/user", tags=["User"])

    # @user_router.get("/", response_model=ApiResponse)
    # async def get_user(current_user: CurrentUser = Depends(auth_middleware)):
    #     return await user_controller.get_user(current_user)

    @user_router.get("/email", response_model=ApiResponse)
    async def get_user_by_email(email: Email):
        return await user_controller.get_user_by_email(email)


    return [common_router, auth_router, user_router]
