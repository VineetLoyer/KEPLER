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
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length
            max_length = 5000
            raw_content = text[:max_length] if len(text) > max_length else text
            
            # Create summary (first 500 characters)
            summary = text[:500] + "..." if len(text) > 500 else text
            
            return raw_content, summary
        
        except Exception as e:
            # Return error message as content
            error_msg = f"Failed to scrape {url}: {str(e)}"
            return error_msg, error_msg
