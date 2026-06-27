"""Spark batch evaluation of KEPLER on the FEVER benchmark.

Partitions FEVER claims across Spark executors and runs the KEPLER pipeline
in parallel. Aggregates label accuracy on the driver.

Usage:
    spark-submit evaluation/spark_fever_eval.py \
        --input evaluation/data/fever_dev.jsonl \
        --output evaluation/results/fever_spark_metrics.json \
        --limit 100
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow imports from repository root when launched via spark-submit
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _predict_label(claim_text: str) -> str:
    """Run the KEPLER pipeline for a single claim and return the verdict label."""
    from datetime import datetime

    from src.models.data_models import LLM, MultimodalInput
    from src.pipeline import PipelineOrchestrator

    llm = LLM(
        model_id=os.getenv("KEPLER_EVAL_MODEL", "openai/gpt-4"),
        provider="openai",
        version="v1",
        api_endpoint="https://api.openai.com/v1",
    )
    pipeline = PipelineOrchestrator()
    result = pipeline.process_claim(
        MultimodalInput(
            text=claim_text,
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
    )
    return result.consensus_verdict.final_classification.value


def _evaluate_partition(rows):
    from evaluation.fever_evaluator import normalize_label

    for row in rows:
        claim_id = int(row["id"])
        gold = normalize_label(row["label"])
        try:
            predicted = _predict_label(row["claim"])
        except Exception as exc:
            predicted = "Not Enough Information"
            error = str(exc)
        else:
            error = None
        yield {
            "id": claim_id,
            "gold_label": gold,
            "predicted_label": predicted,
            "correct": gold == normalize_label(predicted),
            "error": error,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FEVER evaluation on Spark")
    parser.add_argument("--input", default="evaluation/data/fever_dev.jsonl")
    parser.add_argument("--output", default="evaluation/results/fever_spark_metrics.json")
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit for smoke tests")
    args = parser.parse_args()

    from pyspark.sql import SparkSession

    from evaluation.fever_evaluator import EvaluationMetrics, save_metrics

    spark = (
        SparkSession.builder.appName("KEPLER-FEVER-Eval")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    lines = spark.read.text(args.input)
    if args.limit:
        lines = lines.limit(args.limit)

    parsed = lines.rdd.map(lambda row: json.loads(row.value))
    results = parsed.mapPartitions(_evaluate_partition).collect()

    total = len(results)
    correct = sum(1 for row in results if row["correct"])
    metrics = EvaluationMetrics(
        total=total,
        correct=correct,
        accuracy=correct / total if total else 0.0,
        per_label={},
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_metrics(metrics, output_path)

    predictions_path = output_path.with_suffix(".predictions.jsonl")
    with open(predictions_path, "w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row) + "\n")

    print(json.dumps(metrics.to_dict(), indent=2))
    spark.stop()


if __name__ == "__main__":
    main()
