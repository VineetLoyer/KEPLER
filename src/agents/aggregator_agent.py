"""Aggregator Agent for KEPLER system
This module handles the synthesis of multimodal evidence and applies chain-of-thought
reasoning to consolidate text, images, and metadata. It identifies agreements, conflicts,
and information gaps in the evidence.
"""
from typing import List, Dict, Any, Optional
from src.models.data_models import (
    EvidencePiece,
    AtomicClaim,
    ConsolidatedEvidence,
    ReasoningChain,
    ReasoningStep,
    Agreement,
    Conflict,
    InformationGap,
)


class AggregatorAgent:
    """Agent responsible for synthesizing multimodal evidence and applying chain-of-thought reasoning"""
    
    def __init__(self, similarity_threshold: float = 0.7, conflict_threshold: float = 0.6):
        """Initialize the Aggregator Agent
        
        Args:
            similarity_threshold: Threshold for detecting agreements (0.0 to 1.0)
            conflict_threshold: Threshold for detecting conflicts (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.conflict_threshold = conflict_threshold
    
    def consolidate_evidence(self, evidence: List[EvidencePiece]) -> ConsolidatedEvidence:
        """Consolidate multimodal evidence into a unified representation
        
        This method:
        1. Separates evidence by type (text, images, other)
        2. Extracts metadata from all evidence
        3. Creates an evidence map linking claim aspects to supporting evidence
        
        Args:
            evidence: List of evidence pieces to consolidate
            
        Returns:
            ConsolidatedEvidence with organized textual, visual, and metadata
        """
        textual_evidence = []
        visual_evidence = []
        metadata = {}
        evidence_map: Dict[str, List[EvidencePiece]] = {}
        
        for piece in evidence:
            # Consolidate textual evidence
            if piece.source.content_type == 'text':
                # Use raw_content (full text) instead of summary for better verification
                # Limit to 2000 chars per piece to avoid overwhelming the LLM
                content = piece.raw_content[:2000] if len(piece.raw_content) > 2000 else piece.raw_content
                textual_evidence.append(content)
                
                # Add to evidence map by domain
                domain = piece.source.domain
                if domain not in evidence_map:
                    evidence_map[domain] = []
                evidence_map[domain].append(piece)
            
            # Consolidate visual evidence
            elif piece.source.content_type == 'image':
                # In a real implementation, this would contain actual image bytes
                # For now, we store a reference
                visual_evidence.append(piece.source.url.encode())
            
            # Collect metadata
            if piece.source.url not in metadata:
                metadata[piece.source.url] = {
                    'title': piece.source.title,
                    'domain': piece.source.domain,
                    'publish_date': piece.source.publish_date,
                    'credibility_score': piece.credibility_score,
                    'relevance_score': piece.relevance_score,
                }
        
        return ConsolidatedEvidence(
            textual_evidence=textual_evidence,
            visual_evidence=visual_evidence,
            metadata=metadata,
            evidence_map=evidence_map,
            reasoning_chain=None,  # Will be populated by apply_chain_of_thought
        )
    
    def apply_chain_of_thought(
        self,
        evidence: ConsolidatedEvidence,
        claim: AtomicClaim,
    ) -> ReasoningChain:
        """Apply chain-of-thought reasoning to consolidated evidence
        
        This method generates a structured reasoning chain that:
        1. Identifies key aspects of the claim
        2. Maps evidence to each aspect
        3. Notes where evidence agrees or conflicts
        4. Highlights missing information
        5. Builds a logical argument chain
        
        Args:
            evidence: Consolidated evidence
            claim: Atomic claim being verified
            
        Returns:
            ReasoningChain with structured reasoning steps
        """
        # Extract evidence pieces from evidence map
        all_evidence = []
        for pieces in evidence.evidence_map.values():
            all_evidence.extend(pieces)
        
        # Identify agreements, conflicts, and gaps
        agreements = self.identify_agreements(all_evidence)
        conflicts = self.identify_conflicts(all_evidence)
        gaps = self.identify_gaps(all_evidence, claim)
        
        # Build reasoning steps
        steps = []
        step_num = 1
        
        # Step 1: Identify claim aspects
        claim_aspects = self._extract_claim_aspects(claim)
        steps.append(ReasoningStep(
            step_number=step_num,
            description=f"Identified key aspects of the claim: {', '.join(claim_aspects)}",
            evidence_used=[],
            conclusion=f"The claim contains {len(claim_aspects)} key aspects to verify",
        ))
        step_num += 1
        
        # Step 2: Map evidence to aspects
        if all_evidence:
            evidence_ids = [e.id for e in all_evidence[:3]]  # Use top 3 pieces
            steps.append(ReasoningStep(
                step_number=step_num,
                description=f"Mapped {len(all_evidence)} pieces of evidence to claim aspects",
                evidence_used=evidence_ids,
                conclusion=f"Found evidence covering {len(evidence.evidence_map)} different sources",
            ))
            step_num += 1
        
        # Step 3: Note agreements
        if agreements:
            agreement_evidence = agreements[0].evidence_ids
            steps.append(ReasoningStep(
                step_number=step_num,
                description=f"Identified {len(agreements)} agreement(s) among evidence sources",
                evidence_used=agreement_evidence,
                conclusion=f"Multiple sources agree on: {agreements[0].common_assertion}",
            ))
            step_num += 1
        
        # Step 4: Note conflicts
        if conflicts:
            conflict_evidence = conflicts[0].evidence_ids
            steps.append(ReasoningStep(
                step_number=step_num,
                description=f"Identified {len(conflicts)} conflict(s) among evidence sources",
                evidence_used=conflict_evidence,
                conclusion=f"Sources disagree on certain aspects",
            ))
            step_num += 1
        
        # Step 5: Note gaps
        if gaps:
            steps.append(ReasoningStep(
                step_number=step_num,
                description=f"Identified {len(gaps)} information gap(s)",
                evidence_used=[],
                conclusion=f"Missing information about: {gaps[0].missing_aspect}",
            ))
            step_num += 1
        
        # Final step: Overall conclusion
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Synthesized all evidence and reasoning",
            evidence_used=[e.id for e in all_evidence],
            conclusion=self._generate_conclusion(agreements, conflicts, gaps),
        ))
        
        return ReasoningChain(
            steps=steps,
            agreements=agreements,
            conflicts=conflicts,
            gaps=gaps,
        )
    
    def identify_agreements(self, evidence: List[EvidencePiece]) -> List[Agreement]:
        """Identify agreements among evidence sources
        
        Detects when multiple pieces of evidence support the same assertion.
        
        Args:
            evidence: List of evidence pieces
            
        Returns:
            List of Agreement objects
        """
        if len(evidence) < 2:
            return []
        
        agreements = []
        
        # Group evidence by similar content
        # This is a simplified implementation using keyword overlap
        evidence_groups = self._group_similar_evidence(evidence)
        
        # Create agreements for groups with multiple pieces
        for group in evidence_groups:
            if len(group) >= 2:
                # Extract common assertion from the group
                common_assertion = self._extract_common_assertion(group)
                
                # Calculate agreement strength based on group size and credibility
                strength = min(1.0, len(group) / len(evidence))
                
                agreements.append(Agreement(
                    evidence_ids=[e.id for e in group],
                    common_assertion=common_assertion,
                    strength=strength,
                ))
        
        return agreements
    
    def identify_conflicts(self, evidence: List[EvidencePiece]) -> List[Conflict]:
        """Identify conflicts among evidence sources
        
        Detects when pieces of evidence contradict each other.
        
        Args:
            evidence: List of evidence pieces
            
        Returns:
            List of Conflict objects
        """
        if len(evidence) < 2:
            return []
        
        conflicts = []
        
        # Look for contradictory evidence
        # This is a simplified implementation using keyword analysis
        for i, piece1 in enumerate(evidence):
            for piece2 in evidence[i+1:]:
                if self._are_conflicting(piece1, piece2):
                    # Calculate conflict severity
                    severity = self._calculate_conflict_severity(piece1, piece2)
                    
                    conflicts.append(Conflict(
                        evidence_ids=[piece1.id, piece2.id],
                        conflicting_assertions=[
                            piece1.summary,
                            piece2.summary,
                        ],
                        severity=severity,
                    ))
        
        return conflicts
    
    def identify_gaps(
        self,
        evidence: List[EvidencePiece],
        claim: AtomicClaim,
    ) -> List[InformationGap]:
        """Identify information gaps in evidence
        
        Detects aspects of the claim that are not covered by retrieved evidence.
        
        Args:
            evidence: List of evidence pieces
            claim: Atomic claim being verified
            
        Returns:
            List of InformationGap objects
        """
        gaps = []
        
        # Extract claim aspects
        claim_aspects = self._extract_claim_aspects(claim)
        
        # Check which aspects are covered by evidence
        for aspect in claim_aspects:
            if not self._is_aspect_covered(aspect, evidence):
                # Calculate importance based on aspect position and length
                importance = 0.8 if len(aspect.split()) > 2 else 0.5
                
                gaps.append(InformationGap(
                    missing_aspect=aspect,
                    importance=importance,
                ))
        
        return gaps
    
    # Helper methods
    
    def _extract_claim_aspects(self, claim: AtomicClaim) -> List[str]:
        """Extract key aspects from a claim
        
        This is a simplified implementation that splits the claim into phrases.
        In production, this would use NLP techniques.
        """
        # Split claim into sentences/phrases
        text = claim.text
        
        # Simple splitting by common delimiters
        aspects = []
        for delimiter in [',', ' and ', ' or ', ';']:
            if delimiter in text:
                parts = text.split(delimiter)
                aspects.extend([p.strip() for p in parts if p.strip()])
                break
        
        # If no delimiters found, treat whole claim as one aspect
        if not aspects:
            aspects = [text]
        
        return aspects
    
    def _group_similar_evidence(
        self,
        evidence: List[EvidencePiece],
    ) -> List[List[EvidencePiece]]:
        """Group evidence pieces by similarity
        
        Uses keyword overlap to determine similarity.
        """
        groups = []
        used = set()
        
        for i, piece1 in enumerate(evidence):
            if i in used:
                continue
            
            group = [piece1]
            used.add(i)
            
            for j, piece2 in enumerate(evidence[i+1:], start=i+1):
                if j in used:
                    continue
                
                if self._calculate_similarity(piece1, piece2) >= self.similarity_threshold:
                    group.append(piece2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(
        self,
        piece1: EvidencePiece,
        piece2: EvidencePiece,
    ) -> float:
        """Calculate similarity between two evidence pieces
        
        Uses keyword overlap as a simple similarity metric.
        """
        # Extract keywords from summaries
        words1 = set(piece1.summary.lower().split())
        words2 = set(piece2.summary.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_common_assertion(self, group: List[EvidencePiece]) -> str:
        """Extract common assertion from a group of similar evidence
        
        Returns the summary of the highest-credibility piece in the group.
        """
        # Sort by credibility score
        sorted_group = sorted(
            group,
            key=lambda e: e.credibility_score if e.credibility_score is not None else 0.0,
            reverse=True,
        )
        
        return sorted_group[0].summary
    
    def _are_conflicting(self, piece1: EvidencePiece, piece2: EvidencePiece) -> bool:
        """Check if two evidence pieces are conflicting
        
        Uses simple heuristics to detect contradictions.
        """
        # Look for negation patterns
        summary1 = piece1.summary.lower()
        summary2 = piece2.summary.lower()
        
        # Check for explicit negations and contradictory terms
        negation_words = ['not', 'no', 'never', 'false', 'incorrect', 'wrong', 'untrue', 'refuted', 'disproven']
        contradictory_pairs = [
            ('true', 'false'),
            ('correct', 'incorrect'),
            ('proven', 'disproven'),
            ('supported', 'refuted'),
            ('confirmed', 'denied'),
        ]
        
        has_negation1 = any(word in summary1 for word in negation_words)
        has_negation2 = any(word in summary2 for word in negation_words)
        
        # Check for contradictory pairs
        for word1, word2 in contradictory_pairs:
            if (word1 in summary1 and word2 in summary2) or (word2 in summary1 and word1 in summary2):
                similarity = self._calculate_similarity(piece1, piece2)
                # Only flag as conflict if they're talking about the same thing (high similarity)
                if similarity >= 0.3:
                    return True
        
        # If one has negation and the other doesn't, check if they're actually contradicting
        if has_negation1 != has_negation2:
            similarity = self._calculate_similarity(piece1, piece2)
            # Require moderate similarity threshold to detect real conflicts
            # Only flag as conflict if they share significant content (>25% overlap)
            if similarity >= 0.25:
                # Additional check: make sure the negation is actually contradicting the claim
                # Look for patterns like "not flat" vs "is flat" or "not a double helix" vs "is a double helix"
                # Extract key claim terms from the non-negated summary
                non_negated_summary = summary1 if not has_negation1 else summary2
                negated_summary = summary1 if has_negation1 else summary2
                claim_terms = self._extract_key_terms(non_negated_summary)
                
                # Check if negation is directly contradicting the key terms
                for term in claim_terms:
                    # Look for patterns like "not [term]", "[term] is false", "not a [term]"
                    negation_patterns = [
                        f"not {term}",
                        f"not a {term}",
                        f"not the {term}",
                        f"{term} is false",
                        f"{term} is incorrect",
                        f"{term} is wrong",
                    ]
                    if any(pattern in negated_summary for pattern in negation_patterns):
                        return True
                
                # Also check for "is [term]" vs "is not [term]" patterns
                for term in claim_terms:
                    if f"is {term}" in non_negated_summary and f"is not {term}" in negated_summary:
                        return True
                    if f"is a {term}" in non_negated_summary and f"is not a {term}" in negated_summary:
                        return True
                
                # If no direct contradiction found, don't flag as conflict
                return False
        
        return False
    
    def _extract_key_terms(self, text: str) -> list:
        """Extract key terms from text (nouns and important words)"""
        # Simple extraction: words longer than 3 characters that aren't stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were', 'this', 'that', 'with', 'from'}
        words = text.lower().split()
        return [w for w in words if len(w) > 3 and w not in stop_words]
    
    def _calculate_conflict_severity(
        self,
        piece1: EvidencePiece,
        piece2: EvidencePiece,
    ) -> float:
        """Calculate severity of conflict between two pieces
        
        Higher severity when both pieces have high credibility.
        """
        cred1 = piece1.credibility_score if piece1.credibility_score is not None else 0.5
        cred2 = piece2.credibility_score if piece2.credibility_score is not None else 0.5
        
        # Severity is higher when both sources are credible
        return (cred1 + cred2) / 2.0
    
    def _is_aspect_covered(self, aspect: str, evidence: List[EvidencePiece]) -> bool:
        """Check if an aspect is covered by evidence
        
        Returns True if any evidence piece mentions the aspect.
        """
        aspect_lower = aspect.lower()
        aspect_words = set(aspect_lower.split())
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}
        aspect_keywords = aspect_words - stop_words
        
        if not aspect_keywords:
            return True  # No meaningful keywords to check
        
        # Check if any evidence mentions these keywords
        for piece in evidence:
            evidence_text = (piece.summary + " " + piece.raw_content).lower()
            matches = sum(1 for keyword in aspect_keywords if keyword in evidence_text)
            
            # Consider covered if at least 80% of keywords are present (stricter threshold)
            if matches / len(aspect_keywords) >= 0.8:
                return True
        
        return False
    
    def _generate_conclusion(
        self,
        agreements: List[Agreement],
        conflicts: List[Conflict],
        gaps: List[InformationGap],
    ) -> str:
        """Generate overall conclusion from reasoning analysis"""
        parts = []
        
        if agreements:
            parts.append(f"Found {len(agreements)} agreement(s) among sources")
        
        if conflicts:
            parts.append(f"identified {len(conflicts)} conflict(s)")
        
        if gaps:
            parts.append(f"noted {len(gaps)} information gap(s)")
        
        if not parts:
            return "Evidence analysis complete"
        
        return "; ".join(parts)
