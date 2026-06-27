# FEVER Benchmark Evaluation

KEPLER is evaluated on the [FEVER dataset](https://fever.ai/) using a **Spark batch job** that partitions claims across executors and runs the same eight-stage verification pipeline used in production.

## Results

| Split | Metric | Score |
|-------|--------|-------|
| FEVER dev | Label accuracy | **73.3%** |

## Quick start

```bash
# Install distributed dependencies (Kafka + Spark clients)
pip install -r requirements-distributed.txt

# Download FEVER dev split
python evaluation/download_fever.py --split dev

# Run Spark evaluation (requires Spark + API keys in .env)
spark-submit evaluation/spark_fever_eval.py \
  --input evaluation/data/fever_dev.jsonl \
  --output evaluation/results/fever_spark_metrics.json
```

Use `--limit 50` for a smoke test before running the full dev set.

## Files

| File | Purpose |
|------|---------|
| `fever_evaluator.py` | Metrics computation and label normalization |
| `spark_fever_eval.py` | PySpark driver that parallelizes pipeline invocations |
| `download_fever.py` | Downloads official FEVER JSONL splits |

## Metrics

The Spark driver writes:

- `evaluation/results/fever_spark_metrics.json` — aggregate accuracy
- `evaluation/results/fever_spark_metrics.predictions.jsonl` — per-claim predictions

See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for how Spark fits into the overall system design.
