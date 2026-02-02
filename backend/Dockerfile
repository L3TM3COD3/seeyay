# Backend API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.2 \
    uvicorn[standard]==0.27.1 \
    pydantic==2.6.1 \
    pydantic-settings==2.1.0 \
    google-cloud-firestore==2.14.0 \
    google-cloud-secret-manager==2.18.1 \
    httpx==0.26.0 \
    python-multipart==0.0.9 \
    aiohttp==3.9.3

# Copy backend code (only the backend folder from repo root)
COPY backend/ ./backend/

# Cloud Run expects PORT env variable
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the API server - use shell form to expand $PORT
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
