from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)

db = client["chatBot"]

async def check_database_connection():
    try:
        await client.admin.command('ping')
        return {"status": "connected", "message": "Database connected successfully!", "database": "chatBot"}
    except Exception as e:
        return {"status": "disconnected", "message": f"Database connection failed: {str(e)}", "database": "chatBot"}