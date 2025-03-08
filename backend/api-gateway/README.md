# API Gateway Service

## Overview
The API Gateway serves as the single entry point for all client-side requests. It handles routing, request aggregation, and authentication verification.

## Architecture
- Port: 8000 (internal and external)
- Dependencies: All microservices
- Environment Variables: None required

## API Endpoints

### Projects & Workspaces
- `POST /api/v1/projects`
  - Creates a new project
  - Requires: name, owner_id
  - Optional: description

- `POST /api/v1/workspaces`
  - Creates a new workspace within a project
  - Requires: name, project_id
  - Optional: description

### Recordings
- `POST /api/v1/meetings/record`
  - Starts a new recording session
  - Requires: file (audio), workspace_id, user_id
  - Optional: title, description
  - Returns: recording details

### Transcription
- `POST /api/v1/meetings/transcribe/{meeting_id}`
  - Initiates transcription for a recorded meeting
  - Returns: transcription job status

### Summarization
- `GET /api/v1/meetings/{meeting_id}/summary`
  - Retrieves meeting summary
  - Returns: summarized content

### Health Check
- `GET /health`
  - Checks health of all dependent services
  - Returns: status of each service

## Error Handling
- 400: Bad Request - Invalid input
- 401: Unauthorized - Authentication required
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource doesn't exist
- 500: Internal Server Error
- 503: Service Unavailable - Dependent service unreachable 