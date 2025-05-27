from pydantic import BaseModel, ValidationError, Field
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from datetime import datetime
from typing import Any, Dict, List, Union


class CustomBaseModel(BaseModel):
    """
    Base model that forbids unexpected fields and can be extended for shared config.
    """
    class Config:
        extra = "forbid"
        allow_population_by_field_name = True  # optional: allows using alias names
        orm_mode = True  # helpful if working with ORM objects like SQLAlchemy


def format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Formats the list of validation errors into a consistent structure.
    """
    return [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Invalid input")
        }
        for err in errors
    ]


def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Custom exception handler for validation errors.
    """
    formatted_errors = format_validation_errors(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "errors": formatted_errors,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "path": str(request.url),
                "method": request.method,
            },
        },
    )
