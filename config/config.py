from pydantic_settings import BaseSettings
from typing import Dict, Any
from functools import lru_cache
import yaml
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Activity App API"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/activity_app"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email settings
    SENDGRID_API_KEY: str = "your-sendgrid-api-key"
    SENDGRID_FROM_EMAIL: str = "your-email@example.com"
    SENDGRID_FROM_NAME: str = "Activity App"
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Web URL for email verification
    WEB_URL: str = "http://localhost:3000"
    
    # Language settings
    DEFAULT_LANGUAGE: str = "en"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @classmethod
    @lru_cache()
    def get_settings(cls) -> "Settings":
        return cls()

    def get_redis_url(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def load_messages(self) -> Dict[str, Any]:
        messages_file = f"config/messages/{self.DEFAULT_LANGUAGE}.yaml"
        if not os.path.exists(messages_file):
            messages_file = "config/messages/en.yaml"
        
        with open(messages_file, "r") as f:
            return yaml.safe_load(f)

class Config:
    def __init__(self):
        self.config = self.load_config()
        self.CurrentLanguage = self.config.get('CurrentLanguage', 'en')
        self.ApplicationMessages = self.config.get('ApplicationMessages', {})
        self.AccessTokenSecret = self.config.get('AccessTokenSecret')
        self.RefreshTokenSecret = self.config.get('RefreshTokenSecret')
        self.WebURL = self.config.get('WebURL')

    def load_config(self):
        config_path = 'config/config.yml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

settings = Settings.get_settings() 