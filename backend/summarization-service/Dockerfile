FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create model cache directory
RUN mkdir -p /app/model_cache && chmod 777 /app/model_cache

# Install NumPy 1.x first to ensure compatibility
RUN pip install "numpy<2.0.0" --no-cache-dir

# Copy requirements and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Pre-download the model during build
COPY <<EOF /app/download_model.py
from transformers import pipeline
import os

os.environ["TRANSFORMERS_CACHE"] = "/app/model_cache"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "500"
os.environ["HF_ENDPOINT"] = "https://huggingface.co"

try:
    summarizer = pipeline(
        "summarization",
        model="sshleifer/distilbart-cnn-12-6",
        tokenizer="sshleifer/distilbart-cnn-12-6"
    )
except Exception as e:
    print(f"Failed to download model: {e}")
EOF

RUN python /app/download_model.py

# Copy application code
COPY ./app ./app
COPY main.py .

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app
ENV HF_HUB_DOWNLOAD_TIMEOUT=500
ENV HF_ENDPOINT=https://huggingface.co

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 