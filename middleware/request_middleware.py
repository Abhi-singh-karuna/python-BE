from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from utils.logger import request_id, user_id, endpoint, ip_address, Logger
from typing import Callable
import json
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = Logger(name="request_middleware")

class RequestMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0  # seconds
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        req_id = str(uuid.uuid4())
        request_id.set(req_id)
        
        # Set request context
        endpoint.set(request.url.path)
        ip_address.set(request.client.host if request.client else "unknown")
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    "Slow request detected",
                    duration=duration,
                    method=request.method,
                    path=request.url.path
                )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = req_id
            
            # Log request completion
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except RequestValidationError as e:
            # Handle validation errors
            logger.error(
                "Request validation failed",
                errors=e.errors(),
                method=request.method,
                path=request.url.path
            )
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "errors": e.errors(),
                    "request_id": req_id
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                "Request failed",
                error=str(e),
                method=request.method,
                path=request.url.path,
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": req_id
                }
            ) 