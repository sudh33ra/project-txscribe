# Transcription Service

## Overview
The Transcription Service converts audio recordings to text using OpenAI's Whisper model, supporting both English and Sinhala languages.

## Functionality

### Input
- Recording ID
- Audio file path (shared volume with recording-service)
- Language preferences (optional)

### Process
1. Loads audio file from storage
2. Detects audio language if not specified
3. Runs Whisper model for transcription
4. Translates to English if source is Sinhala
5. Saves transcription results

### Output
- Transcribed text
- Detected language
- Confidence scores
- Timestamps for each segment
- Translation (if applicable)

## API Endpoints

### Transcribe Audio
- `POST /transcribe/{recording_id}`
  - Processes audio file and returns transcription
  - Supports async processing for long files

### Get Transcription Status
- `GET /status/{job_id}`
  - Returns current status of transcription job

## Model Details
- Uses Whisper base model
- Supports multiple languages
- GPU acceleration enabled
- Batch processing capability

## Configuration
- Port: 8002
- GPU Requirements: NVIDIA GPU with CUDA support
- Model: Whisper base (configurable to other sizes) 