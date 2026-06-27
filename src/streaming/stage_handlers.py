"""Stage handler functions invoked by Kafka workers."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

from src.models.data_models import AtomicClaim, MultimodalInput
from src.pipeline import PipelineOrchestrator
from src.streaming.messages import PipelineEnvelope
from src.streaming.serde import (
    decode_atomic_claim,
    decode_consolidated_evidence,
    decode_evidence_piece,
    decode_multimodal_input,
    encode_atomic_claim,
    encode_consolidated_evidence,
    encode_evidence_piece,
    encode_multimodal_input,
)
from src.streaming.topics import STAGE_ORDER

logger = logging.getLogger(__name__)


def _active_claim(payload: Dict) -> AtomicClaim:
    claims = payload.get("atomic_claims", [])
    idx = payload.get("active_claim_index", 0)
    return decode_atomic_claim(claims[idx])


def handle_input_processing(
    orchestrator: PipelineOrchestrator, envelope: PipelineEnvelope
) -> PipelineEnvelope:
    inp = decode_multimodal_input(envelope.payload["input"])
    if not inp.text and not inp.image:
        raise ValueError("Claim must include text and/or image")
    if not inp.selected_llms:
        raise ValueError("At least one verification model is required")

    envelope.payload = {"input": encode_multimodal_input(inp)}
    envelope.append_trace({"stage": "input_processing", "event": "complete"})
    return envelope


def handle_claim_decomposition(
    orchestrator: PipelineOrchestrator, envelope: PipelineEnvelope
) -> PipelineEnvelope:
    inp = decode_multimodal_input(envelope.payload["input"])
    claims = orchestrator._decompose_claims(inp)
    envelope.payload["atomic_claims"] = [encode_atomic_claim(c) for c in claims]
    envelope.payload["active_claim_index"] = 0
    envelope.payload["results"] = []
    envelope.append_trace(
        {"stage": "claim_decomposition", "event": "complete", "num_claims": len(claims)}
    )
    return envelope


def _process_active_claim(
    orchestrator: PipelineOrchestrator, envelope: PipelineEnvelope, stage: str
) -> PipelineEnvelope:
    inp = decode_multimodal_input(envelope.payload["input"])
    claim = _active_claim(envelope.payload)
    idx = envelope.payload.get("active_claim_index", 0)
    claims: List[AtomicClaim] = [decode_atomic_claim(c) for c in envelope.payload["atomic_claims"]]

    if stage == "evidence_retrieval":
        evidence = orchestrator._retrieve_evidence(
            claim,
            inp.timestamp,
            inp.image is not None,
            inp.image,
        )
        envelope.payload["evidence_pieces"] = [encode_evidence_piece(p) for p in evidence]

    elif stage == "evidence_reranking":
        pieces = [decode_evidence_piece(p) for p in envelope.payload.get("evidence_pieces", [])]
        ranked = orchestrator._rerank_evidence(pieces, claim)
        envelope.payload["ranked_evidence"] = [encode_evidence_piece(p) for p in ranked]

    elif stage == "evidence_aggregation":
        ranked = [decode_evidence_piece(p) for p in envelope.payload.get("ranked_evidence", [])]
        consolidated = orchestrator._aggregate_evidence(ranked, claim)
        envelope.payload["consolidated_evidence"] = encode_consolidated_evidence(consolidated)

    elif stage == "multi_model_verification":
        consolidated = decode_consolidated_evidence(envelope.payload["consolidated_evidence"])
        verdicts = orchestrator.verifier.verify_with_ensemble(claim, consolidated, inp.selected_llms)
        envelope.payload["individual_verdicts"] = [
            {
                "model_id": v.model_id,
                "classification": v.classification.value,
                "confidence": v.confidence,
                "justification": v.justification,
                "evidence_references": list(v.evidence_references),
            }
            for v in verdicts
        ]

    elif stage == "consensus_aggregation":
        from src.models.data_models import Verdict, VerdictType

        verdicts = [
            Verdict(
                model_id=item["model_id"],
                classification=VerdictType(item["classification"]),
                justification=item["justification"],
                confidence=item["confidence"],
                evidence_references=item.get("evidence_references", []),
            )
            for item in envelope.payload["individual_verdicts"]
        ]
        consensus = orchestrator.multi_model_aggregator.aggregate_verdicts(verdicts)
        envelope.payload["consensus"] = {
            "final_classification": consensus.final_classification.value,
            "consensus_justification": consensus.consensus_justification,
            "agreement_level": consensus.agreement_level,
        }

    elif stage == "confidence_scoring":
        from src.models.data_models import ConsensusVerdict, Verdict, VerdictType

        consensus_data = envelope.payload["consensus"]
        verdicts = [
            Verdict(
                model_id=item["model_id"],
                classification=VerdictType(item["classification"]),
                justification=item["justification"],
                confidence=item["confidence"],
                evidence_references=item.get("evidence_references", []),
            )
            for item in envelope.payload["individual_verdicts"]
        ]
        consensus = ConsensusVerdict(
            final_classification=VerdictType(consensus_data["final_classification"]),
            consensus_justification=consensus_data["consensus_justification"],
            individual_verdicts=verdicts,
            agreement_level=consensus_data["agreement_level"],
        )
        ranked = [decode_evidence_piece(p) for p in envelope.payload.get("ranked_evidence", [])]
        consolidated = decode_consolidated_evidence(envelope.payload["consolidated_evidence"])
        confidence = orchestrator._calculate_confidence(
            consensus,
            ranked,
            consolidated.reasoning_chain,
            claim,
        )
        claim.verification_status = consensus.final_classification
        claims[idx] = claim
        envelope.payload["atomic_claims"] = [encode_atomic_claim(c) for c in claims]
        envelope.payload.setdefault("results", []).append(
            {
                "claim_id": claim.id,
                "verdict": consensus.final_classification.value,
                "confidence": confidence.overall_score,
            }
        )

        if idx + 1 < len(claims):
            envelope.payload["active_claim_index"] = idx + 1
            envelope.payload.pop("evidence_pieces", None)
            envelope.payload.pop("ranked_evidence", None)
            envelope.payload.pop("consolidated_evidence", None)
            envelope.payload.pop("individual_verdicts", None)
            envelope.payload.pop("consensus", None)
            envelope.stage = "evidence_retrieval"
            envelope.append_trace(
                {"stage": "confidence_scoring", "event": "claim_complete", "claim_id": claim.id}
            )
            return envelope

        primary = orchestrator._select_primary_verdict(claims)
        overall = orchestrator._aggregate_claim_confidences(claims)
        envelope.payload["final_output"] = {
            "verdict": primary.final_classification.value,
            "confidence": overall.overall_score,
            "results": envelope.payload.get("results", []),
            "num_atomic_claims": len(claims),
            "processing_metadata": {
                "pipeline_version": "1.0",
                "total_stages": 8,
                "mode": "kafka",
            },
        }
        envelope.stage = "complete"

    envelope.append_trace({"stage": stage, "event": "complete", "claim_id": claim.id})
    return envelope


def handle_evidence_retrieval(o, e):
    return _process_active_claim(o, e, "evidence_retrieval")


def handle_evidence_reranking(o, e):
    return _process_active_claim(o, e, "evidence_reranking")


def handle_evidence_aggregation(o, e):
    return _process_active_claim(o, e, "evidence_aggregation")


def handle_multi_model_verification(o, e):
    return _process_active_claim(o, e, "multi_model_verification")


def handle_consensus_aggregation(o, e):
    return _process_active_claim(o, e, "consensus_aggregation")


def handle_confidence_scoring(o, e):
    return _process_active_claim(o, e, "confidence_scoring")


STAGE_HANDLERS: Dict[str, Callable[[PipelineOrchestrator, PipelineEnvelope], PipelineEnvelope]] = {
    "input_processing": handle_input_processing,
    "claim_decomposition": handle_claim_decomposition,
    "evidence_retrieval": handle_evidence_retrieval,
    "evidence_reranking": handle_evidence_reranking,
    "evidence_aggregation": handle_evidence_aggregation,
    "multi_model_verification": handle_multi_model_verification,
    "consensus_aggregation": handle_consensus_aggregation,
    "confidence_scoring": handle_confidence_scoring,
}


def validate_stage(stage: str) -> str:
    if stage not in STAGE_ORDER:
        raise ValueError(f"Unknown stage '{stage}'. Valid: {', '.join(STAGE_ORDER)}")
    return stage
