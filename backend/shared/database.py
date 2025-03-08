from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
            cls.db = cls.client.meeting_minutes
            # Test the connection
            await cls.db.command("ping")
            print("Connected to MongoDB")
        except ConnectionFailure:
            print("Could not connect to MongoDB")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("MongoDB connection closed")

    @classmethod
    async def get_db(cls):
        if cls.db is None:
            await cls.connect_db()
        return cls.db 