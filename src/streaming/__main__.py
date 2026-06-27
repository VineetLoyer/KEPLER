"""CLI entrypoint for KEPLER Kafka streaming workers."""

from __future__ import annotations

import argparse
import logging

from src.streaming.client import ensure_topics
from src.streaming.stage_handlers import STAGE_HANDLERS
from src.streaming.worker import StageWorker


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run a KEPLER Kafka stage worker")
    parser.add_argument(
        "--stage",
        required=True,
        choices=list(STAGE_HANDLERS.keys()),
        help="Pipeline stage this worker executes",
    )
    parser.add_argument(
        "--init-topics",
        action="store_true",
        help="Create Kafka topics before starting the worker",
    )
    args = parser.parse_args()

    if args.init_topics:
        ensure_topics()

    worker = StageWorker(args.stage)
    worker.run_forever()


if __name__ == "__main__":
    main()
