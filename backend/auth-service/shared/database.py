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
            print("Connected to MongoDB")
        except ConnectionFailure:
            print("Could not connect to MongoDB")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    async def get_db(cls):
        if not cls.db:
            await cls.connect_db()
        return cls.db 