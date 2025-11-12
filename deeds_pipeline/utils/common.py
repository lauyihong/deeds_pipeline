"""
Common utility functions used across the pipeline
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..config import CACHE_DIR, LOG_DIR, LOG_FORMAT, LOG_LEVEL, CACHE_EXPIRY_DAYS


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with console and file handlers
    
    Args:
        name: Logger name
        log_file: Optional log file name (will be saved in LOG_DIR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_json(file_path: Path) -> Any:
    """
    Load data from JSON file
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Loaded JSON data
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to output JSON file
        indent: JSON indentation (default: 2)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def get_cache_key(*args) -> str:
    """
    Generate a cache key from arguments
    
    Args:
        *args: Arguments to hash
    
    Returns:
        MD5 hash string
    """
    key_string = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()


def load_from_cache(cache_key: str) -> Optional[Dict]:
    """
    Load data from cache
    
    Args:
        cache_key: Cache key
    
    Returns:
        Cached data if exists and not expired, None otherwise
    """
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    # Check if cache is expired
    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - mtime > timedelta(days=CACHE_EXPIRY_DAYS):
        return None
    
    try:
        return load_json(cache_file)
    except Exception:
        return None


def save_to_cache(cache_key: str, data: Dict) -> None:
    """
    Save data to cache
    
    Args:
        cache_key: Cache key
        data: Data to cache
    """
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        save_json(data, cache_file)
    except Exception as e:
        # Cache save failures should not break the pipeline
        print(f"Warning: Failed to save cache: {e}")


def format_timestamp() -> str:
    """
    Get current timestamp in ISO format
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()


def calculate_progress(current: int, total: int) -> str:
    """
    Calculate and format progress percentage
    
    Args:
        current: Current count
        total: Total count
    
    Returns:
        Formatted progress string (e.g., "50/100 (50.0%)")
    """
    if total == 0:
        return "0/0 (0.0%)"
    percentage = (current / total) * 100
    return f"{current}/{total} ({percentage:.1f}%)"

