# Use lightweight official Python image
FROM python:3.14-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security isolation
RUN groupadd -g 1000 aurix && \
    useradd -u 1000 -g aurix -s /bin/bash -m aurix

WORKDIR /app

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements specification
COPY requirements.txt .

# Install pinned Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy platform source code
COPY . .

# Secure ownership for non-root execution
RUN chown -R aurix:aurix /app
USER aurix

# Expose API runtime port
EXPOSE 8000

# Container liveness / readiness health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["sh", "-c", "curl -fsS http://localhost:${PORT:-8000}/api/v1/health || exit 1"]

# Production application entrypoint
CMD ["sh", "-c", "uvicorn aurix_api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
