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
        # Tier 1: Academic and peer-reviewed
        'arxiv.org': 0.95,
        'nature.com': 0.98,
        'science.org': 0.98,
        'ieee.org': 0.95,
        'acm.org': 0.95,
        'springer.com': 0.92,
        'sciencedirect.com': 0.92,
        
        # Tier 2: Verified news sources
        'reuters.com': 0.85,
        'apnews.com': 0.85,
        'bbc.com': 0.82,
        'bbc.co.uk': 0.82,
        'npr.org': 0.80,
        'pbs.org': 0.80,
        
        # Tier 3: General news and established sources
        'nytimes.com': 0.75,
        'washingtonpost.com': 0.75,
        'theguardian.com': 0.72,
        'cnn.com': 0.68,
        'forbes.com': 0.65,
        'techcrunch.com': 0.60,
        
        # Tier 4: Blogs and social media
        'medium.com': 0.35,
        'blogger.com': 0.30,
        'wordpress.com': 0.30,
        'twitter.com': 0.25,
        'facebook.com': 0.20,
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
            # Unknown domain: use neutral default (conservative approach)
            base_credibility = 0.5
        
        # Ensure score is in [0, 1]
        return min(1.0, max(0.0, base_credibility))
    
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
