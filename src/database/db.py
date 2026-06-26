"""
db.py

SQLAlchemy engine configuration and session manager setup.
Integrates with SQLite database configured via environment variables.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./braille_art.db")

# For SQLite, connect_args={"check_same_thread": False} is required
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=True  # Change to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency generator for retrieving database sessions in FastAPI route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
