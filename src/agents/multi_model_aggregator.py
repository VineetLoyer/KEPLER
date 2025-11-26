"""Multi-Model Aggregator for KEPLER system

This module handles the aggregation of individual model verdicts into a consensus
verdict using majority voting and justification summarization.
"""
from typing import List, Dict
from collections import Counter
import logging
from src.models.data_models import (
    Verdict,
    ConsensusVerdict,
    VerdictType,
)

logger = logging.getLogger(__name__)


class MultiModelAggregator:
    """Agent responsible for aggregating multiple model verdicts into consensus"""
    
    def __init__(self):
        """Initialize the Multi-Model Aggregator"""
        pass
    
    def aggregate_verdicts(self, verdicts: List[Verdict]) -> ConsensusVerdict:
        """Aggregate individual model verdicts into a consensus verdict
        
        This method:
        1. Uses majority voting to determine the final classification
        2. Aggregates justifications from all models
        3. Calculates agreement level across models
        
        Args:
            verdicts: List of individual model verdicts
            
        Returns:
            ConsensusVerdict with final classification and aggregated justification
            
        Raises:
            ValueError: If verdicts list is empty
        """
        if not verdicts:
            error_msg = "Cannot aggregate empty list of verdicts"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Determine final classification using majority voting
            final_classification = self.majority_poll(verdicts)
            
            # Log tie-breaking if it occurred
            classification_counts = Counter(v.classification for v in verdicts)
            most_common = classification_counts.most_common()
            if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                logger.warning(
                    f"Tie detected in verdict aggregation. "
                    f"Defaulting to NOT_ENOUGH_INFO. "
                    f"Counts: {dict(classification_counts)}"
                )
            
            # Aggregate justifications
            consensus_justification = self.aggregate_justifications(verdicts)
            
            # Calculate agreement level
            agreement_level = self._calculate_agreement_level(verdicts, final_classification)
            
            logger.info(
                f"Verdict aggregation complete: {final_classification.value}, "
                f"agreement={agreement_level:.2f}, num_verdicts={len(verdicts)}"
            )
            
            return ConsensusVerdict(
                final_classification=final_classification,
                consensus_justification=consensus_justification,
                individual_verdicts=verdicts,
                agreement_level=agreement_level,
            )
        except Exception as e:
            logger.exception(f"Error during verdict aggregation: {str(e)}")
            raise
    
    def majority_poll(self, verdicts: List[Verdict]) -> VerdictType:
        """Determine consensus classification using majority voting
        
        Uses simple majority voting with tie-breaking:
        - If there's a clear majority, return that classification
        - If there's a tie, default to "Not Enough Information"
        
        Args:
            verdicts: List of individual model verdicts
            
        Returns:
            VerdictType representing the majority classification
        """
        if not verdicts:
            logger.warning("Empty verdicts list in majority_poll, defaulting to NOT_ENOUGH_INFO")
            return VerdictType.NOT_ENOUGH_INFO
        
        # Count classifications
        classification_counts = Counter(v.classification for v in verdicts)
        
        # Get the most common classification(s)
        most_common = classification_counts.most_common()
        
        # Check for tie
        if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
            # Tie detected - default to NOT_ENOUGH_INFO
            logger.info(
                f"Tie-breaking: Multiple classifications with equal votes. "
                f"Defaulting to NOT_ENOUGH_INFO. Counts: {dict(classification_counts)}"
            )
            return VerdictType.NOT_ENOUGH_INFO
        
        # Return the most common classification
        return most_common[0][0]
    
    def aggregate_justifications(self, verdicts: List[Verdict]) -> str:
        """Aggregate individual justifications into a consensus justification
        
        This method summarizes the justifications from all models into a
        concise, human-readable consensus justification that reflects the
        dominant reasoning across the ensemble.
        
        In a production system, this would use a lightweight LLM for
        summarization. For now, we extract common themes and combine them.
        
        Args:
            verdicts: List of individual model verdicts
            
        Returns:
            Aggregated justification string
        """
        if not verdicts:
            return "No verdicts available for aggregation."
        
        # Group justifications by classification
        justifications_by_class: Dict[VerdictType, List[str]] = {}
        for verdict in verdicts:
            if verdict.classification not in justifications_by_class:
                justifications_by_class[verdict.classification] = []
            justifications_by_class[verdict.classification].append(verdict.justification)
        
        # Get the final classification (from majority_poll)
        final_classification = self.majority_poll(verdicts)
        
        # Check if this is a tie situation (final is NOT_ENOUGH_INFO but no model said that)
        is_tie = (
            final_classification == VerdictType.NOT_ENOUGH_INFO and
            VerdictType.NOT_ENOUGH_INFO not in justifications_by_class
        )
        
        if is_tie:
            # Handle tie case specially - be concise
            classifications = list(justifications_by_class.keys())
            class_str = " and ".join(cls.value for cls in classifications)
            return f"Models are evenly split between {class_str}. Unable to reach consensus."
        
        # Get justifications for the final classification
        if final_classification in justifications_by_class:
            dominant_justifications = justifications_by_class[final_classification]
        else:
            # Fallback - shouldn't happen but handle gracefully
            dominant_justifications = list(justifications_by_class.values())[0]
        
        # Create a summarized justification
        # In production, this would use an LLM for better summarization
        num_models = len(verdicts)
        num_agreeing = len(dominant_justifications)
        
        # Build consensus summary - keep it concise
        if num_agreeing == num_models:
            # Unanimous - just use one justification
            return dominant_justifications[0]
        else:
            # Majority - add brief context then one justification
            summary = f"{num_agreeing}/{num_models} models: "
            
            # Add a representative justification (simplified approach)
            # In production, an LLM would extract common themes and synthesize them
            representative_justification = dominant_justifications[0]
            
            # Truncate if too long
            max_length = 200
            if len(representative_justification) > max_length:
                representative_justification = representative_justification[:max_length] + "..."
            
            summary += representative_justification
            
            return summary
    
    def _calculate_agreement_level(
        self,
        verdicts: List[Verdict],
        final_classification: VerdictType,
    ) -> float:
        """Calculate the agreement level across models
        
        Agreement level is the percentage of models that agree with the
        final classification.
        
        Args:
            verdicts: List of individual model verdicts
            final_classification: The final consensus classification
            
        Returns:
            Agreement level as a float between 0.0 and 1.0
        """
        if not verdicts:
            return 0.0
        
        agreeing_count = sum(
            1 for v in verdicts
            if v.classification == final_classification
        )
        
        return agreeing_count / len(verdicts)
