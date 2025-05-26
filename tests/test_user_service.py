import pytest
from unittest.mock import Mock, AsyncMock
from service.user_service import UserInteractor, UserNotFoundError, InvalidCredentialsError
from model.user_model import UserCreate, UserResponse
from datetime import datetime

@pytest.fixture
def mock_user_repo():
    return Mock()

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_config():
    return Mock()

@pytest.fixture
def mock_email_service():
    return Mock()

@pytest.fixture
def user_service(mock_user_repo, mock_logger, mock_config, mock_email_service):
    return UserInteractor(
        user_repo=mock_user_repo,
        logger=mock_logger,
        config=mock_config,
        email_service=mock_email_service
    )

@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_user_repo):
    # Arrange
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
        phone_no=1234567890
    )
    
    mock_user_repo.create_user = AsyncMock(return_value=UserResponse(
        id="1",
        name=user_data.name,
        email=user_data.email,
        phone_no=user_data.phone_no,
        is_verified=False
    ))
    
    # Act
    result = await user_service.create_user(user_data, None)
    
    # Assert
    assert result is not None
    assert result.name == user_data.name
    assert result.email == user_data.email
    assert result.phone_no == user_data.phone_no
    assert not result.is_verified

@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service, mock_user_repo):
    # Arrange
    email = "nonexistent@example.com"
    mock_user_repo.get_user_by_email = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(UserNotFoundError):
        await user_service.get_user_by_email(email)

@pytest.mark.asyncio
async def test_login_invalid_credentials(user_service, mock_user_repo):
    # Arrange
    email = "test@example.com"
    password = "wrongpassword"
    mock_user_repo.get_user_by_email = AsyncMock(return_value=UserResponse(
        id="1",
        name="Test User",
        email=email,
        phone_no=1234567890,
        is_verified=True
    ))
    
    # Act & Assert
    with pytest.raises(InvalidCredentialsError):
        await user_service.login_for_access_token(email, password, None) 