from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
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

class ProjectModel(MongoBaseModel):
    name: str
    owner_id: PyObjectId
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class WorkspaceModel(MongoBaseModel):
    name: str
    project_id: PyObjectId
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class RecordingModel(MongoBaseModel):
    workspace_id: PyObjectId
    user_id: PyObjectId
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    duration: float = 0.0
    file_path: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "status": "pending"
            }
        }

class ProjectService:
    def __init__(self, db):
        self.db = db
        self.collection = db["projects"]

    async def create_project(self, project: ProjectModel):
        result = await self.collection.insert_one(project.dict())
        return result.inserted_id

    async def get_user_projects(self, user_id: str):
        cursor = self.collection.find({"owner_id": ObjectId(user_id)})
        return await cursor.to_list(length=None)

class WorkspaceService:
    def __init__(self, db):
        self.db = db
        self.collection = db["workspaces"]

    async def create_workspace(self, workspace: WorkspaceModel):
        result = await self.collection.insert_one(workspace.dict())
        return str(result.inserted_id)

    async def get_project_workspaces(self, project_id: str):
        cursor = self.collection.find({"project_id": ObjectId(project_id)})
        return await cursor.to_list(length=None)

    async def get_workspace(self, workspace_id: str):
        """Get a workspace by ID"""
        try:
            if not ObjectId.is_valid(workspace_id):
                return None
            return await self.collection.find_one({"_id": ObjectId(workspace_id)})
        except Exception as e:
            logger.error(f"Error getting workspace: {str(e)}")
            return None

    async def workspace_exists(self, workspace_id: str) -> bool:
        """Check if a workspace exists"""
        try:
            if not ObjectId.is_valid(workspace_id):
                return False
            workspace = await self.get_workspace(workspace_id)
            return workspace is not None
        except Exception as e:
            logger.error(f"Error checking workspace existence: {str(e)}")
            return False

class RecordingService:
    def __init__(self, db):
        self.db = db
        self.collection = db.recordings

    async def create_recording(self, recording: RecordingModel):
        result = await self.collection.insert_one(recording.dict())
        return str(result.inserted_id)

    async def get_workspace_recordings(self, workspace_id: str):
        cursor = self.collection.find({"workspace_id": ObjectId(workspace_id)})
        return await cursor.to_list(length=None)

    async def get_recording(self, recording_id: str):
        return await self.collection.find_one({"_id": ObjectId(recording_id)})

    async def update_recording(self, recording_id: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(recording_id)},
            {"$set": update_data}
        ) 