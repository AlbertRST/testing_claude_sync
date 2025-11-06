"""Configuration settings for web scrapers."""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_RAW = BASE_DIR / "output" / "raw"
OUTPUT_PROCESSED = BASE_DIR / "output" / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Scraping settings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_DELAY = 1  # seconds between requests
TIMEOUT = 30  # request timeout in seconds

# Output settings
OUTPUT_FORMAT = "json"  # json, csv, or both
