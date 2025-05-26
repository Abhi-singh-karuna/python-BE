from typing import Optional
from datetime import datetime
from model.user_model import StandardResponse, MetaInfo, ErrorInfo

def create_success_response(message: str, data: dict = None) -> StandardResponse:
    """Create a standardized success response"""
    return StandardResponse(
        success=True,
        message=message,
        data=data,
        meta={
            "timestamp": datetime.now(),
            "version": "1.0"
        }
    )

def create_error_response(code: str, message: str, details: str = None) -> StandardResponse:
    """Create a standardized error response"""
    return StandardResponse(
        success=False,
        message=message,
        error={
            "code": code,
            "message": message,
            "details": details
        },
        meta={
            "timestamp": datetime.now(),
            "version": "1.0"
        }
    ) 