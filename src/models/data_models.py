"""Core data models for KEPLER fact-verification system"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum


class VerdictType(Enum):
    """Classification types for fact-checking verdicts"""
    SUPPORTED = "Supported"
    REFUTED = "Refuted"
    NOT_ENOUGH_INFO = "Not Enough Information"


@dataclass
class ImageMetadata:
    """Metadata for image inputs"""
    format: str
    size_bytes: int
    dimensions: Tuple[int, int]
    hash: str


@dataclass
class LLM:
    """Large Language Model configuration"""
    model_id: str
    provider: str
    version: str
    api_endpoint: str


@dataclass
class MultimodalInput:
    """User input containing text and/or images"""
    text: Optional[str]
    image: Optional[bytes]
    image_metadata: Optional[ImageMetadata]
    timestamp: datetime
    selected_llms: List[LLM]
    decomposition_model: LLM


@dataclass
class AtomicClaim:
    """A minimal, self-contained factual statement"""
    id: str
    text: str
    is_atomic: bool
    parent_claim: Optional[str]
    verification_status: Optional[VerdictType]
    confidence_score: Optional['ConfidenceScore'] = None
    consensus_verdict: Optional['ConsensusVerdict'] = None


@dataclass
class Source:
    """Information source metadata"""
    url: str
    title: str
    publish_date: Optional[datetime]
    domain: str
    content_type: str


@dataclass
class DomainCredibility:
    """Domain credibility factors"""
    agreement_score: float
    citation_density: float
    authorship_quality: float
    stability: float
    link_authority: float
    
    def calculate_overall(self) -> float:
        """Calculate overall domain credibility score"""
        return (
            self.agreement_score * 0.3 + 
            self.citation_density * 0.2 + 
            self.authorship_quality * 0.2 + 
            self.stability * 0.15 + 
            self.link_authority * 0.15
        )


@dataclass
class EvidencePiece:
    """A piece of retrieved evidence with scores"""
    id: str
    source: Source
    summary: str
    raw_content: str
    relevance_score: Optional[float]
    credibility_score: Optional[float]
    recency_score: Optional[float]
    final_rank_score: Optional[float]


@dataclass
class Agreement:
    """Agreement among evidence sources"""
    evidence_ids: List[str]
    common_assertion: str
    strength: float


@dataclass
class Conflict:
    """Conflict among evidence sources"""
    evidence_ids: List[str]
    conflicting_assertions: List[str]
    severity: float


@dataclass
class InformationGap:
    """Missing information in evidence"""
    missing_aspect: str
    importance: float


@dataclass
class ReasoningStep:
    """A single step in chain-of-thought reasoning"""
    step_number: int
    description: str
    evidence_used: List[str]
    conclusion: str


@dataclass
class ReasoningChain:
    """Complete chain-of-thought reasoning"""
    steps: List[ReasoningStep]
    agreements: List[Agreement]
    conflicts: List[Conflict]
    gaps: List[InformationGap]


@dataclass
class ConsolidatedEvidence:
    """Synthesized multimodal evidence"""
    textual_evidence: List[str]
    visual_evidence: List[bytes]
    metadata: Dict[str, Any]
    evidence_map: Dict[str, List[EvidencePiece]]
    reasoning_chain: Optional[ReasoningChain]


@dataclass
class Verdict:
    """Individual model verdict"""
    model_id: str
    classification: VerdictType
    justification: str
    confidence: float
    evidence_references: List[str]


@dataclass
class ConsensusVerdict:
    """Aggregated verdict from multiple models"""
    final_classification: VerdictType
    consensus_justification: str
    individual_verdicts: List[Verdict]
    agreement_level: float


@dataclass
class StructuredJustification:
    """Structured justification with evidence links"""
    summary: str
    key_evidence: List[EvidencePiece]
    reasoning_chain: ReasoningChain
    source_links: List[str]


@dataclass
class ConfidenceScore:
    """Confidence score with component factors"""
    overall_score: float
    source_reliability: float
    model_agreement: float
    evidence_recency: float
    structured_justification: StructuredJustification


@dataclass
class FinalOutput:
    """Complete system output with traceability"""
    original_input: MultimodalInput
    atomic_claims: List[AtomicClaim]
    consensus_verdict: ConsensusVerdict
    confidence_score: ConfidenceScore
    processing_metadata: Dict[str, Any]
    trace_log: List[Dict[str, Any]]


@dataclass
class ErrorResponse:
    """Error response structure"""
    error_code: str
    error_message: str
    error_stage: str
    recoverable: bool
    suggested_action: str
    trace_id: str
