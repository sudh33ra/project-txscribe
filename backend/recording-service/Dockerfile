FROM python:3.9-slim-buster

WORKDIR /app

# Install only required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create storage directory
RUN mkdir -p storage && chmod 777 storage

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy only necessary files
COPY ./app ./app
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 