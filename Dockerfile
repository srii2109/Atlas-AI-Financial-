# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose port for FastAPI
EXPOSE 8000

# Set environment variables
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV PORT=8000

# Start script to run both server and bot
CMD ["python", "run_all.py"]
