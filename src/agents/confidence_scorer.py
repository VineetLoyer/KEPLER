"""Confidence Scorer for KEPLER system

This module calculates confidence scores for fact-checking verdicts based on
source reliability, model agreement, and evidence recency.
"""
from typing import List
from datetime import datetime
import math
from src.models.data_models import (
    ConsensusVerdict,
    ConfidenceScore,
    EvidencePiece,
    StructuredJustification,
    ReasoningChain,
    Verdict,
    AtomicClaim,
)


class ConfidenceScorer:
    """Agent responsible for calculating confidence scores for verdicts"""
    
    def __init__(self):
        """Initialize the Confidence Scorer"""
        pass
    
    def calculate_confidence(
        self,
        consensus: ConsensusVerdict,
        evidence: List[EvidencePiece],
        reasoning_chain: ReasoningChain,
        claim: AtomicClaim,
    ) -> ConfidenceScore:
        """Calculate confidence score for a consensus verdict with context-aware weighting
        
        Combines three factors with weights adjusted by claim type:
        - Source reliability: Quality of evidence sources
        - Model agreement: Consensus among LLMs
        - Evidence recency: How recent the evidence is
        
        Args:
            consensus: The consensus verdict from multiple models
            evidence: List of evidence pieces used in verification
            reasoning_chain: The reasoning chain from aggregation
            claim: The atomic claim being verified (for type detection)
            
        Returns:
            ConfidenceScore with overall score and component factors
        """
        # Detect claim type for context-aware scoring
        claim_type = self.detect_claim_type(claim, evidence)
        
        # Calculate component scores
        source_reliability = self.assess_source_reliability(evidence, claim_type)
        model_agreement = self.assess_model_agreement(consensus.individual_verdicts)
        evidence_recency = self.assess_evidence_recency(evidence, claim_type)
        
        # Adjust weights based on claim type
        if claim_type == "scientific":
            # For scientific claims: prioritize source reliability and model agreement
            weights = {
                'source': 0.50,  # Increased from 0.35
                'agreement': 0.40,
                'recency': 0.10,  # Decreased from 0.25
            }
        elif claim_type == "current_event":
            # For current events: prioritize recency and source reliability
            weights = {
                'source': 0.35,
                'agreement': 0.30,
                'recency': 0.35,  # Increased from 0.25
            }
        else:  # general
            # Balanced weights
            weights = {
                'source': 0.35,
                'agreement': 0.40,
                'recency': 0.25,
            }
        
        # Calculate overall confidence
        overall_score = (
            weights['source'] * source_reliability +
            weights['agreement'] * model_agreement +
            weights['recency'] * evidence_recency
        )
        
        # Apply boost for high-quality scientific claims
        if claim_type == "scientific" and source_reliability > 0.9 and model_agreement > 0.8:
            overall_score = min(1.0, overall_score * 1.05)  # 5% boost, capped at 1.0
        
        # Create structured justification
        structured_justification = self._create_structured_justification(
            consensus,
            evidence,
            reasoning_chain,
        )
        
        return ConfidenceScore(
            overall_score=overall_score,
            source_reliability=source_reliability,
            model_agreement=model_agreement,
            evidence_recency=evidence_recency,
            structured_justification=structured_justification,
        )
    
    def detect_claim_type(self, claim: AtomicClaim, evidence: List[EvidencePiece]) -> str:
        """Detect whether claim is scientific, current event, or general
        
        Uses heuristics based on:
        - Claim text keywords
        - Source domains
        - Evidence content
        
        Args:
            claim: The atomic claim to classify
            evidence: Evidence pieces for the claim
            
        Returns:
            Claim type: "scientific", "current_event", or "general"
        """
        claim_lower = claim.text.lower()
        
        # Scientific indicators
        scientific_keywords = [
            'dna', 'molecule', 'atom', 'protein', 'cell', 'gene',
            'theory', 'equation', 'formula', 'chemical', 'physics',
            'biology', 'chemistry', 'scientific', 'research', 'study',
            'discovered', 'proven', 'structure', 'composition', 'element',
            'compound', 'reaction', 'experiment', 'hypothesis', 'law',
        ]
        
        # Current event indicators
        current_event_keywords = [
            'today', 'yesterday', 'this week', 'this month', 'recently',
            'announced', 'breaking', 'latest', 'current', 'now',
            'elected', 'appointed', 'resigned', 'died', 'born',
            '2024', '2025', 'just', 'new',
        ]
        
        # Check claim text
        scientific_count = sum(1 for kw in scientific_keywords if kw in claim_lower)
        current_event_count = sum(1 for kw in current_event_keywords if kw in claim_lower)
        
        # Check source domains
        scientific_domains = [
            'arxiv.org', 'nature.com', 'science.org', 'pubmed',
            'ncbi.nlm.nih.gov', 'sciencedirect.com', '.edu',
            'nih.gov', 'pnas.org', 'cell.com',
        ]
        
        news_domains = [
            'reuters.com', 'apnews.com', 'bbc.com', 'cnn.com',
            'nytimes.com', 'theguardian.com', 'washingtonpost.com',
            'news', 'today',
        ]
        
        scientific_sources = sum(
            1 for e in evidence
            if any(domain in e.source.domain for domain in scientific_domains)
        )
        
        news_sources = sum(
            1 for e in evidence
            if any(domain in e.source.domain for domain in news_domains)
        )
        
        # Decision logic
        if scientific_count >= 2 or (evidence and scientific_sources >= len(evidence) * 0.5):
            return "scientific"
        elif current_event_count >= 2 or (evidence and news_sources >= len(evidence) * 0.5):
            return "current_event"
        else:
            return "general"
    
    def assess_source_reliability(
        self,
        evidence: List[EvidencePiece],
        claim_type: str = "general"
    ) -> float:
        """Assess source reliability with authority weighting
        
        Calculates credibility score with authority boost for high-quality domains.
        
        Args:
            evidence: List of evidence pieces with credibility scores
            claim_type: Type of claim ("scientific", "current_event", "general")
            
        Returns:
            Source reliability score between 0.0 and 1.0
        """
        if not evidence:
            return 0.5  # Neutral score for no evidence
        
        # High-authority domains for scientific claims
        high_authority_scientific = {
            'nature.com': 1.0,
            'science.org': 1.0,
            'cell.com': 1.0,
            'pnas.org': 0.98,
            'arxiv.org': 0.95,
            'ncbi.nlm.nih.gov': 0.98,
            'pubmed': 0.98,
            'nih.gov': 0.97,
        }
        
        # High-authority domains for news
        high_authority_news = {
            'reuters.com': 0.95,
            'apnews.com': 0.95,
            'bbc.com': 0.92,
            'nytimes.com': 0.90,
        }
        
        reliability_scores = []
        
        for e in evidence:
            # Start with base credibility score
            if e.credibility_score is not None:
                base_score = e.credibility_score
            else:
                base_score = 0.5
            
            # Apply authority boost for scientific claims
            if claim_type == "scientific":
                for domain, authority in high_authority_scientific.items():
                    if domain in e.source.domain:
                        base_score = max(base_score, authority)
                        break
            
            # Apply authority boost for current events
            elif claim_type == "current_event":
                for domain, authority in high_authority_news.items():
                    if domain in e.source.domain:
                        base_score = max(base_score, authority)
                        break
            
            reliability_scores.append(base_score)
        
        if not reliability_scores:
            return 0.5
        
        # Use weighted average (top sources matter more)
        sorted_scores = sorted(reliability_scores, reverse=True)
        
        # Weight top 3 sources more heavily
        if len(sorted_scores) >= 3:
            weighted_score = (
                sorted_scores[0] * 0.5 +
                sorted_scores[1] * 0.3 +
                sorted_scores[2] * 0.2
            )
        elif len(sorted_scores) == 2:
            weighted_score = (
                sorted_scores[0] * 0.6 +
                sorted_scores[1] * 0.4
            )
        else:
            weighted_score = sorted_scores[0]
        
        return weighted_score
    
    def assess_model_agreement(self, verdicts: List[Verdict]) -> float:
        """Assess the level of agreement among models
        
        Uses the agreement level from consensus verdict calculation.
        Higher agreement = higher confidence.
        
        Args:
            verdicts: List of individual model verdicts
            
        Returns:
            Model agreement score between 0.0 and 1.0
        """
        if not verdicts:
            return 0.0
        
        # Count how many models agree with the most common classification
        from collections import Counter
        classification_counts = Counter(v.classification for v in verdicts)
        most_common_count = classification_counts.most_common(1)[0][1]
        
        # Agreement level is the proportion agreeing with majority
        return most_common_count / len(verdicts)
    
    def assess_evidence_recency(
        self,
        evidence: List[EvidencePiece],
        claim_type: str = "general"
    ) -> float:
        """Assess evidence recency with context awareness
        
        Different claim types have different recency requirements:
        - Scientific facts: Recency matters less (older = more established)
        - Current events: Recency matters most
        - General facts: Moderate recency importance
        
        Args:
            evidence: List of evidence pieces with publish dates
            claim_type: Type of claim ("scientific", "current_event", "general")
            
        Returns:
            Evidence recency score between 0.0 and 1.0
        """
        if not evidence:
            return 0.5  # Neutral score for no evidence
        
        # Collect evidence with publish dates
        dated_evidence = [
            e for e in evidence
            if e.source.publish_date is not None
        ]
        
        if not dated_evidence:
            return 0.5  # Neutral score if no dates available
        
        # Calculate recency scores for each piece
        current_time = datetime.now()
        recency_scores = []
        
        for e in dated_evidence:
            # Calculate age in days
            age_days = (current_time - e.source.publish_date).days
            
            if claim_type == "scientific":
                # For scientific claims, older = more established
                # Recent papers: 0.9, 1-5 years: 1.0 (peak), 5+ years: 0.95
                if age_days < 365:
                    score = 0.9  # Very recent, still being validated
                elif age_days < 1825:  # 1-5 years
                    score = 1.0  # Sweet spot: peer-reviewed and established
                else:
                    score = 0.95  # Older but still valid
            
            elif claim_type == "current_event":
                # For current events, recency is critical
                # Use steep exponential decay
                score = math.exp(-age_days / 180.0)  # Half-life of 6 months
            
            else:  # general
                # Moderate decay for general facts
                score = math.exp(-age_days / 730.0)  # Half-life of 2 years
            
            recency_scores.append(score)
        
        # Return average recency
        return sum(recency_scores) / len(recency_scores)
    
    def _create_structured_justification(
        self,
        consensus: ConsensusVerdict,
        evidence: List[EvidencePiece],
        reasoning_chain: ReasoningChain,
    ) -> StructuredJustification:
        """Create structured justification with source links
        
        Args:
            consensus: The consensus verdict
            evidence: List of evidence pieces
            reasoning_chain: The reasoning chain from aggregation
            
        Returns:
            StructuredJustification with summary, evidence, and source links
        """
        # Use consensus justification as summary
        summary = consensus.consensus_justification
        
        # Select key evidence (top-ranked pieces)
        key_evidence = self._select_key_evidence(evidence)
        
        # Extract source links from all evidence
        source_links = [e.source.url for e in evidence]
        
        return StructuredJustification(
            summary=summary,
            key_evidence=key_evidence,
            reasoning_chain=reasoning_chain,
            source_links=source_links,
        )
    
    def _select_key_evidence(
        self,
        evidence: List[EvidencePiece],
        max_pieces: int = 5,
    ) -> List[EvidencePiece]:
        """Select the most important evidence pieces
        
        Selects top-ranked evidence based on final_rank_score.
        
        Args:
            evidence: List of all evidence pieces
            max_pieces: Maximum number of pieces to select
            
        Returns:
            List of key evidence pieces
        """
        if not evidence:
            return []
        
        # Sort by final_rank_score (descending)
        sorted_evidence = sorted(
            evidence,
            key=lambda e: e.final_rank_score if e.final_rank_score is not None else 0.0,
            reverse=True,
        )
        
        # Return top pieces
        return sorted_evidence[:max_pieces]
