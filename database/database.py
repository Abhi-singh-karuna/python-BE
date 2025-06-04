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
        sql_path = Path(__file__).parent / 'migration' / filename
        with open(sql_path, 'r') as f:
            return f.read()

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        # Get the database connection pool, creating it if it doesn't exist.
        if cls._pool is None:
            config = cls._load_config()
            db_config = {
                'host': config.general.sql.write.host,
                'port': int(config.general.sql.write.port),
                'user': config.general.sql.write.user,
                'password': config.general.sql.write.password,
                'database': config.general.sql.write.database,
                'min_size': 1,
                'max_size': 10,
                'command_timeout': 60.0,
                'server_settings': {
                    'application_name': 'police_app'
                }
            }
            try:
                cls._pool = await asyncpg.create_pool(**db_config)
                logger.info("Database connection pool created", pool_size=db_config['max_size'], host=db_config['host'], port=db_config['port'], user=db_config['user'], password=db_config['password'], database=db_config['database'])
            except Exception as e:
                # logger.error("Database connection pool creation failed varibale values" , db_config)
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
            record = await conn.fetchrow(query, *args)
            if record is None:
                return None
            return tuple(record.values())  # <-- returning a tuple
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

        async def split_sql_statements(sql: str, is_procedure: bool) -> list[str]:
            # Helper to split SQL script into executable statements
            if not is_procedure:
                return [stmt.strip() for stmt in sql.split(';') if stmt.strip()]

            statements = []
            current_stmt_lines = []
            in_dollar_quote = False

            for line in sql.splitlines():
                # Toggle dollar quote when $$ appears
                if '$$' in line:
                    in_dollar_quote = not in_dollar_quote
                current_stmt_lines.append(line)

                if not in_dollar_quote and ';' in line:
                    statements.append('\n'.join(current_stmt_lines).strip())
                    current_stmt_lines = []

            if current_stmt_lines:
                statements.append('\n'.join(current_stmt_lines).strip())

            return [stmt for stmt in statements if stmt]

        async def execute_sql_file(filename: str, context: str, is_procedure=False):
            sql = cls._load_sql_file(filename)
            statements = await split_sql_statements(sql, is_procedure)

            for stmt in statements:
                try:
                    # logger.info(f"Executing {context} statement...")
                    await conn.execute(stmt)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.error(f"Error executing statement in {context}: {e}")
                        raise
                    # logger.warning(f"{context} already exists or failed but ignored: {e}")

        try:
            conn = await cls.get_connection()

            logger.info("Initializing database tables.. init.sql ")
            # Execute schema creation scripts
            await execute_sql_file('init.sql', context="Table/Index")

            logger.info("Initializing database procedures.. procedures.sql ")
            # Execute procedures/functions/triggers
            await execute_sql_file('procedures.sql', context="Procedure/Function/Trigger", is_procedure=True)

            logger.info("Database tables(init.sql) and procedures(procedures.sql) initialized successfully.")

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
