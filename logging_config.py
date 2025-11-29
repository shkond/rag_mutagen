"""
Logging configuration module for Mutagen RAG system.
Consolidates duplicate logging setup code and provides centralized logging initialization.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import (
    DEFAULT_LOG_FILE,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    LOG_LEVEL
)

# Repository root directory
REPO_ROOT = Path(__file__).resolve().parent

# Logger instance
logger = logging.getLogger("mutagen-rag")

# Log file path from environment variable or default
LOG_FILE = os.getenv("MCP_LOG_FILE", str(REPO_ROOT / DEFAULT_LOG_FILE))


def setup_logging():
    """
    Initialize logging configuration for the Mutagen RAG system.
    
    Sets up:
    - Console handler (stderr) for INFO level and above
    - Rotating file handler for persistent logs
    - Consistent formatting across all handlers
    
    Falls back to stderr-only logging if file handler cannot be created.
    """
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    
    # Configure stderr handler
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Get root logger and clear existing handlers
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    
    # Add stderr handler
    root.addHandler(stderr_handler)
    root.setLevel(getattr(logging, LOG_LEVEL))
    
    # Try to add file handler
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # Test write access
        with open(LOG_FILE, "a", encoding="utf-8"):
            pass
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        root.addHandler(file_handler)
        
        logger.info("Logging initialized to %s", LOG_FILE)
    except Exception as e:
        logger.warning(
            "Cannot open log file %s: %s. Continuing with stderr only.",
            LOG_FILE,
            e
        )


def get_logger(name: str = "mutagen-rag") -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (default: "mutagen-rag")
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
