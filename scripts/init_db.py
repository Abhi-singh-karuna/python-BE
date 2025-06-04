import asyncio
import asyncpg
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from database.psql_connection import DatabaseConnection

# Replace DB_CONFIG with DatabaseConnection configuration
config = DatabaseConnection._load_config()
DB_CONFIG = {
    'host': config.general.sql.write.host,
    'port': config.general.sql.write.port,
    'user': config.general.sql.write.user,
    'password': config.general.sql.write.password,
    'database': config.general.sql.write.database
}

async def init_db():
    # Create connection
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Execute SQL from init.sql file
        sql = DatabaseConnection._load_sql_file('init.sql')
        for statement in sql.split(';'):
            if statement.strip():
                await conn.execute(statement)
        print("Database tables initialized successfully")
    finally:
        # Close connection
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_db()) 