"""Pipeline message envelope passed between Kafka stages."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineEnvelope:
    """Serializable claim state flowing through Kafka topics."""

    job_id: str
    stage: str
    attempt: int
    payload: Dict[str, Any]
    trace: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def create(cls, stage: str, payload: Dict[str, Any]) -> PipelineEnvelope:
        return cls(
            job_id=str(uuid.uuid4()),
            stage=stage,
            attempt=0,
            payload=payload,
        )

    def to_bytes(self) -> bytes:
        return json.dumps(
            {
                "job_id": self.job_id,
                "stage": self.stage,
                "attempt": self.attempt,
                "payload": self.payload,
                "trace": self.trace,
                "error": self.error,
            }
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> PipelineEnvelope:
        raw = json.loads(data.decode("utf-8"))
        return cls(
            job_id=raw["job_id"],
            stage=raw["stage"],
            attempt=raw.get("attempt", 0),
            payload=raw.get("payload", {}),
            trace=raw.get("trace", []),
            error=raw.get("error"),
        )

    def with_stage(self, stage: str) -> PipelineEnvelope:
        return PipelineEnvelope(
            job_id=self.job_id,
            stage=stage,
            attempt=0,
            payload=self.payload,
            trace=list(self.trace),
        )

    def append_trace(self, event: Dict[str, Any]) -> None:
        self.trace.append(event)
