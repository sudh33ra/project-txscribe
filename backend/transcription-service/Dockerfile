FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Copy the app code
COPY ./app ./app
COPY main.py .

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 