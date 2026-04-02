"""
Springer Search
Fetches articles from Springer Nature API and crawls Springer for PDF links
using Scrapy.
"""

import os
import csv
import re
import requests
from urllib.parse import quote, urljoin

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False


def fetch_springer_articles(all_words, exact_phrase="", at_least_one_word="",
                            without_words="", title_contains="", author_editor="",
                            start_year="2000", end_year="2024", api_key=None):
    """
    Fetch articles from the Springer Nature metadata API.
    
    Args:
        all_words: Main search terms
        exact_phrase: Exact phrase to match
        at_least_one_word: At least one of these words
        without_words: Exclude these words
        title_contains: Filter by title
        author_editor: Filter by author/editor
        start_year: Publication start year
        end_year: Publication end year
        api_key: Springer API key (from env if not provided)
    
    Returns:
        List of article dicts with title and URL
    """
    if api_key is None:
        api_key = os.getenv("SPRINGER_API_KEY", "")
    
    base_url = "https://api.springernature.com/metadata/json?"
    query_parts = []
    
    if all_words:
        formatted = "+AND+".join(quote(w.strip()) for w in all_words.split())
        query_parts.append(formatted)
    if exact_phrase:
        query_parts.append(f"%22{quote(exact_phrase)}%22")
    if at_least_one_word:
        or_terms = "%28" + "+OR+".join(quote(w.strip()) for w in at_least_one_word.split()) + "%29"
        query_parts.append(or_terms)
    if without_words:
        not_terms = "%28" + "+AND+".join(quote(w.strip()) for w in without_words.split()) + "%29"
        query_parts.append(f"NOT+{not_terms}")
    
    query = "+AND+".join(query_parts)
    url = f"{base_url}q={query}&api_key={api_key}&showAll=true"
    
    if title_contains:
        url += f"&dc.title={quote(title_contains)}"
    if author_editor:
        url += f"&dc.creator={quote(author_editor)}"
    if start_year and end_year:
        url += f"&facet-start-year={start_year}&facet-end-year={end_year}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        articles = data.get("records", [])
        print(f"Fetched {len(articles)} articles from Springer")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Springer API: {e}")
        return []


if SCRAPY_AVAILABLE:
    class SpringerSpider(scrapy.Spider):
        """Crawls Springer for article URLs and validates PDF availability."""
        
        name = "springer"
        max_articles = 20
        download_delay = 0.1
        current_page = 1
        total_articles = 0
        custom_settings = {
            "RETRY_ENABLED": True,
            "RETRY_TIMES": 1,
            "DOWNLOAD_TIMEOUT": 3,
            "HTTPERROR_ALLOW_ALL": True,
        }
        
        def __init__(self, query=None, output_dir="output", *args, **kwargs):
            super().__init__(*args, **kwargs)
            if query is None:
                query = "california wastewater management"
            self.start_urls = [
                f"https://link.springer.com/search?query={quote(query)}&showAll=false"
            ]
            os.makedirs(output_dir, exist_ok=True)
            self.csv_path = os.path.join(output_dir, "springer_articles.csv")
            self.csv_file = open(self.csv_path, mode="a", newline="", encoding="utf-8")
            self.csv_writer = csv.writer(self.csv_file)
            if not os.path.isfile(self.csv_path) or os.path.getsize(self.csv_path) == 0:
                self.csv_writer.writerow(["Title", "Article URL", "PDF URL"])
        
        def closed(self, reason):
            self.csv_file.close()
        
        def parse(self, response):
            if self.total_articles >= self.max_articles:
                return
            
            links = response.css("ol#results-list li h2 a.title::attr(href)").getall()
            if not links:
                return
            
            for link in links:
                if self.total_articles >= self.max_articles:
                    break
                yield scrapy.Request(response.urljoin(link), callback=self.parse_article)
            
            if self.total_articles < self.max_articles:
                self.current_page += 1
                next_url = re.sub(r"page=\d+", f"page={self.current_page}", response.url)
                if "page=" not in next_url:
                    next_url = f"{response.url}&page={self.current_page}"
                yield scrapy.Request(next_url, callback=self.parse)
        
        def parse_article(self, response):
            if self.total_articles >= self.max_articles:
                return
            
            title = response.css('meta[property="og:title"]::attr(content)').get() or "Untitled"
            article_url = response.css('meta[property="og:url"]::attr(content)').get()
            
            if article_url:
                path_parts = article_url.split("/")
                if len(path_parts) >= 3:
                    identifier = "/".join(path_parts[4:])
                    pdf_url = f"https://link.springer.com/content/pdf/{identifier}.pdf"
                    
                    self.csv_writer.writerow([title, article_url, pdf_url])
                    self.total_articles += 1
                    print(f"Added: {title}")
