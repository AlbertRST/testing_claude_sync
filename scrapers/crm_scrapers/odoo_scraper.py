"""Odoo Purchase Order scraper using Playwright."""
from playwright.sync_api import sync_playwright
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from scrapers.base_scraper import BaseScraper


class OdooScraper(BaseScraper):
    """Scraper for Odoo ERP Purchase Orders."""
    
    def __init__(self, config: dict):
        super().__init__("OdooScraper")
        self.login_url = config.get('login_url', 'http://localhost:8069')
        self.po_list_url = config.get('po_list_url', 'http://localhost:8069/odoo/purchase-orders')
        self.credentials = config['credentials']
        self.concurrent_workers = config.get('workers', 8)
        self.storage_state = None
        
    def block_resources(self, route):
        """Block unnecessary resources to speed up scraping."""
        if route.request.resource_type in ['stylesheet', 'image', 'font', 'media']:
            route.abort()
        else:
            route.continue_()
    
    def login_and_get_storage(self, playwright):
        """Perform initial login and save session state."""
        self.logger.info("Performing initial login...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(self.login_url)
        page.fill('input[name="login"]', self.credentials['email'])
        page.fill('input[name="password"]', self.credentials['password'])
        page.click('button[type="submit"]')
        page.wait_for_selector('.o_web_client', timeout=30000)
        
        storage = context.storage_state()
        browser.close()
        self.logger.info("Login successful")
        return storage
    
    def get_po_numbers_from_page(self, page):
        """Extract PO numbers from current page."""
        po_numbers = []
        po_rows = page.query_selector_all('tr.o_data_row')
        for row in po_rows:
            po_cell = row.query_selector('td[name="name"]')
            if po_cell:
                po_numbers.append(po_cell.inner_text().strip())
        return po_numbers
    
    def extract_single_po(self, po_number, page_num, storage_state, index, total):
        """Extract data from a single Purchase Order."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(storage_state=storage_state)
                page = context.new_page()
                page.route("**/*", self.block_resources)
                
                page.goto(self.po_list_url)
                page.wait_for_selector('tr.o_data_row', timeout=15000)
                
                # Navigate to correct page
                for _ in range(page_num - 1):
                    next_button = page.locator('button.o_pager_next')
                    next_button.click()
                    page.wait_for_selector('tr.o_data_row', timeout=15000)
                    time.sleep(0.5)
                
                # Click PO link
                po_link = page.locator(f'td[name="name"]:has-text("{po_number}")').first
                po_link.click()
                page.wait_for_selector('.o_field_res_partner_many2one', timeout=15000)
                
                po_data = {'po_number': po_number, 'url': page.url}
                
                # Extract vendor
                vendor_elem = page.query_selector('.o_field_res_partner_many2one .align-bottom')
                if vendor_elem:
                    po_data['vendor'] = vendor_elem.inner_text().strip()
                
                # Extract order date
                order_date_elem = page.query_selector('div[name="date_approve"] .o_field_datetime')
                if order_date_elem:
                    po_data['order_date'] = order_date_elem.inner_text().strip()
                
                # Extract expected arrival
                arrival_elem = page.query_selector('button[data-field="date_planned"]')
                if arrival_elem:
                    po_data['expected_arrival'] = arrival_elem.inner_text().strip()
                
                # Extract status
                status_elem = page.query_selector('.o_statusbar_status .o_arrow_button_current')
                if status_elem:
                    po_data['status'] = status_elem.inner_text().strip()
                
                # Extract total amount
                total_elem = page.query_selector('span[name="amount_total"]')
                if total_elem:
                    total_text = total_elem.inner_text().strip()
                    parts = total_text.split()
                    if len(parts) == 2:
                        po_data['currency'] = parts[0]
                        po_data['total_amount'] = parts[1]
                    else:
                        po_data['total_amount'] = total_text
                
                # Extract line items
                line_items = []
                product_rows = page.query_selector_all('tbody.ui-sortable tr.o_data_row')
                
                for row in product_rows:
                    line_item = {}
                    
                    product_elem = row.query_selector('td[name="product_id"] a')
                    if product_elem:
                        line_item['product'] = product_elem.inner_text().strip()
                    
                    qty_elem = row.query_selector('td[name="product_qty"]')
                    if qty_elem:
                        line_item['quantity'] = float(qty_elem.inner_text().strip())
                    
                    price_elem = row.query_selector('td[name="price_unit"]')
                    if price_elem:
                        line_item['unit_price'] = float(price_elem.inner_text().strip())
                    
                    tax_elem = row.query_selector('td[name="tax_ids"] .o_tag_badge_text')
                    if tax_elem:
                        line_item['taxes'] = tax_elem.inner_text().strip()
                    
                    subtotal_elem = row.query_selector('td[name="price_subtotal"]')
                    if subtotal_elem:
                        subtotal_raw = subtotal_elem.inner_text().strip()
                        subtotal_clean = subtotal_raw.replace('$', '').replace(' ', '').replace(',', '')
                        line_item['subtotal'] = float(subtotal_clean)
                    
                    if line_item:
                        line_items.append(line_item)
                
                po_data['line_items'] = line_items
                browser.close()
                self.logger.info(f"[{index}/{total}] {po_number}: {len(line_items)} items")
                return po_data
                
        except Exception as e:
            self.logger.error(f"[{index}/{total}] {po_number}: {str(e)}")
            return {'po_number': po_number, 'error': str(e)}
    
    def process_page(self, page_num, playwright, storage_state, all_results):
        """Process a complete page of Purchase Orders."""
        self.logger.info(f"Processing page {page_num}")
        
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(storage_state=storage_state)
        page = context.new_page()
        page.route("**/*", self.block_resources)
        
        page.goto(self.po_list_url)
        self.logger.info(f"Navigated to: {page.url}")
        
        try:
            page.wait_for_selector('tr.o_data_row', timeout=30000)
        except Exception as e:
            self.logger.error(f"Failed to find rows. URL: {page.url}, Title: {page.title()}")
            page.screenshot(path='output/debug_screenshot.png')
            self.logger.error("Screenshot saved to output/debug_screenshot.png")
            browser.close()
            raise
        
        # Navigate to correct page
        for _ in range(page_num - 1):
            next_button = page.locator('button.o_pager_next')
            next_button.click()
            page.wait_for_selector('tr.o_data_row', timeout=15000)
            time.sleep(1)
        
        # Extract PO numbers
        po_numbers = self.get_po_numbers_from_page(page)
        counter = page.locator('.o_pager_value').inner_text()
        self.logger.info(f"Range: {counter}, POs found: {len(po_numbers)}")
        
        browser.close()
        
        # Parallel processing
        self.logger.info(f"Extracting with {self.concurrent_workers} workers...")
        page_results = []
        total = len(po_numbers)
        
        with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
            futures = {
                executor.submit(self.extract_single_po, po_num, page_num, storage_state, i+1, total): po_num 
                for i, po_num in enumerate(po_numbers)
            }
            
            for future in as_completed(futures):
                page_results.append(future.result())
        
        # Sort and append to overall results
        page_results.sort(key=lambda x: x.get('po_number', ''))
        all_results.extend(page_results)
        
        self.logger.info(f"Page {page_num} completed. Total accumulated: {len(all_results)} POs")
        return all_results
    
    def scrape(self, num_pages: int = 3):
        """Main scraping method.
        
        Args:
            num_pages: Number of pages to scrape
        """
        start_time = time.time()
        all_results = []
        
        with sync_playwright() as playwright:
            storage_state = self.login_and_get_storage(playwright)
            
            # Process pages sequentially
            for page_num in range(1, num_pages + 1):
                self.process_page(page_num, playwright, storage_state, all_results)
                
                # Save incrementally
                self.save_json(all_results, 'odoo_purchase_orders.json')
        
        elapsed = time.time() - start_time
        success_count = sum(1 for po in all_results if 'error' not in po)
        
        self.logger.info(f"Extraction completed: {len(all_results)} POs, "
                        f"{success_count} successful, "
                        f"{len(all_results) - success_count} errors, "
                        f"{elapsed:.2f}s total, "
                        f"{elapsed/len(all_results):.2f}s per PO")
        
        return all_results
