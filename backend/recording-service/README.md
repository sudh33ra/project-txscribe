# Recording Service

## Overview
The Recording Service handles audio file uploads and storage management for meeting recordings. It also manages projects and workspaces organization.

## Architecture
- Port: 8000 (internal), 8001 (external)
- Storage: Docker volume (recording_data)
- Database: MongoDB

## Data Models

### Project
- name (required)
- owner_id (required)
- description (optional)
- created_at, updated_at

### Workspace
- name (required)
- project_id (required)
- description (optional)
- created_at, updated_at

### Recording
- workspace_id (required)
- user_id (required)
- filename (required)
- title (optional)
- description (optional)
- duration (optional)
- file_path (required)
- status (required)
- created_at, updated_at

## API Endpoints

### Projects
- `POST /projects/`
  - Creates new project
  - Requires: name, owner_id
  - Optional: description

### Workspaces
- `POST /workspaces/`
  - Creates new workspace
  - Requires: name, project_id
  - Optional: description

### Recordings
- `POST /upload`
  - Uploads new recording
  - Requires: file, workspace_id, user_id
  - Optional: title, description

### Health Check
- `GET /health`
  - Checks service and database health

## Storage
- Mount Point: /app/storage
- File Format: m4a
- Naming: {timestamp}_{uuid}.m4a

## Configuration
- MONGODB_URI: MongoDB connection string
- Max File Size: 100MB (configurable) 