"""Confidence Scorer for KEPLER system

This module calculates confidence scores for fact-checking verdicts based on
source reliability, model agreement, and evidence recency.
"""
from typing import List
from datetime import datetime
from src.models.data_models import (
    ConsensusVerdict,
    ConfidenceScore,
    EvidencePiece,
    StructuredJustification,
    ReasoningChain,
    Verdict,
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
    ) -> ConfidenceScore:
        """Calculate confidence score for a consensus verdict
        
        Combines three factors:
        - Source reliability (35%): Quality of evidence sources
        - Model agreement (40%): Consensus among LLMs
        - Evidence recency (25%): How recent the evidence is
        
        Args:
            consensus: The consensus verdict from multiple models
            evidence: List of evidence pieces used in verification
            reasoning_chain: The reasoning chain from aggregation
            
        Returns:
            ConfidenceScore with overall score and component factors
        """
        # Calculate component scores
        source_reliability = self.assess_source_reliability(evidence)
        model_agreement = self.assess_model_agreement(consensus.individual_verdicts)
        evidence_recency = self.assess_evidence_recency(evidence)
        
        # Calculate overall confidence using weighted formula
        # confidence = (0.35 * source_reliability) + (0.40 * model_agreement) + (0.25 * evidence_recency)
        overall_score = (
            0.35 * source_reliability +
            0.40 * model_agreement +
            0.25 * evidence_recency
        )
        
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
    
    def assess_source_reliability(self, evidence: List[EvidencePiece]) -> float:
        """Assess the reliability of evidence sources
        
        Calculates average credibility score across all evidence pieces.
        If no evidence or no credibility scores, returns neutral 0.5.
        
        Args:
            evidence: List of evidence pieces with credibility scores
            
        Returns:
            Source reliability score between 0.0 and 1.0
        """
        if not evidence:
            return 0.5  # Neutral score for no evidence
        
        # Collect credibility scores
        credibility_scores = [
            e.credibility_score
            for e in evidence
            if e.credibility_score is not None
        ]
        
        if not credibility_scores:
            return 0.5  # Neutral score if no credibility scores available
        
        # Return average credibility
        return sum(credibility_scores) / len(credibility_scores)
    
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
    
    def assess_evidence_recency(self, evidence: List[EvidencePiece]) -> float:
        """Assess the recency of evidence
        
        More recent evidence receives higher scores. Uses exponential decay
        based on age of evidence.
        
        Args:
            evidence: List of evidence pieces with publish dates
            
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
            
            # Use exponential decay: score = e^(-age/365)
            # This gives ~0.37 for 1-year-old evidence, ~0.14 for 2-year-old
            import math
            recency_score = math.exp(-age_days / 365.0)
            recency_scores.append(recency_score)
        
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
