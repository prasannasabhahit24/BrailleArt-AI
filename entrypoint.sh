#!/bin/bash
# ==============================================================================
# BrailleArt AI - Multi-Role Container Entrypoint
# ==============================================================================
set -e

# Default SERVICE_TYPE to backend if not specified
SERVICE_TYPE="${SERVICE_TYPE:-backend}"

echo "=============================================================================="
echo "Starting BrailleArt AI Service: $SERVICE_TYPE"
echo "=============================================================================="

if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "Launching FastAPI Backend..."
    exec uvicorn src.backend.main:app --host 0.0.0.0 --port 8000

elif [ "$SERVICE_TYPE" = "frontend" ]; then
    echo "Launching Streamlit Frontend..."
    exec streamlit run src/frontend/app.py --server.address 0.0.0.0 --server.port 8501

elif [ "$SERVICE_TYPE" = "mcp" ]; then
    echo "Launching Model Context Protocol (FastMCP) Server..."
    exec fastmcp run src/mcp/server.py --host 0.0.0.0 --port 8012

elif [ "$SERVICE_TYPE" = "all" ]; then
    echo "Launching FastAPI Backend in the background..."
    uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 &
    
    # Give the backend a brief moment to boot up
    sleep 3
    
    echo "Launching Streamlit Frontend in the foreground..."
    exec streamlit run src/frontend/app.py --server.address 0.0.0.0 --server.port 8501

else
    echo "ERROR: Unknown SERVICE_TYPE '$SERVICE_TYPE'"
    echo "Valid values: 'backend', 'frontend', 'mcp', 'all'"
    exit 1
fi
