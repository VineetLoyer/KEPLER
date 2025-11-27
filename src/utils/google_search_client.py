"""Google Custom Search API client for KEPLER"""
import requests
from typing import List, Optional
from datetime import datetime
from src.config import config


class GoogleSearchClient:
    """Client for Google Custom Search API"""
    
    def __init__(self, api_key: Optional[str] = None, engine_id: Optional[str] = None):
        """Initialize Google Search client
        
        Args:
            api_key: Google API key (uses config if None)
            engine_id: Custom Search Engine ID (uses config if None)
        """
        self.api_key = api_key or config.api.google_search_api_key
        self.engine_id = engine_id or config.api.google_search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.engine_id:
            raise ValueError(
                "Google Search API key and engine ID are required. "
                "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables."
            )
    
    def web_search(self, query: str, max_results: int = 10) -> List[dict]:
        """Perform web search using Google Custom Search API
        
        Args:
            query: Search query
            max_results: Maximum number of results (max 10 per request)
            
        Returns:
            List of search results
        """
        results = []
        
        try:
            # Google Custom Search API limits to 10 results per request
            num_results = min(max_results, 10)
            
            params = {
                'key': self.api_key,
                'cx': self.engine_id,
                'q': query,
                'num': num_results,
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            for item in data.get('items', []):
                result = {
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'publish_date': None,  # Google CSE doesn't provide publish dates
                    'domain': self._extract_domain(item.get('link', '')),
                }
                results.append(result)
        
        except requests.exceptions.RequestException as e:
            print(f"Google Search API error: {e}")
            # Return empty results on error
            return []
        
        return results
    
    def image_search(self, query: str, max_results: int = 10) -> List[dict]:
        """Perform image search using Google Custom Search API
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of image search results
        """
        results = []
        
        try:
            num_results = min(max_results, 10)
            
            params = {
                'key': self.api_key,
                'cx': self.engine_id,
                'q': query,
                'num': num_results,
                'searchType': 'image',
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            for item in data.get('items', []):
                result = {
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'publish_date': None,
                    'domain': self._extract_domain(item.get('link', '')),
                }
                results.append(result)
        
        except requests.exceptions.RequestException as e:
            print(f"Google Image Search API error: {e}")
            return []
        
        return results
    
    def reverse_image_search(self, image: bytes) -> List[dict]:
        """Reverse image search (not supported by Google Custom Search API)
        
        Args:
            image: Image bytes
            
        Returns:
            Empty list (not supported)
        """
        # Google Custom Search API doesn't support reverse image search
        # Would need Google Vision API or similar
        return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ''
        
        if '://' in url:
            url = url.split('://', 1)[1]
        
        domain = url.split('/')[0]
        
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
