"""
Configuration file for the deeds pipeline
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
CACHE_DIR = PROJECT_ROOT / "cache"
LOG_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Input file
INPUT_JSON = DATA_DIR / "deed_reviews_northern_middlesex_20251103_110333.json"

# Output files for each step
STEP1_OUTPUT = OUTPUT_DIR / "step1_reformatted_by_deed_id.json"
STEP2_OUTPUT = OUTPUT_DIR / "step2_ocr_extracted.json"
STEP3_OUTPUT = OUTPUT_DIR / "step3_scraper_data.json"
STEP4_OUTPUT = OUTPUT_DIR / "step4_geolocation.json"
STEP5_OUTPUT = OUTPUT_DIR / "step5_final_integrated.json"
STEP5_OUTPUT_CSV = OUTPUT_DIR / "step5_final_integrated.csv"

# API Keys (from environment variables)
GOOGLE_VISION_PROJECT_ID = os.getenv("GOOGLE_VISION_PROJECT_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Processing settings
BATCH_SIZE = 10  # Number of records to process in one batch
MAX_RETRIES = 3  # Maximum number of retries for failed operations
TIMEOUT = 30  # Timeout in seconds for API calls

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Chrome driver settings (for step 3)
# Allow override via env var: export CHROME_HEADLESS=false to run non-headless
CHROME_HEADLESS = os.getenv("CHROME_HEADLESS", "true").lower() == "true"  # Default True

# Cache settings
ENABLE_CACHE = True  # Enable caching to avoid re-processing
CACHE_EXPIRY_DAYS = 30  # Cache expiration in days

