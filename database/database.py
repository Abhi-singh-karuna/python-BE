"""
database.py

This module provides a DatabaseConnection class that manages the connection pool
to a PostgreSQL database using asyncpg. It includes methods for loading configuration,
executing SQL files, and managing database connections in an asynchronous context.
"""

import asyncpg
from pathlib import Path
from typing import Optional
from utils.logger import Logger
from config.config import load_config
import re

logger = Logger(name="database")

class DatabaseConnection:
    # A class to manage the database connection pool.
    _pool: Optional[asyncpg.Pool] = None  # Single shared instance
    _config = None

    @classmethod
    def _load_config(cls):
        # Load the database configuration using the new config system
        if cls._config is None:
            cls._config = load_config("config/config.yml")
        return cls._config

    @classmethod
    def _load_sql_file(cls, filename: str) -> str:
        # Load an SQL file from the 'sql' directory.
        sql_path = Path(__file__).parent / 'sql' / filename
        with open(sql_path, 'r') as f:
            return f.read()

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        # Get the database connection pool, creating it if it doesn't exist.
        if cls._pool is None:
            config = cls._load_config()
            db_config = {
                'host': config.sql.write.host,
                'port': config.sql.write.port,
                'user': config.sql.write.user,
                'password': config.sql.write.password,
                'database': config.sql.write.database,
                'min_size': 1,
                'max_size': 10,
                'command_timeout': 60.0,
                'server_settings': {
                    'application_name': 'activity_app'
                }
            }
            try:
                cls._pool = await asyncpg.create_pool(**db_config)
                logger.info("Database connection pool created", pool_size=db_config['max_size'])
            except Exception as e:
                logger.error("Failed to create database pool", error=str(e))
                raise
        return cls._pool

    @classmethod
    async def close_pool(cls):
        # Close the database connection pool.
        if cls._pool is not None:
            await cls._pool.close()
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
    async def fetch(cls, query: str, *args):
        conn = await cls.get_connection()
        try:
            return await conn.fetch(query, *args)
        except Exception as e:
            logger.error("Fetch query failed", error=str(e), query=query)
            raise
        finally:
            await cls.release_connection(conn)

    @classmethod
    async def fetchrow(cls, query: str, *args):
        conn = await cls.get_connection()
        try:
            return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error("Fetchrow query failed", error=str(e), query=query)
            raise
        finally:
            await cls.release_connection(conn)

    @classmethod
    async def execute(cls, query: str, *args):
        conn = await cls.get_connection()
        try:
            return await conn.execute(query, *args)
        except Exception as e:
            logger.error("Execute query failed", error=str(e), query=query)
            raise
        finally:
            await cls.release_connection(conn)

    @classmethod
    async def init_db(cls):
        # Initialize the database schema by executing SQL files.
        conn = None
        try:
            conn = await cls.get_connection()
            async def execute_sql_file(filename: str, context: str, is_procedure=False):
                # Execute an SQL file, handling procedures and triggers if specified.
                sql = cls._load_sql_file(filename)
                if is_procedure:
                    # FIX: Only match CREATE ... $$ ... $$; blocks that start at the beginning of a line (ignoring comments and whitespace)
                    # This prevents comments and DROP statements from being included in the block, which caused syntax errors.
                    pattern = re.compile(r'(?im)^\s*(CREATE[\s\S]+?\$\$[\s\S]+?\$\$;)', re.MULTILINE)
                    blocks = pattern.findall(sql)
                    # Remove these blocks from the SQL string
                    sql_remaining = pattern.sub('', sql)
                    # Execute CREATE ... $$ ... $$; blocks
                    for block in blocks:
                        try:
                            logger.info(f"Executing block: {block}")  # Debug log
                            await conn.execute(block)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                raise
                            logger.warning(f"{context} already exists or failed: {str(e)}")
                    # Execute other statements (like DROP ...;)
                    statements = [stmt.strip() for stmt in sql_remaining.split(';') if stmt.strip()]
                    for statement in statements:
                        try:
                            logger.info(f"Executing statement: {statement}")  # Debug log
                            await conn.execute(statement)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                raise
                            logger.warning(f"{context} already exists or failed: {str(e)}")
                else:
                    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                    for statement in statements:
                        try:
                            await conn.execute(statement)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                raise
                            logger.warning(f"{context} already exists or failed: {str(e)}")

            # Create tables
            await execute_sql_file('init.sql', context="Table/Index")

            # Create procedures, functions, triggers
            await execute_sql_file('procedures.sql', context="Procedure/Function/Trigger", is_procedure=True)

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
