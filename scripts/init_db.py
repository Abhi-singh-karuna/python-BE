import asyncio
import aiomysql
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from config.database import DB_CONFIG

async def init_db():
    # Create connection
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor() as cur:
        # Create users table
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                phone_no INT NOT NULL,
                otp VARCHAR(6),
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()
    
    # Close connection
    conn.close()
    await conn.wait_closed()

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db()) 