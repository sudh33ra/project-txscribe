# Summarization Service

## Overview
The Summarization Service generates structured meeting minutes from transcribed text using T5 model.

## Functionality

### Input
- Transcribed text
- Meeting metadata (optional)
- Summary format preferences

### Process
1. Preprocesses transcribed text
2. Segments long text if needed
3. Generates summary using T5 model
4. Structures output in meeting minutes format
5. Applies formatting and templates

### Output
- Structured meeting minutes including:
  - Meeting overview
  - Key points
  - Action items
  - Decisions made
  - Next steps

## API Endpoints

### Generate Summary
- `POST /summarize`
  - Accepts transcribed text
  - Returns formatted meeting minutes

### Get Templates
- `GET /templates`
  - Returns available summary templates

## Model Details
- Uses T5-small model
- Customizable output length
- Template-based formatting
- Fine-tuning capability for specific domains

## Configuration
- Port: 8003
- GPU Requirements: NVIDIA GPU with CUDA support
- Model: T5-small (configurable) 