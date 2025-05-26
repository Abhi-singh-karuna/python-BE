import redis.asyncio as redis
from pathlib import Path
from typing import Optional
from utils.logger import Logger
from config.config import load_config

logger = Logger(name="redis")

class RedisConnection:
    _instance: Optional[redis.Redis] = None
    _config = None

    @classmethod
    async def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            config = cls._load_config()
            redis_conf = config.redis.write
            cls._instance = redis.from_url(
                f"redis://:{redis_conf.password}@{redis_conf.host}:{redis_conf.port}/{redis_conf.database}"
            )
            logger.info("Redis connection established")
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")

    @classmethod
    def _load_config(cls):
        if cls._config is None:
            cls._config = load_config("config/config.yml")
        return cls._config

# Convenience function for FastAPI dependency injection
async def get_redis():
    redis = await RedisConnection.get_instance()
    try:
        yield redis
    finally:
        # Note: We don't close the connection here as it's a singleton
        pass 