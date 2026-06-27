"""Retriever Agent for KEPLER system
This module handles the collection of multimodal evidence from the web using
multiple search strategies including web search, image search, and reverse
image search. It also implements temporal filtering and domain exclusion.
"""
from typing import List, Optional, Protocol
from datetime import datetime
from src.models.data_models import AtomicClaim, Source, EvidencePiece
from src.config import config
import uuid


class SearchClient(Protocol):
    """Protocol for search client implementations"""
    
    def web_search(self, query: str, max_results: int) -> List[dict]:
        """Perform web search and return results"""
        ...
    
    def image_search(self, query: str, max_results: int) -> List[dict]:
        """Perform image search and return results"""
        ...
    
    def reverse_image_search(self, image: bytes) -> List[dict]:
        """Perform reverse image search and return results"""
        ...


class ScraperClient(Protocol):
    """Protocol for web scraping client implementations"""
    
    def scrape_and_summarize(self, url: str) -> tuple[str, str]:
        """Scrape URL and return (raw_content, summary)"""
        ...


class RetrieverAgent:
    """Agent responsible for retrieving multimodal evidence from the web"""
    
    def __init__(
        self,
        search_client: Optional[SearchClient] = None,
        scraper_client: Optional[ScraperClient] = None,
    ):
        """Initialize the Retriever Agent
        
        Args:
            search_client: Optional search client for making search API calls.
                          If None, uses a mock client for testing.
            scraper_client: Optional scraper client for web scraping.
                           If None, uses a mock client for testing.
        """
        self.search_client = search_client or MockSearchClient()
        self.scraper_client = scraper_client or MockScraperClient()
        self.max_results = config.system.max_search_results
        self.fact_checking_domains = config.system.fact_checking_domains
        self.restricted_domains = config.system.restricted_domains
    
    def web_search(self, claim: AtomicClaim, max_results: Optional[int] = None) -> List[Source]:
        """Perform web search to collect relevant textual information
        
        Args:
            claim: Atomic claim to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of Source objects from web search
        """
        if max_results is None:
            max_results = self.max_results
        
        # Generate optimized search query
        search_query = self._generate_search_query(claim.text)
        
        # Perform search
        results = self.search_client.web_search(search_query, max_results)
        
        # Convert to Source objects
        sources = []
        for result in results:
            source = Source(
                url=result.get('url', ''),
                title=result.get('title', ''),
                publish_date=result.get('publish_date'),
                domain=self._extract_domain(result.get('url', '')),
                content_type='text',
            )
            sources.append(source)
        
        return sources
    
    def _generate_search_query(self, claim_text: str) -> str:
        """Generate an optimized search query from a claim
        
        Converts factual claims into better search queries by:
        - Extracting key entities and attributes
        - Removing definitive statements (is, are, was, were)
        - Adding context keywords
        
        Args:
            claim_text: Original claim text
            
        Returns:
            Optimized search query
        """
        import re
        
        # Remove trailing punctuation
        query = claim_text.strip().rstrip('.')
        
        # Pattern: "X is/are/was/were Y" → "X Y"
        # Example: "Eiffel Tower is 600 meters tall" → "Eiffel Tower 600 meters tall"
        query = re.sub(r'\s+(is|are|was|were|has|have|had)\s+', ' ', query, flags=re.IGNORECASE)
        
        # For numerical claims, add context keywords
        # Example: "Eiffel Tower 600 meters tall" → "Eiffel Tower height meters"
        if re.search(r'\d+\s*(meters?|feet|km|miles|kg|pounds|years?|celsius|fahrenheit)', query, re.IGNORECASE):
            # Extract the subject (before the number)
            match = re.match(r'(.+?)\s+\d+', query)
            if match:
                subject = match.group(1).strip()
                
                # Determine the attribute being measured
                if 'meter' in query.lower() or 'feet' in query.lower() or 'tall' in query.lower() or 'high' in query.lower():
                    attribute = 'height'
                elif 'kg' in query.lower() or 'pound' in query.lower() or 'weight' in query.lower():
                    attribute = 'weight'
                elif 'year' in query.lower() or 'age' in query.lower():
                    attribute = 'age'
                elif 'celsius' in query.lower() or 'fahrenheit' in query.lower() or 'temperature' in query.lower():
                    attribute = 'temperature'
                else:
                    attribute = ''
                
                # Reconstruct query with attribute
                if attribute:
                    query = f"{subject} {attribute}"
        
        # For date claims, add context
        # Example: "Obama was 44th President" → "Obama 44th President United States"
        if 'president' in query.lower() and 'united states' not in query.lower():
            query += ' United States'
        
        return query
    
    def image_search(self, query: str, max_results: Optional[int] = None) -> List[Source]:
        """Perform image search to collect relevant visual evidence
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of Source objects from image search
        """
        if max_results is None:
            max_results = self.max_results
        
        # Perform search
        results = self.search_client.image_search(query, max_results)
        
        # Convert to Source objects
        sources = []
        for result in results:
            source = Source(
                url=result.get('url', ''),
                title=result.get('title', ''),
                publish_date=result.get('publish_date'),
                domain=self._extract_domain(result.get('url', '')),
                content_type='image',
            )
            sources.append(source)
        
        return sources
    
    def reverse_image_search(self, image: bytes) -> List[Source]:
        """Perform reverse image search to find visually similar content
        
        Args:
            image: Image data as bytes
            
        Returns:
            List of Source objects from reverse image search
        """
        # Perform search
        results = self.search_client.reverse_image_search(image)
        
        # Convert to Source objects
        sources = []
        for result in results:
            source = Source(
                url=result.get('url', ''),
                title=result.get('title', ''),
                publish_date=result.get('publish_date'),
                domain=self._extract_domain(result.get('url', '')),
                content_type=result.get('content_type', 'image'),
            )
            sources.append(source)
        
        return sources
    
    def scrape_and_summarize(self, source: Source) -> EvidencePiece:
        """Scrape and summarize content from a source
        
        Args:
            source: Source to scrape
            
        Returns:
            EvidencePiece with scraped and summarized content
        """
        # Scrape the source
        raw_content, summary = self.scraper_client.scrape_and_summarize(source.url)
        
        # Create evidence piece
        evidence = EvidencePiece(
            id=str(uuid.uuid4()),
            source=source,
            summary=summary,
            raw_content=raw_content,
            relevance_score=None,
            credibility_score=None,
            recency_score=None,
            final_rank_score=None,
        )
        
        return evidence
    
    def filter_by_date(self, sources: List[Source], claim_date: datetime) -> List[Source]:
        """Filter sources to only include those published before the claim date
        
        Args:
            sources: List of sources to filter
            claim_date: Date of the claim
            
        Returns:
            Filtered list of sources
        """
        filtered = []
        for source in sources:
            # Keep sources with no publish date (unknown) or published before claim date
            if source.publish_date is None or source.publish_date < claim_date:
                filtered.append(source)
        
        return filtered
    
    def exclude_domains(self, sources: List[Source], blocklist: Optional[List[str]] = None) -> List[Source]:
        """Exclude sources from blocked domains
        
        Args:
            sources: List of sources to filter
            blocklist: Optional custom blocklist. If None, uses system default.
            
        Returns:
            Filtered list of sources
        """
        if blocklist is None:
            blocklist = self.fact_checking_domains + self.restricted_domains
        
        # Normalize blocklist domains to lowercase
        blocklist_lower = [domain.lower() for domain in blocklist]
        
        filtered = []
        for source in sources:
            # Check if source domain is in blocklist
            if source.domain.lower() not in blocklist_lower:
                filtered.append(source)
        
        return filtered
    
    def filter_low_quality_sources(self, sources: List[Source]) -> List[Source]:
        """Filter out low-quality sources based on domain patterns
        
        This removes sources that are unlikely to provide reliable evidence:
        - Social media posts (unless no other sources available)
        - Homework help sites with user-generated answers
        - E-commerce/shopping sites
        - Personal blogs (unless authoritative)
        
        Args:
            sources: List of sources to filter
            
        Returns:
            Filtered list of higher-quality sources
        """
        # Define low-quality domain patterns
        low_quality_patterns = [
            # Social media (keep if no other sources)
            'facebook.com',
            'twitter.com',
            'x.com',
            'instagram.com',
            'tiktok.com',
            'snapchat.com',
            
            # E-commerce/shopping
            'amazon.com',
            'ebay.com',
            'etsy.com',
            'alibaba.com',
            'aliexpress.com',
            
            # Personal blogs (generic platforms)
            'blogspot.com',
            'tumblr.com',
            'wix.com',
            'weebly.com',
            'squarespace.com',
        ]
        
        # Separate sources into high and low quality
        high_quality = []
        low_quality = []
        
        for source in sources:
            domain_lower = source.domain.lower()
            
            # Check if domain matches low-quality patterns
            is_low_quality = any(pattern in domain_lower for pattern in low_quality_patterns)
            
            if is_low_quality:
                low_quality.append(source)
            else:
                high_quality.append(source)
        
        # If we have enough high-quality sources, use only those
        # Otherwise, include some low-quality sources as fallback
        if len(high_quality) >= 5:
            return high_quality
        else:
            # Not enough high-quality sources, include some low-quality ones
            # Prioritize: keep up to 3 low-quality sources
            return high_quality + low_quality[:3]
    
    def retrieve_evidence(
        self,
        claim: AtomicClaim,
        claim_date: datetime,
        has_visual_content: bool = False,
        image: Optional[bytes] = None,
    ) -> List[EvidencePiece]:
        """Retrieve and process evidence for a claim
        
        This is the main entry point that orchestrates the retrieval process:
        1. Perform web search
        2. Perform image searches if visual content is present
        3. Filter by date
        4. Exclude blocked domains
        5. Filter low-quality sources
        6. Scrape and summarize content
        
        Args:
            claim: Atomic claim to retrieve evidence for
            claim_date: Date of the claim for temporal filtering
            has_visual_content: Whether the input contains visual content
            image: Optional image data for reverse image search
            
        Returns:
            List of EvidencePiece objects
        """
        all_sources = []
        
        # 1. Web search (always performed)
        web_sources = self.web_search(claim)
        all_sources.extend(web_sources)
        
        # 2. Image searches if visual content is present
        if has_visual_content:
            # Image search using claim text
            image_sources = self.image_search(claim.text)
            all_sources.extend(image_sources)
            
            # Reverse image search if image data is provided
            if image is not None:
                reverse_sources = self.reverse_image_search(image)
                all_sources.extend(reverse_sources)
        
        # 3. Filter by date (temporal consistency)
        all_sources = self.filter_by_date(all_sources, claim_date)
        
        # 4. Exclude blocked domains
        all_sources = self.exclude_domains(all_sources)
        
        # 5. Filter low-quality sources (NEW)
        all_sources = self.filter_low_quality_sources(all_sources)
        
        # 6. Scrape and summarize content
        evidence_pieces = []
        for source in all_sources:
            try:
                evidence = self.scrape_and_summarize(source)
                evidence_pieces.append(evidence)
            except Exception as e:
                # Log error but continue with other sources
                # In production, this would use proper logging
                continue
        
        return evidence_pieces
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL
        
        Args:
            url: Full URL
            
        Returns:
            Domain name
        """
        if not url:
            return ''
        
        # Simple domain extraction
        # Remove protocol
        if '://' in url:
            url = url.split('://', 1)[1]
        
        # Get domain (before first /)
        domain = url.split('/')[0]
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain


class MockSearchClient:
    """Mock search client for testing purposes"""
    
    def web_search(self, query: str, max_results: int) -> List[dict]:
        """Mock web search implementation"""
        # Return mock results
        results = []
        for i in range(min(3, max_results)):
            results.append({
                'url': f'https://example{i}.com/article',
                'title': f'Article about {query[:30]}',
                'publish_date': datetime(2023, 1, 1 + i),
                'domain': f'example{i}.com',
            })
        return results
    
    def image_search(self, query: str, max_results: int) -> List[dict]:
        """Mock image search implementation"""
        results = []
        for i in range(min(2, max_results)):
            results.append({
                'url': f'https://images{i}.com/image.jpg',
                'title': f'Image of {query[:30]}',
                'publish_date': datetime(2023, 1, 1 + i),
                'domain': f'images{i}.com',
            })
        return results
    
    def reverse_image_search(self, image: bytes) -> List[dict]:
        """Mock reverse image search implementation"""
        results = []
        for i in range(2):
            results.append({
                'url': f'https://reverse{i}.com/similar',
                'title': f'Similar image {i}',
                'publish_date': datetime(2023, 1, 1 + i),
                'domain': f'reverse{i}.com',
                'content_type': 'image',
            })
        return results


class MockScraperClient:
    """Mock scraper client for testing purposes"""
    
    def scrape_and_summarize(self, url: str) -> tuple[str, str]:
        """Mock scraping and summarization"""
        raw_content = f"This is the full content from {url}. It contains detailed information about the topic."
        summary = f"Summary of content from {url}"
        return raw_content, summary
