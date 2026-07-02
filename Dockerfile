# ===========================================================================
# Dockerfile — Job Pipeline API
# Multi-stage build: slim runtime image with no dev dependencies.
# ===========================================================================

# --- Stage 1: Builder ------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time OS dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="pipeline-team"
LABEL description="Headless FastAPI job-application pipeline API"

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Ensure the appuser owns the working directory to write scheduler database and local states
RUN chown -R appuser:appuser /app

# Ensure Python can find the app package
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root
USER appuser


EXPOSE 8000

# Default command: run the API with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
