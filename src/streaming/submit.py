"""Submit a claim to the Kafka pipeline."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from typing import List, Optional

from src.models.data_models import LLM
from src.streaming.client import create_producer, ensure_topics
from src.streaming.messages import PipelineEnvelope
from src.streaming.serde import encode_multimodal_input
from src.streaming.topics import TOPICS

logger = logging.getLogger(__name__)


DEFAULT_MODELS = [
    LLM(
        model_id="openai/gpt-4",
        provider="openai",
        version="v1",
        api_endpoint="https://api.openai.com/v1",
    ),
]


def build_input(text: str, models: Optional[List[LLM]] = None):
    from src.models.data_models import MultimodalInput

    selected = models or DEFAULT_MODELS
    return MultimodalInput(
        text=text,
        image=None,
        image_metadata=None,
        timestamp=datetime.now(),
        selected_llms=selected,
        decomposition_model=selected[0],
    )


def submit_claim(text: str) -> str:
    ensure_topics()
    producer = create_producer()
    inp = build_input(text)
    envelope = PipelineEnvelope.create(
        stage="input_processing",
        payload={"input": encode_multimodal_input(inp)},
    )
    future = producer.send(TOPICS["input_processing"], envelope.to_bytes())
    future.get(timeout=30)
    producer.flush()
    logger.info("Submitted job %s to %s", envelope.job_id, TOPICS["input_processing"])
    return envelope.job_id


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Submit a claim to the KEPLER Kafka pipeline")
    parser.add_argument("--text", required=True, help="Claim text to verify")
    args = parser.parse_args()
    job_id = submit_claim(args.text)
    print(json.dumps({"job_id": job_id, "topic": TOPICS["input_processing"]}))


if __name__ == "__main__":
    main()
