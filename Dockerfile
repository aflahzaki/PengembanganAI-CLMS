# ============================================================
# Multi-stage Dockerfile for CLMS
# Stage 1: Build frontend static files
# Stage 2: Production backend with gunicorn + uvicorn workers
# ============================================================

# --- Stage 1: Frontend Build ---
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first for better caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production ---
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend static files from stage 1
COPY --from=frontend-build /app/frontend/build /app/frontend/build

# Create data directory for persistence
RUN mkdir -p /app/backend/data

# Expose port
EXPOSE 8000

# Run with gunicorn + uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
