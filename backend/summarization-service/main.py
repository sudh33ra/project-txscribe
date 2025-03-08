from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from typing import Dict
from shared.database import Database
import logging
import warnings
import os

# Suppress huggingface warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Hugging Face cache and timeout
os.environ['TRANSFORMERS_CACHE'] = '/app/model_cache'
os.environ['HF_HOME'] = '/app/model_cache'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '500'

app = FastAPI(title="Summarization Service")

# Initialize models as None
summarizer = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    global summarizer
    try:
        # Connect to database
        await Database.connect_db()
        
        # Create cache directory
        os.makedirs('/app/model_cache', exist_ok=True)
        
        # Load models with offline mode if download fails
        logger.info("Loading summarization model...")
        try:
            # Use a smaller model by default
            summarizer = pipeline("summarization",
                                model="sshleifer/distilbart-cnn-12-6",
                                tokenizer="sshleifer/distilbart-cnn-12-6")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise e
            
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()

@app.post("/summarize")
async def generate_summary(text: str) -> Dict:
    try:
        if summarizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
            
        summary = summarizer(text, 
                           max_length=130,
                           min_length=30,
                           do_sample=False)[0]['summary_text']
        
        return {
            "summary": summary,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Check service and database health
    """
    try:
        # Check database connection
        db = await Database.get_db()
        await db.command("ping")
        
        # Check if model is loaded
        if summarizer is None:
            raise Exception("Model not loaded")
            
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