FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install packages with mirror
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 1000 --retries 10 "pip>=23.0.1" && \
    pip install --no-cache-dir --timeout 1000 --retries 10 \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copy application code
COPY ./app ./app
COPY main.py .

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]