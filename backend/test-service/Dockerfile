FROM python:3.9-slim-buster

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy only necessary files
COPY main.py wait-for-services.sh ./
RUN chmod +x wait-for-services.sh

CMD ["./wait-for-services.sh"] 