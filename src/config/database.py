from motor.motor_asyncio import AsyncIOMotorClient
from src.models.config import ConfigDB
from tenacity import retry, stop_after_attempt, wait_exponential

class DatabaseError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def init_db():
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        await client.server_info()  # Test connection
        db = client[settings.DB_NAME]
        
        # Create indexes
        await db.config.create_index([("_id", 1)], unique=True)
        
        # Initialize default config
        if not await db.config.find_one({"_id": "llm_settings"}):
            await db.config.insert_one({
                "_id": "llm_settings",
                "deepseek": {"enabled": True},
                "gemini": {"enabled": False},
                "openai": {"enabled": False}
            })
        
        return ConfigDB(client)
    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {str(e)}") 