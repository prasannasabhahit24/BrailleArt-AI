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

# Copy source code and files
COPY .gitignore .env.example README.md requirements.txt ./
COPY src/ ./src/

# Expose default ports:
# 8000: FastAPI Backend
# 8501: Streamlit Frontend
# 8012: FastMCP Server
EXPOSE 8000 8501 8012

# Default command runs the backend. This can be overridden at runtime.
# To run Streamlit: docker run -p 8501:8501 <image> streamlit run src/frontend/app.py
# To run FastMCP: docker run -p 8012:8012 <image> fastmcp run src/mcp/server.py
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
