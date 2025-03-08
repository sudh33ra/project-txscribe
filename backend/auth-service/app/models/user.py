from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

# Custom type for handling MongoDB ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Base model for MongoDB documents
class MongoBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class UserModel(MongoBaseModel):
    email: EmailStr
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class UserService:
    def __init__(self, db):
        self.db = db
        self.collection = db.users

    async def create_user(self, user: UserModel):
        result = await self.collection.insert_one(user.dict())
        return str(result.inserted_id)

    async def get_user_by_email(self, email: str):
        return await self.collection.find_one({"email": email})

    async def update_user(self, email: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"email": email},
            {"$set": update_data}
        ) 