from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionModel(BaseModel):
    recording_id: ObjectId
    text: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "pending"
    segments: List[TranscriptionSegment] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TranscriptionService:
    def __init__(self, db):
        self.db = db
        self.collection = db.transcriptions

    async def create_transcription(self, transcription: TranscriptionModel):
        result = await self.collection.insert_one(transcription.dict())
        return str(result.inserted_id)

    async def update_transcription(self, transcription_id: str, update_data: dict):
        await self.collection.update_one(
            {"_id": ObjectId(transcription_id)},
            {
                "$set": {
                    **update_data,
                    "updated_at": datetime.utcnow()
                }
            }
        ) 