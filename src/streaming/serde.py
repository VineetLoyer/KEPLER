"""Serialize pipeline dataclasses for Kafka message payloads."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.data_models import (
    AtomicClaim,
    ConfidenceScore,
    ConsolidatedEvidence,
    EvidencePiece,
    FinalOutput,
    LLM,
    MultimodalInput,
    ReasoningChain,
    Source,
    StructuredJustification,
    VerdictType,
)


def _enum_value(value: Optional[VerdictType]) -> Optional[str]:
    return value.value if value is not None else None


def _parse_verdict(value: Optional[str]) -> Optional[VerdictType]:
    if value is None:
        return None
    for item in VerdictType:
        if item.value == value:
            return item
    return None


def encode_llm(llm: LLM) -> Dict[str, str]:
    return {
        "model_id": llm.model_id,
        "provider": llm.provider,
        "version": llm.version,
        "api_endpoint": llm.api_endpoint,
    }


def decode_llm(data: Dict[str, str]) -> LLM:
    return LLM(**data)


def encode_multimodal_input(inp: MultimodalInput) -> Dict[str, Any]:
    return {
        "text": inp.text,
        "image_b64": base64.b64encode(inp.image).decode("ascii") if inp.image else None,
        "timestamp": inp.timestamp.isoformat(),
        "selected_llms": [encode_llm(llm) for llm in inp.selected_llms],
        "decomposition_model": encode_llm(inp.decomposition_model),
    }


def decode_multimodal_input(data: Dict[str, Any]) -> MultimodalInput:
    image_b64 = data.get("image_b64")
    return MultimodalInput(
        text=data.get("text"),
        image=base64.b64decode(image_b64) if image_b64 else None,
        image_metadata=None,
        timestamp=datetime.fromisoformat(data["timestamp"]),
        selected_llms=[decode_llm(item) for item in data["selected_llms"]],
        decomposition_model=decode_llm(data["decomposition_model"]),
    )


def encode_atomic_claim(claim: AtomicClaim) -> Dict[str, Any]:
    return {
        "id": claim.id,
        "text": claim.text,
        "is_atomic": claim.is_atomic,
        "parent_claim": claim.parent_claim,
        "verification_status": _enum_value(claim.verification_status),
    }


def decode_atomic_claim(data: Dict[str, Any]) -> AtomicClaim:
    return AtomicClaim(
        id=data["id"],
        text=data["text"],
        is_atomic=data["is_atomic"],
        parent_claim=data.get("parent_claim"),
        verification_status=_parse_verdict(data.get("verification_status")),
    )


def encode_source(source: Source) -> Dict[str, Any]:
    return {
        "url": source.url,
        "title": source.title,
        "publish_date": source.publish_date.isoformat() if source.publish_date else None,
        "domain": source.domain,
        "content_type": source.content_type,
    }


def decode_source(data: Dict[str, Any]) -> Source:
    publish_date = data.get("publish_date")
    return Source(
        url=data["url"],
        title=data["title"],
        publish_date=datetime.fromisoformat(publish_date) if publish_date else None,
        domain=data["domain"],
        content_type=data["content_type"],
    )


def encode_evidence_piece(piece: EvidencePiece) -> Dict[str, Any]:
    return {
        "id": piece.id,
        "source": encode_source(piece.source),
        "summary": piece.summary,
        "raw_content": piece.raw_content,
        "relevance_score": piece.relevance_score,
        "credibility_score": piece.credibility_score,
        "recency_score": piece.recency_score,
        "final_rank_score": piece.final_rank_score,
    }


def decode_evidence_piece(data: Dict[str, Any]) -> EvidencePiece:
    return EvidencePiece(
        id=data["id"],
        source=decode_source(data["source"]),
        summary=data["summary"],
        raw_content=data["raw_content"],
        relevance_score=data.get("relevance_score"),
        credibility_score=data.get("credibility_score"),
        recency_score=data.get("recency_score"),
        final_rank_score=data.get("final_rank_score"),
    )


def encode_reasoning_chain(chain: ReasoningChain) -> Dict[str, Any]:
    return {
        "steps": [
            {
                "step_number": step.step_number,
                "description": step.description,
                "conclusion": step.conclusion,
            }
            for step in chain.steps
        ],
        "agreements": list(chain.agreements),
        "conflicts": list(chain.conflicts),
        "gaps": list(chain.gaps),
    }


def decode_reasoning_chain(data: Dict[str, Any]) -> ReasoningChain:
    from src.models.data_models import ReasoningStep

    return ReasoningChain(
        steps=[
            ReasoningStep(
                step_number=step["step_number"],
                description=step["description"],
                conclusion=step["conclusion"],
            )
            for step in data.get("steps", [])
        ],
        agreements=data.get("agreements", []),
        conflicts=data.get("conflicts", []),
        gaps=data.get("gaps", []),
    )


def encode_consolidated_evidence(evidence: ConsolidatedEvidence) -> Dict[str, Any]:
    return {
        "textual_evidence": [encode_evidence_piece(p) for p in evidence.textual_evidence],
        "visual_evidence": [encode_evidence_piece(p) for p in evidence.visual_evidence],
        "reasoning_chain": encode_reasoning_chain(evidence.reasoning_chain)
        if evidence.reasoning_chain
        else None,
    }


def decode_consolidated_evidence(data: Dict[str, Any]) -> ConsolidatedEvidence:
    chain_data = data.get("reasoning_chain")
    return ConsolidatedEvidence(
        textual_evidence=[decode_evidence_piece(p) for p in data.get("textual_evidence", [])],
        visual_evidence=[decode_evidence_piece(p) for p in data.get("visual_evidence", [])],
        reasoning_chain=decode_reasoning_chain(chain_data) if chain_data else None,
    )


def encode_final_output(output: FinalOutput) -> Dict[str, Any]:
    return {
        "verdict": output.consensus_verdict.final_classification.value,
        "confidence": output.confidence_score.overall_score,
        "num_atomic_claims": len(output.atomic_claims),
        "trace_log": output.trace_log,
        "processing_metadata": output.processing_metadata,
    }
