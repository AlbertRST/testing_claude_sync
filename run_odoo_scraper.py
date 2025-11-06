"""Run Odoo Purchase Order scraper."""
from scrapers.crm_scrapers.odoo_scraper import OdooScraper
from config.odoo_config import ODOO_CONFIG


def main():
    print("Starting Odoo Purchase Order scraper...")
    print("-" * 60)
    
    scraper = OdooScraper(ODOO_CONFIG)
    data = scraper.scrape(num_pages=3)
    
    print("-" * 60)
    print(f"✓ Extraction complete: {len(data)} Purchase Orders")
    print(f"✓ Data saved to output/raw/odoo_purchase_orders.json")


if __name__ == "__main__":
    main()
