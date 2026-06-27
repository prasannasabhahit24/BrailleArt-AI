# ==============================================================================
# BrailleArt AI - Production-Ready Dockerfile
# ==============================================================================
# Use official slim Python image as base
FROM python:3.11-slim AS builder

# Set build-time variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies needed for compiling some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -r requirements.txt


# Final stage
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy source code, configurations, launcher
COPY .gitignore .env.example README.md requirements.txt entrypoint.sh ./
COPY src/ ./src/

# Ensure launcher script is executable and create non-root user for security
RUN chmod +x entrypoint.sh && \
    useradd -u 10001 --create-home appuser && \
    chown -R appuser:appuser /app

# Switch to non-root security context
USER appuser

# Expose default ports:
# 8000: FastAPI Backend
# 8501: Streamlit Frontend
# 8012: FastMCP Server
EXPOSE 8000 8501 8012

# Use entrypoint script to support multi-role startup configurations
ENTRYPOINT ["/app/entrypoint.sh"]
