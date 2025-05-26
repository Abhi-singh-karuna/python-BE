import aioredis
import yaml
from pathlib import Path

# Load configuration
def load_config():
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Create Redis connection
async def get_redis():
    redis = await aioredis.from_url(
        f"redis://{config['redis']['host']}:{config['redis']['port']}"
    )
    try:
        yield redis
    finally:
        await redis.close() 