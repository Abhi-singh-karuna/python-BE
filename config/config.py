from pydantic_settings import BaseSettings
from typing import Dict, Any
from functools import lru_cache
import yaml
import os
from pathlib import Path

class Settings(BaseSettings):
    """Base settings class for the application"""
    
    # Application settings
    APP_NAME: str = "Authentication API"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = "mysql+aiomysql://root:123456789@localhost:3306/auth_app"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_REFRESH_SECRET_KEY: str = "your-super-secret-jwt-refresh-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @classmethod
    @lru_cache()
    def get_settings(cls) -> "Settings":
        return cls()

    def get_redis_url(self) -> str:
        """Get Redis URL from settings"""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

class Config:
    """Configuration class for loading and accessing application settings"""
    
    def __init__(self):
        """Initialize configuration by loading from YAML file"""
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = 'config/config.yml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found
            
        Returns:
            Configuration value or default if not found
        """
        return self.config.get(key, default)

settings = Settings.get_settings() 