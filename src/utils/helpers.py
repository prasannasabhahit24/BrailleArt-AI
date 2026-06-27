"""
helpers.py

General utility functions, including logging wrappers, text processing, 
and mathematical transformations needed for coordinate plotting.
"""

import os
import logging
import sys
from typing import Any

def setup_logger(name: str = "brailleart_ai") -> logging.Logger:
    """
    Configure a standard logger writing to stdout.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Resolve log level dynamically from environment
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Create pre-configured application logger instance
logger = setup_logger()

def safe_cast_int(val: Any, default: int = 0) -> int:
    """
    Safely cast user input arguments to integers.
    """
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
