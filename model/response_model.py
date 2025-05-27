from typing import Optional
from datetime import datetime
from pydantic import Field
from model.schemas.base import CustomBaseModel

class ResponseMeta(CustomBaseModel):
    """Metadata for API responses"""
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field("1.0", description="API version")

class ResponseError(CustomBaseModel):
    """Error information for API responses"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")

class ApiResponse(CustomBaseModel):
    """Standard API response model"""
    success: bool = Field(..., description="Response success status")
    message: str = Field(..., description="Response message")
    data: Optional[dict] = Field(None, description="Response data")
    error: Optional[ResponseError] = Field(None, description="Error information")
    meta: ResponseMeta = Field(..., description="Response metadata")

def create_success_response(message: str, data: dict = None) -> ApiResponse:
    """Create a standardized success response"""
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        meta=ResponseMeta(
            timestamp=datetime.now(),
            version="1.0"
        )
    )

def create_error_response(code: str, message: str, details: str = None) -> ApiResponse:
    """Create a standardized error response"""
    return ApiResponse(
        success=False,
        message=message,
        error=ResponseError(
            code=code,
            message=message,
            details=details
        ),
        meta=ResponseMeta(
            timestamp=datetime.now(),
            version="1.0"
        )
    ) 