from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class ActionItem(BaseModel):
    description: str
    assignee: str
    due_date: Optional[datetime] = None

class SummaryModel(BaseModel):
    transcription_id: ObjectId
    overview: Optional[str] = None
    key_points: List[str] = []
    action_items: List[ActionItem] = []
    decisions: List[str] = []
    next_steps: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SummaryService:
    def __init__(self, db):
        self.db = db
        self.collection = db.summaries

    async def create_summary(self, summary: SummaryModel):
        result = await self.collection.insert_one(summary.dict())
        return str(result.inserted_id)

    async def get_summary(self, summary_id: str):
        return await self.collection.find_one({"_id": ObjectId(summary_id)}) 