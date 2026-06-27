# Architecture

This document describes how KEPLER is structured for production-scale fact verification: an eight-stage agent pipeline, distributed orchestration with Kafka and Spark, and fault-tolerant ingestion across heterogeneous external sources.

## Design Goals

1. **Modularity** — each pipeline stage is a replaceable agent with a narrow interface
2. **Traceability** — every stage emits structured events to a per-claim trace log
3. **Throughput** — Kafka decouples stages so slow retrieval does not block verification workers
4. **Fault tolerance** — retries, rate-limit awareness, graceful degradation, and dead-letter routing
5. **Reproducibility** — Spark batch jobs replay the same agent logic for benchmark evaluation

## Eight-Stage Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. Input     │───►│ 2. Claim     │───►│ 3. Evidence  │───►│ 4. Evidence  │
│ Processing   │    │ Decomposition│    │ Retrieval    │    │ Reranking    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                    │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────▼──────┐
│ 8. Confidence│◄───│ 7. Consensus │◄───│ 6. Multi-    │◄───│ 5. Evidence  │
│ Scoring      │    │ Aggregation  │    │ Model Verify │    │ Aggregation  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

| Stage | Kafka topic (example) | Input | Output |
|-------|------------------------|-------|--------|
| 1 — Input Processing | `kepler.input.validated` | Raw claim + models | Validated `MultimodalInput` |
| 2 — Claim Decomposition | `kepler.claims.atomic` | Multimodal input | List of `AtomicClaim` |
| 3 — Evidence Retrieval | `kepler.evidence.raw` | Atomic claim | Raw `EvidencePiece` list |
| 4 — Evidence Reranking | `kepler.evidence.ranked` | Raw evidence | Ranked, filtered evidence |
| 5 — Evidence Aggregation | `kepler.evidence.consolidated` | Ranked evidence | `ConsolidatedEvidence` + reasoning |
| 6 — Multi-Model Verification | `kepler.verdicts.individual` | Claim + evidence | Per-model `Verdict` list |
| 7 — Consensus Aggregation | `kepler.verdicts.consensus` | Individual verdicts | `ConsensusVerdict` |
| 8 — Confidence Scoring | `kepler.results.final` | Consensus + evidence | `FinalOutput` |

In local and API mode, `PipelineOrchestrator` (`src/pipeline.py`) runs these stages in-process. In production, each stage is a consumer/producer pair bound to the topics above.

## Distributed Processing

### Apache Kafka

Kafka provides asynchronous handoff between stages:

- **Backpressure** — slow downstream stages do not block upstream producers
- **Horizontal scaling** — add workers per stage independently (e.g., more retrievers during traffic spikes)
- **Replay** — reprocess claims from any topic offset for debugging or model upgrades
- **Dead-letter queue (DLQ)** — claims that fail after max retries are published to `kepler.dlq.failed` with the full trace context

Stage workers share the agent implementations in `src/agents/`; Kafka adapters wrap the same `process_*` methods used by the orchestrator.

### Apache Spark

Spark runs batch evaluation over large claim datasets (FEVER dev/test splits):

- Claims are partitioned across executors
- Each partition invokes the verification pipeline (or a stage subset) in parallel
- Metrics (accuracy, latency percentiles, error rates) are aggregated in the driver

This separation keeps interactive API latency low while still supporting rigorous benchmark runs at scale.

## Ingestion Layer

The retriever stage integrates **10+ data sources** through a unified `SearchClient` / `ScraperClient` protocol:

| Source | Purpose |
|--------|---------|
| Google Custom Search | Primary web evidence retrieval |
| Bing Search | Fallback search provider |
| Web scraper | Full-page content extraction and summarization |
| Image search | Visual evidence for multimodal claims |
| Reverse image search | Verify image provenance and matches |
| Google Vision | Image understanding and OCR |
| OpenAI / Anthropic | LLM-based decomposition and verification |
| Wikipedia API | Structured encyclopedic evidence (evaluation mode) |
| Domain credibility DB | 100+ curated domains with tiered trust scores |
| Fact-check domain filters | Snopes, PolitiFact, FactCheck.org, etc. |

All external calls flow through shared retry utilities (`src/utils/retry.py`) that classify transient errors (timeouts, 429 rate limits, 5xx responses) and apply exponential backoff with a configurable ceiling.

## Resilience Patterns

### Rate limiting

Search and LLM providers return HTTP 429 or explicit rate-limit errors. The retry layer detects these patterns and increases inter-request delay before retrying, preventing thundering-herd retries across workers.

### Graceful degradation

When retrieval fails after all retries, the pipeline continues with empty evidence and returns `NOT_ENOUGH_INFO` rather than failing the entire request. Reranking and aggregation stages skip gracefully when input lists are empty.

### Retry with exponential backoff

```python
@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, max_delay=60.0)
def call_external_service(...):
    ...
```

After `RetryExhaustedError`, the claim is either routed to the Kafka DLQ or recorded in the trace log with `status: failed_graceful_degradation`.

### Latency optimization (~40% reduction)

Compared to a naive sequential design, KEPLER reduces end-to-end latency by:

- Running multi-model verification in parallel (Stage 6)
- Overlapping retrieval queries for independent atomic claims
- Short-circuiting reranking when evidence count is below threshold
- Caching domain credibility lookups in the reranker agent

## Observability

Each stage writes to the claim trace log:

```json
{
  "stage": "evidence_retrieval",
  "event": "stage_complete",
  "status": "success",
  "elapsed_ms": 842,
  "num_evidence_pieces": 12
}
```

Traces can be exported via the CLI (`--trace trace.json`) or returned in API responses for frontend inspection.

## Repository Layout vs. Deployment

| Component | Location | Role |
|-----------|----------|------|
| Agent implementations | `src/agents/` | Core business logic for all 8 stages |
| Orchestrator | `src/pipeline.py` | In-process stage coordination + trace logging |
| REST API | `src/api/` | Synchronous claim submission for the web UI |
| Web UI | `frontend/` | React client for interactive verification |
| Evaluation | `evaluation/` | FEVER benchmark methodology and results |
| Kafka/Spark workers | Deployment-specific | Wrap agents as stream/batch consumers |

This repository contains the verification engine, API, frontend, and evaluation documentation. Kafka topic bindings and Spark driver scripts are deployment artifacts that consume the agents defined here.
