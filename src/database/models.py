"""
models.py

SQLAlchemy ORM models representing the SQLite database schema.
Includes:
1. SavedArt: Holds generated Braille art records, thresholds, dimensions, and types.
2. AgentConversation: Stores user prompt prompts, assistant replies, and token metrics.
"""

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from .db import Base

class SavedArt(Base):
    """
    Model representing generated and saved Braille art designs.
    """
    __tablename__ = "saved_art"

    id = Column(Integer, primary_key=True, index=True)
    art_type = Column(String(50), nullable=False)  # 'text' or 'image'
    source_content = Column(Text, nullable=False)   # Source text or file name
    braille_content = Column(Text, nullable=False)  # Output Braille art characters
    config_params = Column(JSON, nullable=True)     # Save dither/threshold sliders
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentConversation(Base):
    """
    Model representing historical records of user-agent conversations.
    """
    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_prompt = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    meta_logs = Column(JSON, nullable=True)         # Keep debug info / model metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
