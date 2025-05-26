import asyncio
import aiomysql
import sys
from pathlib import Path
from database import DatabaseConnection

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Replace DB_CONFIG with DatabaseConnection configuration
config = DatabaseConnection._load_config()
DB_CONFIG = {
    'host': config['sql']['write']['host'],
    'port': config['sql']['write']['port'],
    'user': config['sql']['write']['user'],
    'password': config['sql']['write']['password'],
    'db': config['sql']['write']['database'],
    'charset': 'utf8mb4',
    'autocommit': True
}

async def init_db():
    # Create connection
    conn = await aiomysql.connect(**DB_CONFIG)
    try:
        async with conn.cursor() as cur:
            # Execute SQL from init.sql file
            sql = DatabaseConnection._load_sql_file('init.sql')
            for statement in sql.split(';'):
                if statement.strip():
                    await cur.execute(statement)
            await conn.commit()
            print("Database tables initialized successfully")
    finally:
        # Close connection
        conn.close()
        await conn.wait_closed()

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db()) 