from pydantic import BaseModel, ValidationError
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import status
from datetime import datetime
from typing import Any, Dict, List

#  Base model that forbids unexpected fields and can be extended for shared config.
class CustomBaseModel(BaseModel):
    class Config:
        extra = "forbid"
        allow_population_by_field_name = True
        orm_mode = True

#  Formats the list of validation errors into a consistent structure.
def format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Invalid input")
        }
        for err in errors
    ]

#  Converts a list of error dicts into a single error string message.
def format_error_message(errors: List[Dict[str, str]]) -> str:
    return "; ".join(f"{err['field']}: {err['message']}" for err in errors)

#  Custom exception handler for validation errors.
def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    formatted_errors = format_validation_errors(exc.errors())
    error_message = format_error_message(formatted_errors)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": error_message,
            # "errors": formatted_errors,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "path": str(request.url),
                "method": request.method,
            },
        },
    )
