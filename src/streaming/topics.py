"""Kafka topic definitions for the eight-stage KEPLER pipeline."""

from typing import Dict, List, Optional

# Stage input topics (consumer reads from here)
TOPICS: Dict[str, str] = {
    "input_processing": "kepler.input.raw",
    "claim_decomposition": "kepler.input.validated",
    "evidence_retrieval": "kepler.claims.atomic",
    "evidence_reranking": "kepler.evidence.raw",
    "evidence_aggregation": "kepler.evidence.ranked",
    "multi_model_verification": "kepler.evidence.consolidated",
    "consensus_aggregation": "kepler.verdicts.individual",
    "confidence_scoring": "kepler.verdicts.consensus",
}

OUTPUT_TOPIC = "kepler.results.final"
DLQ_TOPIC = "kepler.dlq.failed"

STAGE_ORDER: List[str] = [
    "input_processing",
    "claim_decomposition",
    "evidence_retrieval",
    "evidence_reranking",
    "evidence_aggregation",
    "multi_model_verification",
    "consensus_aggregation",
    "confidence_scoring",
]


def next_stage(current: str) -> Optional[str]:
    """Return the next stage name, or None after the final stage."""
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        return None
    if idx + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[idx + 1]


def output_topic_for_stage(stage: str) -> str:
    """Topic to publish to after completing a stage."""
    nxt = next_stage(stage)
    if nxt is None:
        return OUTPUT_TOPIC
    return TOPICS[nxt]
