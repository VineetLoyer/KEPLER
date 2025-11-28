"""Simple web scraper for KEPLER"""
import requests
from bs4 import BeautifulSoup
from typing import Tuple


class WebScraper:
    """Simple web scraper that extracts text content from URLs"""
    
    def __init__(self, timeout: int = 10):
        """Initialize web scraper
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_and_summarize(self, url: str) -> Tuple[str, str]:
        """Scrape URL and return content and summary
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (raw_content, summary)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                element.decompose()
            
            # Try to find main content area first
            main_content = None
            for selector in ['article', 'main', '[role="main"]', '.content', '#content', '.article-body']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body') or soup
            
            # Get text from main content
            text = main_content.get_text()
            
            # Clean up text - remove excessive whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove common noise patterns
            noise_patterns = [
                "This site needs JavaScript",
                "Please enable JavaScript",
                "Clipboard, Search History",
                "Skip to main",
                "Cookie Policy",
                "Privacy Policy",
                "Accept cookies",
            ]
            for pattern in noise_patterns:
                text = text.replace(pattern, "")
            
            # Clean up extra spaces
            text = ' '.join(text.split())
            
            # If content is too short or looks like an error, return link reference instead
            if len(text) < 100 or "JavaScript" in text[:200]:
                summary = f"Source: {url} (Content requires JavaScript or is not accessible for scraping)"
                raw_content = f"Link reference: {url}"
                return raw_content, summary
            
            # Limit text length
            max_length = 3000  # Reduced from 5000 to focus on relevant content
            raw_content = text[:max_length] if len(text) > max_length else text
            
            # Create summary (first 300 characters of cleaned content)
            summary = text[:300] + "..." if len(text) > 300 else text
            
            return raw_content, summary
        
        except Exception as e:
            # Return link reference instead of error
            summary = f"Source: {url} (Unable to access content: {str(e)})"
            raw_content = f"Link reference: {url}"
            return raw_content, summary
