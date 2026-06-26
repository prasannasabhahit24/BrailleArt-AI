"""
main.py

FastAPI Application entrypoint.
Responsible for:
1. Configuring app instance and documentation routes.
2. Initializing CORS, database connections, and logging.
3. Mounting API routers for agent operations.
4. Setting up startup/shutdown lifecycle events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import router and db setup
from .router import api_router
from ..database.db import engine, Base
from ..database import models

# Create tables at startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BrailleArt AI Backend",
    description="Backend API for Kaggle Agents for Good track: BrailleArt AI.",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
def health_check():
    """
    Service health check endpoint.
    """
    return {"status": "ok", "service": "BrailleArt AI Backend"}
