from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import uuid
from datetime import datetime
from shared.database import Database
from app.models.recording import RecordingModel, RecordingService, ProjectModel, WorkspaceModel, ProjectService, WorkspaceService
from bson import ObjectId
import logging
from typing import Optional, Dict
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Recording Service")

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

@app.post("/projects")
async def create_project(
    project: Dict = Body(...),
    authorization: str = Header(None)
) -> Dict:
    """Create a new project"""
    try:
        db = await Database.get_db()
        project_service = ProjectService(db)
        
        # Validate owner_id
        if not ObjectId.is_valid(project["owner_id"]):
            raise HTTPException(status_code=422, detail="Invalid owner_id format")
            
        # Create project model from request data
        project_model = ProjectModel(
            name=project["name"],
            owner_id=ObjectId(project["owner_id"]),
            description=project.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        project_id = await project_service.create_project(project_model)
        return {"project_id": str(project_id)}
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/workspaces")
async def create_workspace(
    project_id: str,
    workspace: Dict = Body(...),  # Changed to use Body for proper JSON parsing
    authorization: str = Header(None)
) -> Dict:
    """Create a new workspace in a project"""
    try:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=422, detail="Invalid project_id format")
            
        db = await Database.get_db()
        workspace_service = WorkspaceService(db)
        
        # Create workspace model from request data
        workspace_model = WorkspaceModel(
            name=workspace["name"],
            project_id=ObjectId(project_id),
            description=workspace.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        workspace_id = await workspace_service.create_workspace(workspace_model)
        return {"workspace_id": str(workspace_id)}
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_recording(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    user_id: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Handle file upload and create recording entry"""
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Validate IDs
        if not ObjectId.is_valid(workspace_id):
            raise HTTPException(status_code=422, detail="Invalid workspace_id format")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=422, detail="Invalid user_id format")
            
        # Verify workspace exists
        db = await Database.get_db()
        workspace_service = WorkspaceService(db)
        workspace = await workspace_service.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Generate unique filename
        recording_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{recording_id}.m4a"
        
        # Save file
        file_path = f"storage/{filename}"
        logger.info(f"Saving file to: {file_path}")
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Create recording entry in MongoDB
        logger.info("Creating database entry")
        recording_service = RecordingService(db)
        recording = RecordingModel(
            workspace_id=ObjectId(workspace_id),
            user_id=ObjectId(user_id),
            filename=filename,
            title=title or file.filename,
            description=description,
            file_path=file_path,
            duration=0.0,
            status="pending"
        )
        
        recording_id = await recording_service.create_recording(recording)
        logger.info(f"Recording created with ID: {recording_id}")
        
        return {
            "recording_id": str(recording_id),
            "filename": filename,
            "status": "pending"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Check service and database health
    """
    try:
        # Check database connection
        db = await Database.get_db()
        if db is None:
            raise Exception("Database connection not established")
            
        # Test database connection
        await db.command("ping")
        
        # Check storage directory exists and is writable
        storage_path = "storage"
        if not os.path.exists(storage_path):
            raise Exception("Storage directory not found")
        if not os.access(storage_path, os.W_OK):
            raise Exception("Storage directory not writable")
            
        return {
            "status": "healthy",
            "database": "connected",
            "storage": "accessible"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        ) 