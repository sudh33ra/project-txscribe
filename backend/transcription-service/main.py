from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import whisper
from typing import Dict
from shared.database import Database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Transcription Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()

# Load Whisper model at startup
model = whisper.load_model("base")

@app.post("/transcribe/{recording_id}")
async def transcribe_audio(recording_id: str) -> Dict:
    try:
        # TODO: Get audio file path from recording ID
        audio_path = f"storage/{recording_id}.m4a"
        
        # Transcribe audio
        result = model.transcribe(audio_path)
        
        return {
            "recording_id": recording_id,
            "text": result["text"],
            "language": result["language"],
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Check service and database health
    """
    try:
        # Check database connection
        db = await Database.get_db()
        # Don't check if db is None, just try to ping
        await db.command("ping")
        
        # Check if Whisper model is loaded
        if model is None:  # This is safe to check since model is a regular Python object
            raise Exception("Whisper model not loaded")
            
        return {
            "status": "healthy",
            "database": "connected",
            "model": "loaded"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        ) 