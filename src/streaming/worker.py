"""Kafka stage worker with retry and dead-letter routing."""

from __future__ import annotations

import logging
import time

from src.pipeline import PipelineOrchestrator
from src.streaming.client import create_consumer, create_producer
from src.streaming.config import max_retries
from src.streaming.messages import PipelineEnvelope
from src.streaming.stage_handlers import STAGE_HANDLERS, validate_stage
from src.streaming.topics import DLQ_TOPIC, OUTPUT_TOPIC, TOPICS, output_topic_for_stage

logger = logging.getLogger(__name__)


class StageWorker:
    """Consumes from a stage topic, runs the handler, publishes to the next topic."""

    def __init__(self, stage: str):
        self.stage = validate_stage(stage)
        self.handler = STAGE_HANDLERS[self.stage]
        self.orchestrator = PipelineOrchestrator()
        self.consumer = create_consumer(self.stage)
        self.producer = create_producer()

    def _publish(self, topic: str, envelope: PipelineEnvelope) -> None:
        future = self.producer.send(topic, envelope.to_bytes())
        future.get(timeout=30)
        logger.info("Published job %s to %s", envelope.job_id, topic)

    def _send_to_dlq(self, envelope: PipelineEnvelope, error: str) -> None:
        envelope.error = error
        self._publish(DLQ_TOPIC, envelope)
        logger.error("Routed job %s to DLQ: %s", envelope.job_id, error)

    def _destination_topic(self, envelope: PipelineEnvelope) -> str:
        if "final_output" in envelope.payload:
            return OUTPUT_TOPIC
        if envelope.stage in TOPICS:
            return TOPICS[envelope.stage]
        return output_topic_for_stage(self.stage)

    def process_envelope(self, envelope: PipelineEnvelope) -> None:
        attempt = envelope.attempt
        while attempt <= max_retries():
            try:
                envelope.attempt = attempt
                result = self.handler(self.orchestrator, envelope)
                topic = self._destination_topic(result)
                self._publish(topic, result)
                return
            except Exception as exc:
                attempt += 1
                logger.warning(
                    "Stage %s failed for job %s (attempt %s/%s): %s",
                    self.stage,
                    envelope.job_id,
                    attempt,
                    max_retries(),
                    exc,
                )
                if attempt > max_retries():
                    self._send_to_dlq(envelope, str(exc))
                    return
                time.sleep(min(2 ** attempt, 30))

    def run_forever(self) -> None:
        logger.info("Starting worker for stage '%s' on topic '%s'", self.stage, TOPICS[self.stage])
        while True:
            for message in self.consumer:
                envelope = PipelineEnvelope.from_bytes(message.value)
                if envelope.stage != self.stage:
                    continue
                self.process_envelope(envelope)
