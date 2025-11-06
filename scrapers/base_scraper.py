"""Base scraper class for all web scrapers."""
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import json
import pandas as pd
from config.settings import OUTPUT_RAW, REQUEST_DELAY, LOGS_DIR

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'scraper.log'),
        logging.StreamHandler()
    ]
)


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.delay = REQUEST_DELAY
        
    @abstractmethod
    def scrape(self):
        """Main scraping method to be implemented by subclasses."""
        pass
    
    def save_json(self, data: list, filename: str):
        """Save scraped data as JSON."""
        output_path = OUTPUT_RAW / filename
        OUTPUT_RAW.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(data)} records to {output_path}")
        return output_path
    
    def save_csv(self, data: list, filename: str):
        """Save scraped data as CSV."""
        output_path = OUTPUT_RAW / filename
        OUTPUT_RAW.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Saved {len(data)} records to {output_path}")
        return output_path
    
    def rate_limit(self):
        """Implement rate limiting between requests."""
        time.sleep(self.delay)
