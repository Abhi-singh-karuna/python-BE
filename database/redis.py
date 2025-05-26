import redis.asyncio as redis
import yaml
from pathlib import Path
from typing import Optional
from utils.logger import Logger

logger = Logger(name="redis")

class RedisConnection:
    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            config = cls._load_config()
            cls._instance = redis.from_url(
                f"redis://{config['redis']['host']}:{config['redis']['port']}"
            )
            logger.info("Redis connection established")
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")

    @staticmethod
    def _load_config():
        config_path = Path("config/config.yml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

# Convenience function for FastAPI dependency injection
async def get_redis():
    redis = await RedisConnection.get_instance()
    try:
        yield redis
    finally:
        # Note: We don't close the connection here as it's a singleton
        pass 