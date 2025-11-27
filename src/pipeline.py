"""Pipeline Orchestrator for KEPLER system

This module coordinates all agents in the fact-verification pipeline and maintains
complete traceability through detailed logging at each stage.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
from src.models.data_models import (
    MultimodalInput,
    AtomicClaim,
    EvidencePiece,
    ConsolidatedEvidence,
    ConsensusVerdict,
    ConfidenceScore,
    FinalOutput,
    ErrorResponse,
    VerdictType,
)
from src.agents.claim_decomposition_agent import ClaimDecompositionAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.reranker_agent import RerankerAgent
from src.agents.aggregator_agent import AggregatorAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.multi_model_aggregator import MultiModelAggregator
from src.agents.confidence_scorer import ConfidenceScorer
from src.utils.retry import retry_with_exponential_backoff, RetryExhaustedError
from src.config import config

logger = logging.getLogger(__name__)


def create_retriever_agent() -> RetrieverAgent:
    """Create retriever agent with real search client if API keys are available"""
    search_client = None
    scraper_client = None
    
    # Try to use real Google Search if API keys are available
    if config.api.google_search_api_key and config.api.google_search_engine_id:
        try:
            from src.utils.google_search_client import GoogleSearchClient
            from src.utils.web_scraper import WebScraper
            search_client = GoogleSearchClient()
            scraper_client = WebScraper()
            logger.info("Using real Google Search API for evidence retrieval")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Search client: {e}. Using mock client.")
    else:
        logger.warning("Google Search API keys not configured. Using mock search client.")
    
    return RetrieverAgent(search_client=search_client, scraper_client=scraper_client)


class PipelineOrchestrator:
    """Main orchestrator that coordinates all agents and maintains traceability"""
    
    def __init__(
        self,
        claim_decomposer: Optional[ClaimDecompositionAgent] = None,
        retriever: Optional[RetrieverAgent] = None,
        reranker: Optional[RerankerAgent] = None,
        aggregator: Optional[AggregatorAgent] = None,
        verifier: Optional[VerifierAgent] = None,
        multi_model_aggregator: Optional[MultiModelAggregator] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
    ):
        """Initialize the Pipeline Orchestrator
        
        Args:
            claim_decomposer: Claim decomposition agent (creates default if None)
            retriever: Retriever agent (creates default if None)
            reranker: Reranker agent (creates default if None)
            aggregator: Aggregator agent (creates default if None)
            verifier: Verifier agent (creates default if None)
            multi_model_aggregator: Multi-model aggregator (creates default if None)
            confidence_scorer: Confidence scorer (creates default if None)
        """
        self.claim_decomposer = claim_decomposer or ClaimDecompositionAgent()
        self.retriever = retriever or create_retriever_agent()
        self.reranker = reranker or RerankerAgent()
        self.aggregator = aggregator or AggregatorAgent()
        self.verifier = verifier or VerifierAgent()
        self.multi_model_aggregator = multi_model_aggregator or MultiModelAggregator()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        
        # Trace log for the current pipeline execution
        self.trace_log: List[Dict[str, Any]] = []
    
    def process_claim(self, multimodal_input: MultimodalInput) -> FinalOutput:
        """Process a claim through the complete verification pipeline
        
        This is the main entry point that orchestrates all stages:
        1. Input Processing
        2. Claim Decomposition
        3. Evidence Retrieval
        4. Evidence Reranking
        5. Evidence Aggregation
        6. Verification
        7. Confidence Scoring
        
        Each stage is logged for complete traceability.
        
        Args:
            multimodal_input: User input with text, images, and selected LLMs
            
        Returns:
            FinalOutput with verdict, confidence, and complete trace log
        """
        # Reset trace log for new execution
        self.trace_log = []
        
        try:
            # Stage 1: Input Processing
            self._log_stage_start("input_processing", {
                "has_text": multimodal_input.text is not None,
                "has_image": multimodal_input.image is not None,
                "num_llms": len(multimodal_input.selected_llms),
                "decomposition_model": multimodal_input.decomposition_model.model_id,
            })
            self._log_stage_complete("input_processing", {
                "status": "success",
                "timestamp": multimodal_input.timestamp.isoformat(),
            })
            
            # Stage 2: Claim Decomposition
            atomic_claims = self._decompose_claims(multimodal_input)
            
            # Handle graceful degradation when no claims are extracted
            if not atomic_claims:
                logger.warning(
                    "No atomic claims extracted from input. "
                    "Returning NOT_ENOUGH_INFO verdict (graceful degradation)."
                )
                
                # Create a default "NOT_ENOUGH_INFO" verdict
                from src.models.data_models import (
                    ConsensusVerdict,
                    Verdict,
                    ConfidenceScore,
                    StructuredJustification,
                    ReasoningChain,
                )
                
                # Create individual verdicts for each model
                individual_verdicts = [
                    Verdict(
                        model_id=llm.model_id,
                        classification=VerdictType.NOT_ENOUGH_INFO,
                        justification="No claims could be extracted from the input for verification.",
                        confidence=0.0,
                        evidence_references=[],
                    )
                    for llm in multimodal_input.selected_llms
                ]
                
                # Create consensus verdict
                consensus_verdict = ConsensusVerdict(
                    final_classification=VerdictType.NOT_ENOUGH_INFO,
                    consensus_justification="No claims could be extracted from the input for verification.",
                    individual_verdicts=individual_verdicts,
                    agreement_level=1.0,  # All models agree on NOT_ENOUGH_INFO
                )
                
                # Create confidence score
                confidence_score = ConfidenceScore(
                    overall_score=0.0,
                    source_reliability=0.0,
                    model_agreement=1.0,
                    evidence_recency=0.0,
                    structured_justification=StructuredJustification(
                        summary="No claims could be extracted from the input.",
                        key_evidence=[],
                        reasoning_chain=ReasoningChain(steps=[], agreements=[], conflicts=[], gaps=[]),
                        source_links=[],
                    ),
                )
                
                # Create processing metadata
                processing_metadata = {
                    "pipeline_version": "1.0",
                    "total_stages": 2,  # Only input processing and claim decomposition
                    "processing_time_ms": self._calculate_total_time(),
                    "num_atomic_claims": 0,
                    "num_evidence_pieces": 0,
                    "num_ranked_evidence": 0,
                }
                
                # Create final output
                final_output = FinalOutput(
                    original_input=multimodal_input,
                    atomic_claims=[],
                    consensus_verdict=consensus_verdict,
                    confidence_score=confidence_score,
                    processing_metadata=processing_metadata,
                    trace_log=self.trace_log.copy(),
                )
                
                return final_output
            
            # Process each atomic claim independently
            all_evidence_pieces = []
            all_ranked_evidence = []
            claim_verdicts = {}  # Map claim_id to verdict
            
            for claim in atomic_claims:
                logger.info(f"Processing atomic claim: {claim.id}")
                
                # Stage 3: Evidence Retrieval (per claim)
                evidence_pieces = self._retrieve_evidence(
                    claim,
                    multimodal_input.timestamp,
                    multimodal_input.image is not None,
                    multimodal_input.image,
                )
                all_evidence_pieces.extend(evidence_pieces)
                
                # Stage 4: Evidence Reranking (per claim)
                ranked_evidence = self._rerank_evidence(evidence_pieces, claim)
                all_ranked_evidence.extend(ranked_evidence)
                
                # Stage 5: Evidence Aggregation (per claim)
                consolidated_evidence = self._aggregate_evidence(ranked_evidence, claim)
                
                # Stage 6: Verification (per claim)
                claim_verdict = self._verify_claim(
                    claim,
                    consolidated_evidence,
                    multimodal_input.selected_llms,
                )
                
                # Store verdict for this claim
                claim_verdicts[claim.id] = claim_verdict
                
                # Update the claim's verification status
                claim.verification_status = claim_verdict.final_classification
                
                logger.info(f"Claim {claim.id} verdict: {claim_verdict.final_classification.value}")
            
            # Stage 7: Aggregate all claim verdicts into overall consensus
            # Use the first claim's verdict as the primary one for now
            # In a more sophisticated system, you'd aggregate across all claims
            primary_claim = atomic_claims[0]
            consensus_verdict = claim_verdicts[primary_claim.id]
            
            # Use evidence from all claims for confidence scoring
            # Aggregate reasoning chains from all claims
            all_reasoning_chains = []
            for claim in atomic_claims:
                claim_evidence = [e for e in all_ranked_evidence if claim.text.lower() in e.summary.lower()]
                if claim_evidence:
                    consolidated = self._aggregate_evidence(claim_evidence, claim)
                    if consolidated.reasoning_chain:
                        all_reasoning_chains.append(consolidated.reasoning_chain)
            
            # Use the first reasoning chain or create empty one
            primary_reasoning_chain = all_reasoning_chains[0] if all_reasoning_chains else None
            if primary_reasoning_chain is None:
                from src.models.data_models import ReasoningChain
                primary_reasoning_chain = ReasoningChain(steps=[], agreements=[], conflicts=[], gaps=[])
            
            # Stage 8: Confidence Scoring (using all evidence)
            confidence_score = self._calculate_confidence(
                consensus_verdict,
                all_ranked_evidence,
                primary_reasoning_chain,
            )
            
            # Create processing metadata
            processing_metadata = {
                "pipeline_version": "1.0",
                "total_stages": 8,
                "processing_time_ms": self._calculate_total_time(),
                "num_atomic_claims": len(atomic_claims),
                "num_evidence_pieces": len(all_evidence_pieces),
                "num_ranked_evidence": len(all_ranked_evidence),
                "per_claim_verification": True,
            }
            
            # Create final output
            final_output = FinalOutput(
                original_input=multimodal_input,
                atomic_claims=atomic_claims,
                consensus_verdict=consensus_verdict,
                confidence_score=confidence_score,
                processing_metadata=processing_metadata,
                trace_log=self.trace_log.copy(),
            )
            
            return final_output
            
        except Exception as e:
            # Log error
            self._log_error("pipeline_execution", str(e))
            raise
    
    def _decompose_claims(self, multimodal_input: MultimodalInput) -> List[AtomicClaim]:
        """Stage 2: Decompose input text into atomic claims"""
        stage_name = "claim_decomposition"
        
        self._log_stage_start(stage_name, {
            "input_text_length": len(multimodal_input.text) if multimodal_input.text else 0,
            "model": multimodal_input.decomposition_model.model_id,
        })
        
        start_time = time.time()
        
        # Decompose claims
        if not multimodal_input.text:
            atomic_claims = []
        else:
            atomic_claims = self.claim_decomposer.decompose(
                multimodal_input.text,
                multimodal_input.decomposition_model,
            )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self._log_stage_complete(stage_name, {
            "status": "success",
            "num_claims": len(atomic_claims),
            "claims": [{"id": c.id, "text": c.text, "is_atomic": c.is_atomic} for c in atomic_claims],
            "elapsed_ms": elapsed_ms,
        })
        
        return atomic_claims
    
    def _retrieve_evidence(
        self,
        claim: AtomicClaim,
        claim_date: datetime,
        has_visual_content: bool,
        image: Optional[bytes],
    ) -> List[EvidencePiece]:
        """Stage 3: Retrieve evidence from the web
        
        Implements graceful degradation: if evidence retrieval fails,
        returns empty list and logs warning.
        """
        stage_name = "evidence_retrieval"
        
        self._log_stage_start(stage_name, {
            "claim_id": claim.id,
            "claim_text": claim.text,
            "has_visual_content": has_visual_content,
            "claim_date": claim_date.isoformat(),
        })
        
        start_time = time.time()
        
        try:
            # Retrieve evidence with retry logic
            evidence_pieces = self._retrieve_with_retry(
                claim,
                claim_date,
                has_visual_content,
                image,
            )
            
            # Graceful degradation: handle empty evidence
            if not evidence_pieces:
                logger.warning(
                    f"No evidence retrieved for claim {claim.id}. "
                    "System will proceed with empty evidence (graceful degradation)."
                )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "success" if evidence_pieces else "success_no_evidence",
                "num_evidence_pieces": len(evidence_pieces),
                "sources": [
                    {
                        "id": e.id,
                        "url": e.source.url,
                        "domain": e.source.domain,
                        "content_type": e.source.content_type,
                    }
                    for e in evidence_pieces
                ],
                "elapsed_ms": elapsed_ms,
            })
            
            return evidence_pieces
            
        except RetryExhaustedError as e:
            # All retries exhausted - graceful degradation
            logger.error(
                f"Evidence retrieval failed after retries for claim {claim.id}: {str(e)}. "
                "Proceeding with empty evidence (graceful degradation)."
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "failed_graceful_degradation",
                "num_evidence_pieces": 0,
                "error": str(e),
                "elapsed_ms": elapsed_ms,
            })
            
            return []  # Return empty list for graceful degradation
            
        except Exception as e:
            # Unexpected error - still try graceful degradation
            logger.exception(
                f"Unexpected error during evidence retrieval for claim {claim.id}: {str(e)}. "
                "Proceeding with empty evidence (graceful degradation)."
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "error_graceful_degradation",
                "num_evidence_pieces": 0,
                "error": str(e),
                "elapsed_ms": elapsed_ms,
            })
            
            return []  # Return empty list for graceful degradation
    
    @retry_with_exponential_backoff(max_retries=2, initial_delay=1.0)
    def _retrieve_with_retry(
        self,
        claim: AtomicClaim,
        claim_date: datetime,
        has_visual_content: bool,
        image: Optional[bytes],
    ) -> List[EvidencePiece]:
        """Retrieve evidence with retry logic
        
        This method is wrapped with retry decorator to handle transient failures.
        """
        return self.retriever.retrieve_evidence(
            claim,
            claim_date,
            has_visual_content,
            image,
        )
    
    def _rerank_evidence(
        self,
        evidence: List[EvidencePiece],
        claim: AtomicClaim,
    ) -> List[EvidencePiece]:
        """Stage 4: Rerank evidence by quality and relevance
        
        Handles empty evidence gracefully.
        """
        stage_name = "evidence_reranking"
        
        self._log_stage_start(stage_name, {
            "claim_id": claim.id,
            "num_input_evidence": len(evidence),
        })
        
        start_time = time.time()
        
        # Handle empty evidence gracefully
        if not evidence:
            logger.warning(
                f"No evidence to rerank for claim {claim.id}. "
                "Skipping reranking stage (graceful degradation)."
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "skipped_no_evidence",
                "num_output_evidence": 0,
                "num_filtered": 0,
                "elapsed_ms": elapsed_ms,
            })
            
            return []
        
        try:
            # Rank evidence
            ranked_evidence = self.reranker.rank_evidence(evidence, claim)
            
            # Check if all evidence was filtered out
            if not ranked_evidence:
                logger.warning(
                    f"All evidence filtered out during reranking for claim {claim.id}. "
                    "Proceeding with empty evidence (graceful degradation)."
                )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "success" if ranked_evidence else "success_all_filtered",
                "num_output_evidence": len(ranked_evidence),
                "num_filtered": len(evidence) - len(ranked_evidence),
                "top_evidence": [
                    {
                        "id": e.id,
                        "url": e.source.url,
                        "relevance": e.relevance_score,
                        "credibility": e.credibility_score,
                        "recency": e.recency_score,
                        "final_rank": e.final_rank_score,
                    }
                    for e in ranked_evidence[:3]  # Log top 3
                ],
                "elapsed_ms": elapsed_ms,
            })
            
            return ranked_evidence
            
        except Exception as e:
            # Error during reranking - return original evidence
            logger.exception(
                f"Error during evidence reranking for claim {claim.id}: {str(e)}. "
                "Returning original evidence (graceful degradation)."
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            self._log_stage_complete(stage_name, {
                "status": "error_using_original",
                "num_output_evidence": len(evidence),
                "num_filtered": 0,
                "error": str(e),
                "elapsed_ms": elapsed_ms,
            })
            
            return evidence  # Return original evidence
    
    def _aggregate_evidence(
        self,
        evidence: List[EvidencePiece],
        claim: AtomicClaim,
    ) -> ConsolidatedEvidence:
        """Stage 5: Aggregate evidence and apply chain-of-thought reasoning"""
        stage_name = "evidence_aggregation"
        
        self._log_stage_start(stage_name, {
            "claim_id": claim.id,
            "num_evidence": len(evidence),
        })
        
        start_time = time.time()
        
        # Consolidate evidence
        consolidated = self.aggregator.consolidate_evidence(evidence)
        
        # Apply chain-of-thought reasoning
        reasoning_chain = self.aggregator.apply_chain_of_thought(consolidated, claim)
        consolidated.reasoning_chain = reasoning_chain
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self._log_stage_complete(stage_name, {
            "status": "success",
            "num_textual_evidence": len(consolidated.textual_evidence),
            "num_visual_evidence": len(consolidated.visual_evidence),
            "num_reasoning_steps": len(reasoning_chain.steps),
            "num_agreements": len(reasoning_chain.agreements),
            "num_conflicts": len(reasoning_chain.conflicts),
            "num_gaps": len(reasoning_chain.gaps),
            "reasoning_steps": [
                {
                    "step": step.step_number,
                    "description": step.description,
                    "conclusion": step.conclusion,
                }
                for step in reasoning_chain.steps
            ],
            "elapsed_ms": elapsed_ms,
        })
        
        return consolidated
    
    def _verify_claim(
        self,
        claim: AtomicClaim,
        evidence: ConsolidatedEvidence,
        models: List,
    ) -> ConsensusVerdict:
        """Stage 6: Verify claim using multiple LLMs and aggregate results"""
        stage_name = "verification"
        
        self._log_stage_start(stage_name, {
            "claim_id": claim.id,
            "num_models": len(models),
            "models": [m.model_id for m in models],
        })
        
        start_time = time.time()
        
        # Verify with ensemble
        individual_verdicts = self.verifier.verify_with_ensemble(claim, evidence, models)
        
        # Aggregate verdicts
        consensus = self.multi_model_aggregator.aggregate_verdicts(individual_verdicts)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self._log_stage_complete(stage_name, {
            "status": "success",
            "individual_verdicts": [
                {
                    "model": v.model_id,
                    "classification": v.classification.value,
                    "confidence": v.confidence,
                    "num_evidence_refs": len(v.evidence_references),
                }
                for v in individual_verdicts
            ],
            "consensus_classification": consensus.final_classification.value,
            "agreement_level": consensus.agreement_level,
            "elapsed_ms": elapsed_ms,
        })
        
        return consensus
    
    def _calculate_confidence(
        self,
        consensus: ConsensusVerdict,
        evidence: List[EvidencePiece],
        reasoning_chain,
    ) -> ConfidenceScore:
        """Stage 7: Calculate confidence score"""
        stage_name = "confidence_scoring"
        
        self._log_stage_start(stage_name, {
            "consensus_classification": consensus.final_classification.value,
            "agreement_level": consensus.agreement_level,
            "num_evidence": len(evidence),
        })
        
        start_time = time.time()
        
        # Calculate confidence
        confidence_score = self.confidence_scorer.calculate_confidence(
            consensus,
            evidence,
            reasoning_chain,
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        self._log_stage_complete(stage_name, {
            "status": "success",
            "overall_score": confidence_score.overall_score,
            "source_reliability": confidence_score.source_reliability,
            "model_agreement": confidence_score.model_agreement,
            "evidence_recency": confidence_score.evidence_recency,
            "num_source_links": len(confidence_score.structured_justification.source_links),
            "elapsed_ms": elapsed_ms,
        })
        
        return confidence_score
    
    def _log_stage_start(self, stage_name: str, details: Dict[str, Any]):
        """Log the start of a pipeline stage
        
        Args:
            stage_name: Name of the stage
            details: Stage-specific details
        """
        log_entry = {
            "stage": stage_name,
            "event": "start",
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }
        self.trace_log.append(log_entry)
    
    def _log_stage_complete(self, stage_name: str, results: Dict[str, Any]):
        """Log the completion of a pipeline stage
        
        Args:
            stage_name: Name of the stage
            results: Stage results and metrics
        """
        log_entry = {
            "stage": stage_name,
            "event": "complete",
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }
        self.trace_log.append(log_entry)
    
    def _log_error(self, stage_name: str, error_message: str):
        """Log an error during pipeline execution
        
        Args:
            stage_name: Name of the stage where error occurred
            error_message: Error message
        """
        log_entry = {
            "stage": stage_name,
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
        }
        self.trace_log.append(log_entry)
    
    def _calculate_total_time(self) -> float:
        """Calculate total processing time from trace log
        
        Returns:
            Total time in milliseconds
        """
        if len(self.trace_log) < 2:
            return 0.0
        
        # Get first and last timestamps
        first_entry = self.trace_log[0]
        last_entry = self.trace_log[-1]
        
        first_time = datetime.fromisoformat(first_entry["timestamp"])
        last_time = datetime.fromisoformat(last_entry["timestamp"])
        
        return (last_time - first_time).total_seconds() * 1000
    
    def inspect_stage(self, stage_name: str) -> List[Dict[str, Any]]:
        """Inspect all log entries for a specific stage
        
        This enables stage-level inspection of the pipeline execution.
        
        Args:
            stage_name: Name of the stage to inspect
            
        Returns:
            List of log entries for the specified stage
        """
        return [
            entry for entry in self.trace_log
            if entry.get("stage") == stage_name
        ]
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of the trace log
        
        Returns:
            Dictionary with trace summary statistics
        """
        stages = set(entry.get("stage") for entry in self.trace_log if entry.get("stage"))
        
        return {
            "total_entries": len(self.trace_log),
            "stages_executed": list(stages),
            "num_stages": len(stages),
            "errors": [
                entry for entry in self.trace_log
                if entry.get("event") == "error"
            ],
        }
