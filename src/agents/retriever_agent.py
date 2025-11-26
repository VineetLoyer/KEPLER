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
        
        # Perform search
        results = self.search_client.web_search(claim.text, max_results)
        
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
        5. Scrape and summarize content
        
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
        
        # 5. Scrape and summarize content
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
