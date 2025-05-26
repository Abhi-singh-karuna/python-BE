import aiomysql
import yaml
from pathlib import Path

# Load configuration
def load_config():
    config_path = 'config/config.yml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Database configuration
DB_CONFIG = {
    'host': config['sql']['write']['host'],
    'port': config['sql']['write']['port'],
    'user': config['sql']['write']['user'],
    'password': config['sql']['write']['password'],
    'db': config['sql']['write']['database'],
    'charset': 'utf8mb4',
    'autocommit': True
}

async def get_connection():
    return await aiomysql.connect(**DB_CONFIG)

async def init_db():
    """Initialize database tables"""
    conn = await get_connection()
    try:
        async with conn.cursor() as cursor:
            # Create users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    phone_no VARCHAR(20),
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)

            # Create otps table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS otps (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    created_at DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL
                )
            """)

            await conn.commit()
    finally:
        conn.close() 