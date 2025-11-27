"""Reranker Agent for KEPLER system

This module handles the filtering and prioritization of retrieved evidence based on
relevance, credibility, and recency. It implements a multi-factor ranking system
with credibility tiers and domain credibility calculations.
"""
from typing import List, Dict, Optional
from datetime import datetime
from src.models.data_models import EvidencePiece, AtomicClaim, Source, DomainCredibility
from src.config import config


class RerankerAgent:
    """Agent responsible for ranking and filtering evidence by quality and relevance"""
    
    # Credibility tier boundaries
    TIER_1_MIN = 0.9  # Published papers, peer-reviewed journals
    TIER_2_MIN = 0.7  # Verified news sources (Reuters, AP, BBC)
    TIER_3_MIN = 0.4  # General news sites, established blogs
    TIER_4_MIN = 0.0  # Social media, unverified sources
    
    # Known domain credibility database
    DOMAIN_CREDIBILITY_DB: Dict[str, float] = {
        # Tier 1: Academic, peer-reviewed, and encyclopedic (0.88-0.98)
        'arxiv.org': 0.95,
        'nature.com': 0.98,
        'science.org': 0.98,
        'ieee.org': 0.95,
        'acm.org': 0.95,
        'springer.com': 0.92,
        'sciencedirect.com': 0.92,
        'wikipedia.org': 0.88,  # High credibility for factual claims
        'en.wikipedia.org': 0.88,
        'britannica.com': 0.90,
        'nasa.gov': 0.98,
        'nih.gov': 0.95,
        'cdc.gov': 0.95,
        'who.int': 0.95,
        'un.org': 0.90,
        
        # Official/Authoritative sources (0.85-0.95)
        'toureiffel.paris': 0.92,  # Official Eiffel Tower site
        'louvre.fr': 0.92,  # Official Louvre site
        'whitehouse.gov': 0.90,
        'europa.eu': 0.90,
        'gov.uk': 0.88,
        'canada.ca': 0.88,
        
        # General government/educational domains (0.80-0.88)
        'gov': 0.85,  # General government domains
        'edu': 0.82,  # General educational domains
        'ac.uk': 0.82,  # UK academic
        'edu.au': 0.82,  # Australian academic
        
        # Tier 2: Verified news sources (0.75-0.85)
        'reuters.com': 0.85,
        'apnews.com': 0.85,
        'bbc.com': 0.82,
        'bbc.co.uk': 0.82,
        'npr.org': 0.80,
        'pbs.org': 0.80,
        'economist.com': 0.78,
        'ft.com': 0.78,  # Financial Times
        
        # Tier 3: General news and established sources (0.60-0.75)
        'nytimes.com': 0.75,
        'washingtonpost.com': 0.75,
        'theguardian.com': 0.72,
        'wsj.com': 0.72,  # Wall Street Journal
        'cnn.com': 0.68,
        'forbes.com': 0.65,
        'techcrunch.com': 0.60,
        'wired.com': 0.62,
        'nationalgeographic.com': 0.70,
        
        # Tier 4: Educational/Reference sites (0.45-0.65)
        'khanacademy.org': 0.65,
        'coursera.org': 0.60,
        'edx.org': 0.60,
        'britannica.com': 0.70,
        'merriam-webster.com': 0.65,
        'dictionary.com': 0.55,
        
        # Tier 5: Q&A and homework sites (0.35-0.50)
        'stackoverflow.com': 0.55,  # Technical Q&A
        'stackexchange.com': 0.50,
        'quora.com': 0.40,
        'brainly.com': 0.35,  # Homework help
        'chegg.com': 0.35,  # Homework help
        'gauthmath.com': 0.35,  # Homework help
        
        # Tier 6: Blogs, forums, and social media (0.15-0.35)
        'medium.com': 0.35,
        'blogger.com': 0.30,
        'wordpress.com': 0.30,
        'reddit.com': 0.25,
        'twitter.com': 0.20,
        'x.com': 0.20,  # Twitter/X
        'facebook.com': 0.15,
        'instagram.com': 0.15,
        'tiktok.com': 0.10,
        'flickr.com': 0.30,  # Photo sharing
        
        # Tier 7: Low credibility - satire, jokes, unreliable (0.05-0.20)
        'theonion.com': 0.05,  # Satire
        'clickhole.com': 0.05,  # Satire
        'babylonbee.com': 0.05,  # Satire
        'reasons.org': 0.15,  # Advocacy/apologetics site
        'cheeseprofessor.com': 0.20,  # Blog
        'snackstack.net': 0.20,  # Blog
        'mentalfloss.com': 0.40,  # Entertainment/trivia
        'smartdoll.jp': 0.10,  # E-commerce
    }
    
    # Domain credibility factors database (for historical analysis)
    DOMAIN_FACTORS_DB: Dict[str, DomainCredibility] = {}
    
    def __init__(
        self,
        relevance_weight: float = 0.4,
        credibility_weight: float = 0.4,
        recency_weight: float = 0.2,
        min_rank_threshold: float = 0.3,
    ):
        """Initialize the Reranker Agent
        
        Args:
            relevance_weight: Weight for relevance score in ranking formula
            credibility_weight: Weight for credibility score in ranking formula
            recency_weight: Weight for recency score in ranking formula
            min_rank_threshold: Minimum rank score to pass evidence to next stage
        """
        self.relevance_weight = relevance_weight
        self.credibility_weight = credibility_weight
        self.recency_weight = recency_weight
        self.min_rank_threshold = min_rank_threshold
    
    def rank_evidence(
        self,
        evidence: List[EvidencePiece],
        claim: AtomicClaim,
    ) -> List[EvidencePiece]:
        """Rank evidence based on relevance, credibility, and recency
        
        This is the main entry point that:
        1. Calculates relevance scores
        2. Calculates credibility scores
        3. Calculates recency scores
        4. Combines scores using the ranking formula
        5. Sorts by final rank score
        6. Filters out low-ranked evidence
        
        Args:
            evidence: List of evidence pieces to rank
            claim: Atomic claim being verified
            
        Returns:
            Ranked and filtered list of evidence pieces
        """
        # Calculate scores for each evidence piece
        for piece in evidence:
            piece.relevance_score = self.calculate_relevance(piece, claim)
            piece.credibility_score = self.calculate_credibility(piece.source)
            piece.recency_score = self.calculate_recency_score(
                piece.source.publish_date,
                datetime.now()
            )
            
            # Calculate final rank score
            piece.final_rank_score = (
                self.relevance_weight * piece.relevance_score +
                self.credibility_weight * piece.credibility_score +
                self.recency_weight * piece.recency_score
            )
        
        # Sort by final rank score (descending)
        ranked_evidence = sorted(
            evidence,
            key=lambda e: e.final_rank_score if e.final_rank_score is not None else 0.0,
            reverse=True
        )
        
        # Filter out low-ranked evidence
        filtered_evidence = [
            e for e in ranked_evidence
            if e.final_rank_score is not None and e.final_rank_score >= self.min_rank_threshold
        ]
        
        return filtered_evidence
    
    def calculate_relevance(self, evidence: EvidencePiece, claim: AtomicClaim) -> float:
        """Calculate relevance score for evidence relative to claim
        
        This is a simplified implementation that uses keyword matching.
        In production, this would use semantic similarity (embeddings, LLM scoring, etc.)
        
        Args:
            evidence: Evidence piece to score
            claim: Atomic claim being verified
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Normalize text for comparison
        claim_text = claim.text.lower()
        evidence_text = (evidence.summary + " " + evidence.raw_content).lower()
        
        # Extract keywords from claim (simple word splitting)
        claim_words = set(claim_text.split())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}
        claim_keywords = claim_words - stop_words
        
        if not claim_keywords:
            return 0.5  # Neutral score if no keywords
        
        # Count keyword matches
        matches = sum(1 for keyword in claim_keywords if keyword in evidence_text)
        
        # Calculate relevance as proportion of keywords found
        relevance = matches / len(claim_keywords)
        
        # Ensure score is in [0, 1]
        return min(1.0, max(0.0, relevance))
    
    def calculate_credibility(self, source: Source) -> float:
        """Calculate credibility score for a source
        
        Uses domain-based credibility with tier system and historical factors.
        
        Args:
            source: Source to score
            
        Returns:
            Credibility score between 0.0 and 1.0
        """
        # Get base credibility from domain database
        domain = source.domain.lower()
        
        # Check if domain has historical credibility factors
        if domain in self.DOMAIN_FACTORS_DB:
            domain_factors = self.DOMAIN_FACTORS_DB[domain]
            base_credibility = domain_factors.calculate_overall()
        elif domain in self.DOMAIN_CREDIBILITY_DB:
            base_credibility = self.DOMAIN_CREDIBILITY_DB[domain]
        else:
            # Unknown domain: infer credibility from TLD and patterns
            base_credibility = self._infer_domain_credibility(domain)
        
        # Ensure score is in [0, 1]
        return min(1.0, max(0.0, base_credibility))
    
    def _infer_domain_credibility(self, domain: str) -> float:
        """Infer credibility for unknown domains based on TLD and patterns
        
        Args:
            domain: Domain name to analyze
            
        Returns:
            Inferred credibility score
        """
        # Check if subdomain matches a known domain
        # e.g., "en.wikipedia.org" should match "wikipedia.org"
        parts = domain.split('.')
        if len(parts) > 2:
            # Try parent domain (last two parts)
            parent_domain = '.'.join(parts[-2:])
            if parent_domain in self.DOMAIN_CREDIBILITY_DB:
                return self.DOMAIN_CREDIBILITY_DB[parent_domain]
            
            # Try with subdomain removed (e.g., "www.example.com" -> "example.com")
            if parts[0] in ['www', 'en', 'fr', 'de', 'es', 'it', 'pt', 'ja', 'zh', 'm', 'mobile']:
                base_domain = '.'.join(parts[1:])
                if base_domain in self.DOMAIN_CREDIBILITY_DB:
                    return self.DOMAIN_CREDIBILITY_DB[base_domain]
        
        # Check for high-credibility TLDs
        if domain.endswith('.gov'):
            return 0.85
        if domain.endswith('.edu'):
            return 0.82
        if domain.endswith('.ac.uk') or domain.endswith('.edu.au'):
            return 0.82
        if domain.endswith('.mil'):  # Military
            return 0.85
        if domain.endswith('.int'):  # International organizations
            return 0.85
        
        # Check for official/organizational TLDs
        if domain.endswith('.org'):
            # .org can be high or low credibility, check keywords
            if any(keyword in domain for keyword in ['wikipedia', 'mozilla', 'apache', 'python', 'nodejs']):
                return 0.75
            return 0.55  # Neutral for unknown .org
        
        # Check for low-credibility indicators
        low_cred_keywords = ['blog', 'wordpress', 'blogspot', 'tumblr', 'wix', 'weebly', 'squarespace']
        if any(keyword in domain for keyword in low_cred_keywords):
            return 0.30
        
        # Check for social media patterns
        social_keywords = ['facebook', 'twitter', 'instagram', 'tiktok', 'reddit', 'snapchat', 'linkedin']
        if any(keyword in domain for keyword in social_keywords):
            return 0.20
        
        # Check for commercial/shop indicators (lower credibility for facts)
        shop_keywords = ['shop', 'store', 'buy', 'sell', 'market', 'cart', 'checkout']
        if any(keyword in domain for keyword in shop_keywords):
            return 0.25
        
        # Check for news indicators (moderate credibility for unknown news sites)
        news_keywords = ['news', 'times', 'post', 'herald', 'tribune', 'gazette', 'journal']
        if any(keyword in domain for keyword in news_keywords):
            return 0.55
        
        # Check for wiki/encyclopedia patterns
        if 'wiki' in domain or 'encyclopedia' in domain or 'britannica' in domain:
            return 0.65
        
        # Check for academic/research patterns
        academic_keywords = ['research', 'journal', 'academic', 'scholar', 'university', 'college']
        if any(keyword in domain for keyword in academic_keywords):
            return 0.70
        
        # Default for unknown domains: slightly below neutral (conservative)
        return 0.45
    
    def calculate_recency_score(
        self,
        publish_date: Optional[datetime],
        claim_date: datetime,
    ) -> float:
        """Calculate recency score based on how recent the evidence is
        
        More recent evidence (closer to claim date) receives higher scores.
        Uses exponential decay with a half-life of 180 days.
        
        Args:
            publish_date: When the evidence was published (None if unknown)
            claim_date: Date of the claim
            
        Returns:
            Recency score between 0.0 and 1.0
        """
        if publish_date is None:
            # Unknown publish date: use neutral score
            return 0.5
        
        # Calculate days between publish date and claim date
        days_diff = (claim_date - publish_date).days
        
        # Handle edge cases
        if days_diff < 0:
            # Future date (should not happen after temporal filtering)
            return 0.0
        if days_diff == 0:
            # Same day: maximum recency
            return 1.0
        
        # Exponential decay with half-life of 180 days
        half_life = 180.0
        recency = 2 ** (-days_diff / half_life)
        
        # Ensure score is in [0, 1]
        return min(1.0, max(0.0, recency))
    
    def get_domain_credibility(self, domain: str) -> float:
        """Get credibility score for a domain
        
        This is a convenience method for accessing domain credibility.
        
        Args:
            domain: Domain name
            
        Returns:
            Credibility score between 0.0 and 1.0
        """
        domain_lower = domain.lower()
        
        # Check historical factors first
        if domain_lower in self.DOMAIN_FACTORS_DB:
            return self.DOMAIN_FACTORS_DB[domain_lower].calculate_overall()
        
        # Then check simple credibility database
        if domain_lower in self.DOMAIN_CREDIBILITY_DB:
            return self.DOMAIN_CREDIBILITY_DB[domain_lower]
        
        # Unknown domain: neutral score
        return 0.5
    
    @classmethod
    def add_domain_credibility(cls, domain: str, credibility: float):
        """Add or update domain credibility in the database
        
        Args:
            domain: Domain name
            credibility: Credibility score (0.0 to 1.0)
        """
        cls.DOMAIN_CREDIBILITY_DB[domain.lower()] = credibility
    
    @classmethod
    def add_domain_factors(cls, domain: str, factors: DomainCredibility):
        """Add or update domain credibility factors in the database
        
        Args:
            domain: Domain name
            factors: DomainCredibility object with historical factors
        """
        cls.DOMAIN_FACTORS_DB[domain.lower()] = factors
