"""
database.py

This module provides a DatabaseConnection class that manages the connection pool
to a MySQL database using aiomysql. It includes methods for loading configuration,
executing SQL files, and managing database connections in an asynchronous context.
"""

import aiomysql
import yaml
from pathlib import Path
from typing import Optional
from utils.logger import Logger

logger = Logger(name="database")

class DatabaseConnection:
    # A class to manage the database connection pool.
    _pool: Optional[aiomysql.Pool] = None  # Single shared instance

    @classmethod
    def _load_config(cls):
        # Load the database configuration from a YAML file.
        config_path = Path("config/config.yml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @classmethod
    def _load_sql_file(cls, filename: str) -> str:
        # Load an SQL file from the 'sql' directory.
        sql_path = Path(__file__).parent / 'sql' / filename
        with open(sql_path, 'r') as f:
            return f.read()

    @classmethod
    async def get_pool(cls) -> aiomysql.Pool:
        # Get the database connection pool, creating it if it doesn't exist.
        if cls._pool is None:
            config = cls._load_config()
            db_config = {
                'host': config['sql']['write']['host'],
                'port': config['sql']['write']['port'],
                'user': config['sql']['write']['user'],
                'password': config['sql']['write']['password'],
                'db': config['sql']['write']['database'],
                'charset': 'utf8mb4',
                'autocommit': True
            }
            pool_config = {
                'minsize': 1,
                'maxsize': 10,
                'pool_recycle': 3600,
                'echo': False
            }
            try:
                cls._pool = await aiomysql.create_pool(**db_config, **pool_config)
                logger.info("Database connection pool created", pool_size=pool_config['maxsize'])
            except Exception as e:
                logger.error("Failed to create database pool", error=str(e))
                raise
        return cls._pool

    @classmethod
    async def close_pool(cls):
        # Close the database connection pool.
        if cls._pool is not None:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None
            logger.info("Database connection pool closed")

    @classmethod
    async def get_connection(cls):
        # Acquire a connection from the pool.
        pool = await cls.get_pool()
        try:
            conn = await pool.acquire()
            return conn
        except Exception as e:
            logger.error("Database connection error", error=str(e))
            raise

    @classmethod
    async def release_connection(cls, conn):
        # Release a connection back to the pool.
        if conn:
            pool = await cls.get_pool()
            await pool.release(conn)

    @classmethod
    async def init_db(cls):
        # Initialize the database schema by executing SQL files.
        conn = None
        try:
            conn = await cls.get_connection()
            async with conn.cursor() as cursor:
                async def execute_sql_file(filename: str, context: str, is_procedure=False):
                    # Execute an SQL file, handling procedures and triggers if specified.
                    sql = cls._load_sql_file(filename)
                    if is_procedure:
                        # This handles multi-line stored procedures and triggers
                        blocks = sql.split('DELIMITER ;')
                        for block in blocks:
                            statements = block.strip().split(';')
                            compound_statement = ""
                            for stmt in statements:
                                if stmt.strip():
                                    compound_statement += stmt.strip() + ";"
                            if compound_statement.strip():
                                try:
                                    await cursor.execute(compound_statement)
                                except Exception as e:
                                    if "already exists" not in str(e).lower():
                                        raise
                                    logger.warning(f"{context} already exists or failed: {str(e)}")
                    else:
                        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                        for statement in statements:
                            try:
                                await cursor.execute(statement)
                            except Exception as e:
                                if "already exists" not in str(e).lower():
                                    raise
                                logger.warning(f"{context} already exists or failed: {str(e)}")

                # Create tables
                await execute_sql_file('init.sql', context="Table/Index")

                # Create procedures, functions, triggers
                await execute_sql_file('procedures.sql', context="Procedure/Function/Trigger", is_procedure=True)

                await conn.commit()
                logger.info("Database tables and procedures initialized successfully.")

        except Exception as e:
            logger.error("Failed to initialize database schema", error=str(e))
            raise

        finally:
            if conn:
                await cls.release_connection(conn)

# For FastAPI dependency injection
async def get_db():
    # Dependency function for FastAPI to get a database connection.
    conn = await DatabaseConnection.get_connection()
    try:
        yield conn
    finally:
        await DatabaseConnection.release_connection(conn)
