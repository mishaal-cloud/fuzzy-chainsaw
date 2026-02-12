FROM python:3.12-slim

WORKDIR /app

# System dependencies for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY due_diligence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY due_diligence/ due_diligence/

# Create data directory for SQLite (mount a volume here in production)
RUN mkdir -p /data
ENV DD_DATABASE_PATH=/data/due_diligence.db

# Cloud Run sets PORT env var (default 8080)
ENV PORT=8080

EXPOSE ${PORT}

# Use exec form so signals propagate correctly
CMD uvicorn due_diligence.api.server:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --timeout-keep-alive 600
