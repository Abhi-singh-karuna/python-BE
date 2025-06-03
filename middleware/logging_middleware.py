from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message
from starlette.datastructures import Headers
from utils.logger import Logger, request_id, endpoint, ip_address
from utils.ip import get_client_ip
from typing import Callable, Awaitable, Optional, Union, List
import json
import uuid
import traceback


SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "authorization"}


def mask_sensitive_data(data: Union[dict, list], keys_to_mask: set = SENSITIVE_KEYS) -> Union[dict, list]:
    """Recursively mask sensitive fields in a dictionary or list."""
    if isinstance(data, dict):
        return {
            key: "***" if key.lower() in keys_to_mask else mask_sensitive_data(value, keys_to_mask)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, keys_to_mask) for item in data]
    else:
        return data


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = Logger(name="request_logger")

    async def set_body(self, request: Request, body: bytes):
        """Set the request body for downstream processing."""
        async def receive() -> Message:
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process the incoming request and log relevant information."""
        req_id = str(uuid.uuid4())
        request_id.set(req_id)
        endpoint.set(request.url.path)
        
        # Use the improved IP detection
        client_ip = get_client_ip(request)
        ip_address.set(client_ip)

        request_body: Optional[Union[dict, str]] = None
        raw_body: Optional[bytes] = None

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                raw_body = await request.body()
                await self.set_body(request, raw_body)
                parsed_body = json.loads(raw_body.decode("utf-8"))
                request_body = mask_sensitive_data(parsed_body)
            except json.JSONDecodeError:
                request_body = "Invalid JSON"
            except Exception as e:
                request_body = f"Error reading body: {str(e)}"
                self.logger.warning(
                    "Exception while reading request body",
                    error=str(e),
                    traceback=traceback.format_exc()
                )

        self.logger.info(
            "Incoming request",
            request_id=req_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            headers=dict(request.headers),
            request_body=request_body
        )

        try:
            response = await call_next(request)
        except Exception as e:
            self.logger.error(
                "Unhandled exception during request processing",
                request_id=req_id,
                error=str(e),
                traceback=traceback.format_exc()
            )
            raise

        return response
