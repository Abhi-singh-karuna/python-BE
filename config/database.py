import aiomysql
import yaml
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from utils.logger import Logger

logger = Logger(name="database")

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

# Pool configuration
POOL_CONFIG = {
    'minsize': 1,
    'maxsize': 10,
    'pool_recycle': 3600,
    'echo': False
}

# Global pool
_pool: Optional[aiomysql.Pool] = None

async def get_pool() -> aiomysql.Pool:
    """Get or create the database connection pool"""
    global _pool
    if _pool is None:
        try:
            _pool = await aiomysql.create_pool(**DB_CONFIG, **POOL_CONFIG)
            logger.info("Database connection pool created", pool_size=POOL_CONFIG['maxsize'])
        except Exception as e:
            logger.error("Failed to create database pool", error=str(e))
            raise
    return _pool

async def close_pool():
    """Close the database connection pool"""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("Database connection pool closed")

async def get_connection():
    """
    Get a database connection from the pool.
    
    Returns:
        aiomysql.Connection: Database connection object
    """
    pool = await get_pool()
    try:
        conn = await pool.acquire()
        return conn
    except Exception as e:
        logger.error("Database connection error", error=str(e))
        raise

async def release_connection(conn):
    """
    Release a database connection back to the pool.
    
    Args:
        conn: Database connection to release
    """
    if conn:
        pool = await get_pool()
        await pool.release(conn)

async def init_db():
    """
    Initialize database tables.
    Creates the users table if it doesn't exist.
    """
    conn = None
    try:
        conn = await get_connection()
        async with conn.cursor() as cursor:
            # Create users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    phone_no VARCHAR(20),
                    is_verified BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            await conn.commit()
            logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database tables", error=str(e))
        raise
    finally:
        if conn:
            await release_connection(conn) 