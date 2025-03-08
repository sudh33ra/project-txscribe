from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
import httpx
import aiofiles
import os
from typing import Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meeting Minutes API Gateway")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
RECORDING_SERVICE = "http://recording-service:8000"
TRANSCRIPTION_SERVICE = "http://transcription-service:8000"
SUMMARIZATION_SERVICE = "http://summarization-service:8000"
AUTH_SERVICE = "http://auth-service:8000"

@app.post("/api/v1/projects")
async def create_project(
    project: Dict,
    authorization: str = Header(None)
) -> Dict:
    """
    Create a new project
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RECORDING_SERVICE}/projects",
                json=project,
                headers={"Authorization": authorization}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Recording service error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text
        )
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/projects/{project_id}/workspaces")
async def create_workspace(
    project_id: str,
    workspace: Dict,
    authorization: str = Header(None)
) -> Dict:
    """
    Create a new workspace in a project
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RECORDING_SERVICE}/projects/{project_id}/workspaces",
                json=workspace,
                headers={"Authorization": authorization}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Recording service error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text
        )
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/meetings/record")
async def start_recording(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    user_id: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
) -> Dict:
    """
    Handle file upload and forward to recording service
    """
    try:
        logger.info(f"Received file upload request: {file.filename}")
        logger.info(f"Request data: workspace_id={workspace_id}, user_id={user_id}, title={title}")
        
        async with httpx.AsyncClient() as client:
            # Create multipart form data
            files = {"file": (file.filename, await file.read(), file.content_type)}
            data = {
                "workspace_id": workspace_id,
                "user_id": user_id
            }
            
            if title:
                data["title"] = title
            if description:
                data["description"] = description

            logger.info(f"Forwarding request to recording service: {RECORDING_SERVICE}/upload")
            try:
                response = await client.post(
                    f"{RECORDING_SERVICE}/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Recording service error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=e.response.text
                )
            except httpx.RequestError as e:
                logger.error(f"Recording service connection error: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Recording service unavailable: {str(e)}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/meetings/transcribe/{meeting_id}")
async def transcribe_meeting(meeting_id: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TRANSCRIPTION_SERVICE}/transcribe/{meeting_id}"
        )
        return response.json()

@app.get("/api/v1/meetings/{meeting_id}/summary")
async def get_meeting_summary(meeting_id: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUMMARIZATION_SERVICE}/summary/{meeting_id}"
        )
        return response.json()

@app.get("/health")
async def health_check():
    """
    Check health of all dependent services
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:  # Increase timeout
            services = {
                "recording": RECORDING_SERVICE,
                "transcription": TRANSCRIPTION_SERVICE,
                "summarization": SUMMARIZATION_SERVICE,
                "auth": AUTH_SERVICE
            }
            
            status = {}
            for name, url in services.items():
                try:
                    response = await client.get(f"{url}/health")
                    status[name] = "healthy" if response.status_code == 200 else "unhealthy"
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {str(e)}")
                    status[name] = "unavailable"
            
            # Return 503 only if all services are unavailable
            if all(s == "unavailable" for s in status.values()):
                raise HTTPException(status_code=503, detail="All services unavailable")
                
            return status
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 