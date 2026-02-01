# Bot Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (updated for Gemini 2.5 support)
RUN pip install --no-cache-dir \
    aiogram==3.4.1 \
    google-cloud-aiplatform>=1.50.0 \
    google-cloud-firestore>=2.14.0 \
    google-cloud-secret-manager>=2.18.1 \
    aiohttp==3.9.3 \
    Pillow==10.2.0 \
    pydantic-settings==2.1.0 \
    requests==2.31.0

# Copy bot code (only the bot folder from repo root)
COPY bot/ ./bot/

# Cloud Run expects PORT env variable
ENV PORT=8080

# Run the bot
CMD ["python", "-m", "bot.main"]
