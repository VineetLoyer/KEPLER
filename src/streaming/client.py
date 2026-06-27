"""Kafka client helpers."""

from __future__ import annotations

import logging

from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from src.streaming.config import bootstrap_servers, consumer_group
from src.streaming.topics import DLQ_TOPIC, OUTPUT_TOPIC, TOPICS

logger = logging.getLogger(__name__)


def all_topics() -> list[str]:
    topics = list(TOPICS.values()) + [OUTPUT_TOPIC, DLQ_TOPIC]
    return sorted(set(topics))


def ensure_topics() -> None:
    """Create pipeline topics if they do not exist (local/dev helper)."""
    admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers())
    configs = [NewTopic(name=t, num_partitions=3, replication_factor=1) for t in all_topics()]
    try:
        admin.create_topics(configs, validate_only=False)
        logger.info("Created Kafka topics: %s", ", ".join(all_topics()))
    except TopicAlreadyExistsError:
        logger.debug("Kafka topics already exist")
    finally:
        admin.close()


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers(),
        acks="all",
        retries=3,
        linger_ms=10,
    )


def create_consumer(stage: str) -> KafkaConsumer:
    return KafkaConsumer(
        TOPICS[stage],
        bootstrap_servers=bootstrap_servers(),
        group_id=consumer_group(stage),
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        consumer_timeout_ms=1000,
    )
