"""Reranker Agent for KEPLER system

This module handles the filtering and prioritization of retrieved evidence based on
relevance, credibility, and recency. It implements a multi-factor ranking system
with credibility tiers and domain credibility calculations.

It supports both:
- Keyword-based relevance scoring (default, lightweight).
- Optional embedding-based relevance scoring (semantic), via an injected scorer.
"""
from typing import List, Dict, Optional, Callable, Sequence
from datetime import datetime
import math
import re
from urllib.parse import urlparse
from src.models.data_models import EvidencePiece, AtomicClaim, Source, DomainCredibility
from src.config import config  # kept for compatibility / future config-driven tuning

Vector = Sequence[float]


class EmbeddingRelevanceScorer:
    """Helper for embedding-based semantic relevance scoring.
    
    You provide an embedding function (e.g., OpenAI, Bedrock, SentenceTransformers)
    and this class handles cosine similarity + normalization to [0.0, 1.0].
    
    Example (pseudocode):
        def embed_text(text: str) -> List[float]:
            return external_embedding_client.embed(text)
        
        scorer = EmbeddingRelevanceScorer(embed_fn=embed_text)
        score = scorer.score("claim text", "evidence text")
    """
    
    def __init__(
        self,
        embed_fn: Callable[[str], Vector],
        *,
        normalize_vectors: bool = True,
    ):
        """
        Args:
            embed_fn: Function that maps text -> embedding vector (Sequence[float]).
            normalize_vectors: If True, explicitly normalize vectors internally.
                If your embed_fn already returns normalized vectors,
                you can set this to False for a tiny speedup.
        """
        self.embed_fn = embed_fn
        self.normalize_vectors = normalize_vectors
    
    def _l2_norm(self, v: Vector) -> float:
        return math.sqrt(sum(x * x for x in v))
    
    def _cosine_similarity(self, v1: Vector, v2: Vector) -> float:
        if not v1 or not v2:
            return 0.0
        
        if self.normalize_vectors:
            norm1 = self._l2_norm(v1)
            norm2 = self._l2_norm(v2)
            if norm1 == 0.0 or norm2 == 0.0:
                return 0.0
            dot = sum(a * b for a, b in zip(v1, v2))
            return dot / (norm1 * norm2)
        
        # Assume they are already normalized
        dot = sum(a * b for a, b in zip(v1, v2))
        # In practice, this should already be in [-1, 1], but clamp anyway
        return max(-1.0, min(1.0, dot))
    
    def score(self, claim_text: str, evidence_text: str) -> float:
        """Compute semantic relevance between claim and evidence in [0.0, 1.0]."""
        claim_text = (claim_text or "").strip()
        evidence_text = (evidence_text or "").strip()
        
        if not claim_text or not evidence_text:
            return 0.0
        
        claim_emb = self.embed_fn(claim_text)
        evid_emb = self.embed_fn(evidence_text)
        
        cos_sim = self._cosine_similarity(claim_emb, evid_emb)
        
        # Map from [-1, 1] to [0, 1]
        score = (cos_sim + 1.0) / 2.0
        return min(1.0, max(0.0, score))


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
        "arxiv.org": 0.95,
        "nature.com": 0.98,
        "science.org": 0.98,
        "ieee.org": 0.95,
        "acm.org": 0.95,
        "springer.com": 0.92,
        "sciencedirect.com": 0.92,
        "wikipedia.org": 0.88,  # High credibility for factual claims
        "en.wikipedia.org": 0.88,
        "britannica.com": 0.90,
        "nasa.gov": 0.98,
        "nih.gov": 0.95,
        "cdc.gov": 0.95,
        "who.int": 0.95,
        "un.org": 0.90,
        
        # Official/Authoritative sources (0.85-0.95)
        "toureiffel.paris": 0.92,  # Official Eiffel Tower site
        "louvre.fr": 0.92,  # Official Louvre site
        "whitehouse.gov": 0.90,
        "europa.eu": 0.90,
        "gov.uk": 0.88,
        "canada.ca": 0.88,
        
        # General government/educational domains (0.80-0.88)
        "gov": 0.85,  # General government domains
        "edu": 0.82,  # General educational domains
        "ac.uk": 0.82,  # UK academic
        "edu.au": 0.82,  # Australian academic
        
        # Tier 2: Verified news sources (0.75-0.85)
        "reuters.com": 0.85,
        "apnews.com": 0.85,
        "bbc.com": 0.82,
        "bbc.co.uk": 0.82,
        "npr.org": 0.80,
        "pbs.org": 0.80,
        "economist.com": 0.78,
        "ft.com": 0.78,  # Financial Times
        
        # Tier 3: General news and established sources (0.60-0.75)
        "nytimes.com": 0.75,
        "washingtonpost.com": 0.75,
        "theguardian.com": 0.72,
        "wsj.com": 0.72,  # Wall Street Journal
        "cnn.com": 0.68,
        "forbes.com": 0.65,
        "techcrunch.com": 0.60,
        "wired.com": 0.62,
        "nationalgeographic.com": 0.70,
        
        # Tier 4: Educational/Reference sites (0.45-0.65)
        "khanacademy.org": 0.65,
        "coursera.org": 0.60,
        "edx.org": 0.60,
        "merriam-webster.com": 0.65,
        "dictionary.com": 0.55,
        
        # Tier 5: Q&A and homework sites (0.35-0.50)
        "stackoverflow.com": 0.55,  # Technical Q&A
        "stackexchange.com": 0.50,
        "quora.com": 0.40,
        "brainly.com": 0.35,  # Homework help
        "chegg.com": 0.35,  # Homework help
        "gauthmath.com": 0.35,  # Homework help
        
        # Tier 6: Blogs, forums, and social media (0.15-0.35)
        "medium.com": 0.35,
        "blogger.com": 0.30,
        "wordpress.com": 0.30,
        "reddit.com": 0.25,
        "twitter.com": 0.20,
        "x.com": 0.20,  # Twitter/X
        "facebook.com": 0.15,
        "instagram.com": 0.15,
        "tiktok.com": 0.10,
        "flickr.com": 0.30,  # Photo sharing
        
        # Tier 7: Low credibility - satire, jokes, unreliable (0.05-0.20)
        "theonion.com": 0.05,  # Satire
        "clickhole.com": 0.05,  # Satire
        "babylonbee.com": 0.05,  # Satire
        "reasons.org": 0.15,  # Advocacy/apologetics site
        "cheeseprofessor.com": 0.20,  # Blog
        "snackstack.net": 0.20,  # Blog
        "mentalfloss.com": 0.40,  # Entertainment/trivia
        "smartdoll.jp": 0.10,  # E-commerce
    }
    
    # Domain credibility factors database (for historical analysis)
    DOMAIN_FACTORS_DB: Dict[str, DomainCredibility] = {}
    
    # Cache for inferred domain scores to avoid repeated computation
    _INFERRED_DOMAIN_CACHE: Dict[str, float] = {}
    
    def __init__(
        self,
        relevance_weight: float = 0.4,
        credibility_weight: float = 0.4,
        recency_weight: float = 0.2,
        min_rank_threshold: float = 0.3,
        embedding_scorer: Optional[EmbeddingRelevanceScorer] = None,
    ):
        """Initialize the Reranker Agent
        
        Args:
            relevance_weight: Weight for relevance score in ranking formula
            credibility_weight: Weight for credibility score in ranking formula
            recency_weight: Weight for recency score in ranking formula
            min_rank_threshold: Minimum rank score to pass evidence to next stage
            embedding_scorer: Optional EmbeddingRelevanceScorer for semantic relevance.
                If None, fallback to keyword-based relevance only.
        """
        # Normalize weights so they always sum to 1.0 (in case of misconfiguration)
        total = relevance_weight + credibility_weight + recency_weight
        if total <= 0:
            # Fallback to equal weights if something weird is passed in
            relevance_weight = credibility_weight = recency_weight = 1.0 / 3.0
            total = 1.0
        
        self.relevance_weight = relevance_weight / total
        self.credibility_weight = credibility_weight / total
        self.recency_weight = recency_weight / total
        self.min_rank_threshold = min_rank_threshold
        
        # Default recency half-life in days; can be overridden after init if needed
        self.recency_half_life_days = 180.0
        
        # Optional embedding-based semantic relevance scorer
        self.embedding_scorer = embedding_scorer
    
    def rank_evidence(
        self,
        evidence: List[EvidencePiece],
        claim: AtomicClaim,
    ) -> List[EvidencePiece]:
        """Rank evidence based on relevance, credibility, and recency."""
        now = datetime.now()
        
        for piece in evidence:
            # Relevance
            piece.relevance_score = self.calculate_relevance(piece, claim)
            
            # Credibility
            piece.credibility_score = self.calculate_credibility(piece.source)
            
            # Recency (relative to "now"; could be changed to claim.timestamp if available)
            piece.recency_score = self.calculate_recency_score(
                piece.source.publish_date,
                now,
            )
            
            # Final combined rank
            piece.final_rank_score = (
                self.relevance_weight * piece.relevance_score
                + self.credibility_weight * piece.credibility_score
                + self.recency_weight * piece.recency_score
            )
        
        # Sort by final rank score (descending)
        ranked_evidence = sorted(
            evidence,
            key=lambda e: e.final_rank_score if e.final_rank_score is not None else 0.0,
            reverse=True,
        )
        
        # Filter out low-ranked evidence
        filtered_evidence = [
            e
            for e in ranked_evidence
            if e.final_rank_score is not None
            and e.final_rank_score >= self.min_rank_threshold
        ]
        
        return filtered_evidence
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Simple tokenizer: extracts word-like tokens, lowercased."""
        return re.findall(r"\w+", text.lower())
    
    def calculate_relevance(self, evidence: EvidencePiece, claim: AtomicClaim) -> float:
        """Calculate relevance score for evidence relative to claim.
        
        If an embedding_scorer is configured, we first attempt semantic relevance.
        If that fails (or is not provided), we fall back to keyword-based relevance.
        """
        claim_text = (claim.text or "").strip()
        summary = evidence.summary or ""
        raw = evidence.raw_content or ""
        evidence_text = f"{summary} {raw}".strip()
        
        # 1) Try embedding-based semantic relevance if available
        if self.embedding_scorer is not None:
            try:
                semantic_score = self.embedding_scorer.score(claim_text, evidence_text)
                # If the score is valid, use it directly
                if 0.0 <= semantic_score <= 1.0:
                    return semantic_score
            except Exception:
                # If embedding scoring fails for any reason, fall through to keyword-based
                pass
        
        # 2) Fallback: keyword-based relevance (previous behavior, improved tokenization)
        claim_tokens = set(self._tokenize_text(claim_text))
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "is", "are", "was", "were",
        }
        claim_keywords = claim_tokens - stop_words
        
        if not claim_keywords:
            # If we can't extract any meaningful keywords, return a neutral score
            return 0.5
        
        evidence_tokens = set(self._tokenize_text(evidence_text))
        matches = sum(1 for keyword in claim_keywords if keyword in evidence_tokens)
        relevance = matches / len(claim_keywords)
        
        return min(1.0, max(0.0, relevance))
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain string.
        
        Handles cases where 'domain' might actually be a full URL.
        """
        domain = (domain or "").strip().lower()
        if not domain:
            return ""
        
        # If it's a URL, extract netloc
        parsed = urlparse(domain)
        if parsed.netloc:
            domain = parsed.netloc
        
        # Remove common leading 'www.'
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    
    def _get_base_domain_credibility(self, domain: str) -> float:
        """Get the base credibility for a domain, using DB and inference."""
        domain = self._normalize_domain(domain)
        if not domain:
            # Totally unknown / empty domain, slightly below neutral
            return 0.45
        
        # Historical factor-based credibility
        factors = self.DOMAIN_FACTORS_DB.get(domain)
        if factors is not None:
            return factors.calculate_overall()
        
        # Direct database hit
        if domain in self.DOMAIN_CREDIBILITY_DB:
            return self.DOMAIN_CREDIBILITY_DB[domain]
        
        # Cached inferred score
        if domain in self._INFERRED_DOMAIN_CACHE:
            return self._INFERRED_DOMAIN_CACHE[domain]
        
        # Need to infer
        inferred = self._infer_domain_credibility(domain)
        self._INFERRED_DOMAIN_CACHE[domain] = inferred
        return inferred
    
    def calculate_credibility(self, source: Source) -> float:
        """Calculate credibility score for a source."""
        base_credibility = self._get_base_domain_credibility(source.domain)
        return min(1.0, max(0.0, base_credibility))
    
    def _infer_domain_credibility(self, domain: str) -> float:
        """Infer credibility for unknown domains based on TLD and patterns."""
        parts = domain.split(".")
        
        # Check if subdomain matches a known domain
        # e.g., "en.wikipedia.org" -> "wikipedia.org"
        if len(parts) > 2:
            parent_domain = ".".join(parts[-2:])
            if parent_domain in self.DOMAIN_CREDIBILITY_DB:
                return self.DOMAIN_CREDIBILITY_DB[parent_domain]
            
            # Try stripping common language / mobile subdomains
            if parts[0] in [
                "www", "en", "fr", "de", "es", "it", "pt", "ja", "zh", "m", "mobile",
            ]:
                base_domain = ".".join(parts[1:])
                if base_domain in self.DOMAIN_CREDIBILITY_DB:
                    return self.DOMAIN_CREDIBILITY_DB[base_domain]
        
        # High-credibility TLDs
        if domain.endswith(".gov"):
            return 0.85
        if domain.endswith(".edu"):
            return 0.82
        if domain.endswith(".ac.uk") or domain.endswith(".edu.au"):
            return 0.82
        if domain.endswith(".mil"):  # Military
            return 0.85
        if domain.endswith(".int"):  # International organizations
            return 0.85
        
        # Official/organizational TLDs
        if domain.endswith(".org"):
            # .org can be high or low credibility, check keywords
            if any(
                keyword in domain
                for keyword in ["wikipedia", "mozilla", "apache", "python", "nodejs"]
            ):
                return 0.75
            return 0.55  # Neutral-ish for unknown .org
        
        # Low-credibility indicators
        low_cred_keywords = [
            "blog", "wordpress", "blogspot", "tumblr", "wix", "weebly", "squarespace",
        ]
        if any(keyword in domain for keyword in low_cred_keywords):
            return 0.30
        
        # Social media patterns
        social_keywords = [
            "facebook", "twitter", "instagram", "tiktok", "reddit", "snapchat", "linkedin",
        ]
        if any(keyword in domain for keyword in social_keywords):
            return 0.20
        
        # Commercial/shop indicators (lower credibility for factual claims)
        shop_keywords = ["shop", "store", "buy", "sell", "market", "cart", "checkout"]
        if any(keyword in domain for keyword in shop_keywords):
            return 0.25
        
        # News indicators (moderate credibility for unknown news sites)
        news_keywords = [
            "news", "times", "post", "herald", "tribune", "gazette", "journal",
        ]
        if any(keyword in domain for keyword in news_keywords):
            return 0.55
        
        # Wiki/encyclopedia patterns
        if (
            "wiki" in domain
            or "encyclopedia" in domain
            or "britannica" in domain
        ):
            return 0.65
        
        # Academic/research patterns
        academic_keywords = [
            "research", "journal", "academic", "scholar", "university", "college",
        ]
        if any(keyword in domain for keyword in academic_keywords):
            return 0.70
        
        # Default for unknown domains: slightly below neutral (conservative)
        return 0.45
    
    def calculate_recency_score(
        self,
        publish_date: Optional[datetime],
        reference_date: datetime,
    ) -> float:
        """Calculate recency score based on how recent the evidence is."""
        if publish_date is None:
            # Unknown publish date: use neutral score
            return 0.5
        
        days_diff = (reference_date - publish_date).days
        
        # Handle edge cases
        if days_diff < 0:
            # Future date (should not happen after temporal filtering)
            return 0.0
        if days_diff == 0:
            # Same day: maximum recency
            return 1.0
        
        # Exponential decay with configurable half-life
        half_life = (
            float(self.recency_half_life_days)
            if self.recency_half_life_days > 0
            else 180.0
        )
        recency = 2 ** (-days_diff / half_life)
        
        return min(1.0, max(0.0, recency))
    
    def get_domain_credibility(self, domain: str) -> float:
        """Get credibility score for a domain."""
        base_credibility = self._get_base_domain_credibility(domain)
        return min(1.0, max(0.0, base_credibility))
    
    @classmethod
    def add_domain_credibility(cls, domain: str, credibility: float):
        """Add or update domain credibility in the database."""
        normalized = domain.strip().lower()
        cls.DOMAIN_CREDIBILITY_DB[normalized] = credibility
        # Also clear any cached inferred value for this domain
        cls._INFERRED_DOMAIN_CACHE.pop(normalized, None)
    
    @classmethod
    def add_domain_factors(cls, domain: str, factors: DomainCredibility):
        """Add or update domain credibility factors in the database."""
        normalized = domain.strip().lower()
        cls.DOMAIN_FACTORS_DB[normalized] = factors
        # Clear any cached inferred value, since we now have explicit factors
        cls._INFERRED_DOMAIN_CACHE.pop(normalized, None)
