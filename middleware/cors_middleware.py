from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

class CORSMiddlewareConfig:
    """CORS middleware configuration class"""
    
    def __init__(
        self,
        allow_origins: List[str] = ["*"],
        allow_credentials: bool = True,
        allow_methods: List[str] = ["*"],
        allow_headers: List[str] = ["*"],
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600
    ):
        self.allow_origins = allow_origins
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.expose_headers = expose_headers
        self.max_age = max_age

    def get_middleware(self) -> dict:
        """Get CORS middleware configuration
        
        Returns:
            dict: Configuration parameters for CORSMiddleware
        """
        return {
            "allow_origins": self.allow_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
            "expose_headers": self.expose_headers,
            "max_age": self.max_age
        }

# Default CORS configuration
default_cors_config = CORSMiddlewareConfig() 