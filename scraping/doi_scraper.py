"""
DOI Scraper
Scrapes full text, tables, and images from academic articles via DOI links.
Implements multi-pattern fallback extraction to handle different publisher
HTML formats (ScienceDirect, Springer, Wiley, etc.).
"""

import time
import csv

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False


class DOIScraper:
    """
    Scrapes text, tables, and images from academic articles using Selenium.
    Tries multiple HTML element patterns to handle different publisher formats.
    """
    
    def __init__(self):
        if not UC_AVAILABLE:
            raise ImportError("undetected_chromedriver and selenium are required")
        self.driver = uc.Chrome()
        self.driver.maximize_window()
        self.all_papers = {}
        self.all_images = []
        self.all_tables = []
        self.paper_count = 1
    
    def scrape_papers(self, doi_list):
        """
        Scrape text, images, and tables for each DOI.
        
        Args:
            doi_list: List of DOI strings
        
        Returns:
            Tuple of (papers_dict, images_list, tables_list)
        """
        for doi in doi_list:
            link = f"https://doi.org/{doi}"
            print(f"\nScraping DOI: {doi}")
            self.driver.get(link)
            time.sleep(3)
            
            text = self._extract_text()
            images = self._extract_images()
            tables = self._extract_tables()
            
            self.all_papers[self.paper_count] = text
            self.all_images.append(images)
            self.all_tables.append(tables)
            self.paper_count += 1
            
            print(f"  Text: {len(text)} chars, Images: {len(images)}, Tables: {len(tables)}")
        
        return self.all_papers, self.all_images, self.all_tables
    
    def _extract_text(self):
        """
        Extract article text using multiple fallback strategies:
        1. Numbered paragraph IDs (pXXXX pattern - ScienceDirect)
        2. Named paragraph IDs (paraXXXX pattern)
        3. Short paragraph IDs (sparaXXX pattern)
        4. Raw span elements (last resort)
        """
        collected_text = ""
        
        # Strategy 1: pXXXX pattern (e.g., p0005, p0010, ...)
        collected_text = self._try_pattern("p", start=5, step=5, pad=4)
        
        # Strategy 2: paraXXXX pattern
        if not collected_text:
            collected_text = self._try_pattern("para", start=1, step=10, pad=4)
        
        # Strategy 3: sparaXXX pattern
        if not collected_text:
            collected_text = self._try_pattern("spara", start=1, step=10, pad=3)
        
        # Strategy 4: All span elements (fallback)
        if not collected_text:
            try:
                spans = self.driver.find_elements(By.XPATH, "//span[contains(text(), '')]")
                for span in spans:
                    text = span.text.strip()
                    if text:
                        collected_text += text + "\n"
            except Exception:
                pass
        
        return collected_text
    
    def _try_pattern(self, prefix, start, step, pad):
        """Try extracting text using a numbered element ID pattern."""
        collected = ""
        idx = start
        consecutive_failures = 0
        max_failures = 3
        
        while consecutive_failures < max_failures:
            element_id = f"{prefix}{str(idx).zfill(pad)}"
            try:
                element = self.driver.find_element(By.ID, element_id)
                text = element.text.strip()
                if text:
                    collected += text + "\n"
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
            except Exception:
                consecutive_failures += 1
            idx += step
        
        return collected
    
    def _extract_images(self):
        """Extract image URLs from the page (filters for journal figure images)."""
        image_urls = []
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                url = img.get_attribute("src")
                if url and "ars" in url and url.endswith(".jpg"):
                    image_urls.append(url)
        except Exception:
            pass
        return image_urls
    
    def _extract_tables(self):
        """Extract HTML tables from the page."""
        tables = []
        try:
            if "table" in self.driver.page_source.lower():
                table_elements = self.driver.find_elements(By.TAG_NAME, "table")
                for table in table_elements:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    table_data = []
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            cells = row.find_elements(By.TAG_NAME, "th")
                        table_data.append([cell.text for cell in cells])
                    if table_data:
                        tables.append(table_data)
        except Exception:
            pass
        return tables
    
    def save_results(self, output_dir="output"):
        """Save scraped text, images, and tables to files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save text
        for paper_num, text in self.all_papers.items():
            with open(f"{output_dir}/paper_{paper_num}_text.txt", "w", encoding="utf-8") as f:
                f.write(text)
        
        # Save image URLs
        with open(f"{output_dir}/collected_images.txt", "w", encoding="utf-8") as f:
            for i, urls in enumerate(self.all_images, 1):
                f.write(f"=== Paper {i} ===\n")
                for url in urls:
                    f.write(url + "\n")
        
        # Save tables
        for i, tables in enumerate(self.all_tables, 1):
            if tables:
                with open(f"{output_dir}/paper_{i}_tables.csv", "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for table in tables:
                        for row in table:
                            writer.writerow(row)
                        writer.writerow([])  # separator
        
        print(f"Results saved to {output_dir}/")
    
    def close(self):
        """Close the browser."""
        self.driver.quit()
