"""FEVER benchmark evaluation utilities for KEPLER."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


LABEL_MAP = {
    "SUPPORTS": "Supported",
    "REFUTES": "Refuted",
    "NOT ENOUGH INFO": "Not Enough Information",
    "NOT_ENOUGH_INFO": "Not Enough Information",
}


@dataclass
class FeverExample:
    id: int
    claim: str
    label: str


@dataclass
class EvaluationMetrics:
    total: int
    correct: int
    accuracy: float
    per_label: Dict[str, Dict[str, float]]

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "correct": self.correct,
            "accuracy": round(self.accuracy, 4),
            "accuracy_pct": round(self.accuracy * 100, 1),
            "per_label": self.per_label,
        }


def load_fever_jsonl(path: str | Path) -> List[FeverExample]:
    examples: List[FeverExample] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            examples.append(
                FeverExample(
                    id=int(row["id"]),
                    claim=row["claim"],
                    label=row["label"],
                )
            )
    return examples


def normalize_label(label: str) -> str:
    return LABEL_MAP.get(label.upper(), label)


def compute_metrics(
    gold: Iterable[FeverExample],
    predictions: Dict[int, str],
) -> EvaluationMetrics:
    per_label_counts: Dict[str, Dict[str, int]] = {}
    total = 0
    correct = 0

    for example in gold:
        total += 1
        expected = normalize_label(example.label)
        predicted = normalize_label(predictions.get(example.id, "Not Enough Information"))
        is_correct = expected == predicted
        correct += int(is_correct)

        bucket = per_label_counts.setdefault(expected, {"total": 0, "correct": 0})
        bucket["total"] += 1
        bucket["correct"] += int(is_correct)

    per_label = {
        label: {
            "total": counts["total"],
            "correct": counts["correct"],
            "accuracy": counts["correct"] / counts["total"] if counts["total"] else 0.0,
        }
        for label, counts in per_label_counts.items()
    }

    return EvaluationMetrics(
        total=total,
        correct=correct,
        accuracy=correct / total if total else 0.0,
        per_label=per_label,
    )


def save_metrics(metrics: EvaluationMetrics, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(metrics.to_dict(), handle, indent=2)


def evaluate_predictions_file(
    dataset_path: str | Path,
    predictions_path: str | Path,
) -> EvaluationMetrics:
    examples = load_fever_jsonl(dataset_path)
    predictions: Dict[int, str] = {}
    with open(predictions_path, "r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            predictions[int(row["id"])] = row["predicted_label"]
    return compute_metrics(examples, predictions)
