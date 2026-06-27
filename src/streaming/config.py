"""Kafka connection configuration."""

import os


def bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def consumer_group(stage: str) -> str:
    return os.getenv("KAFKA_CONSUMER_GROUP", f"kepler-{stage}")


def max_retries() -> int:
    return int(os.getenv("KAFKA_STAGE_MAX_RETRIES", "3"))
