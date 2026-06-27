# KEPLER

**Knowledge Extraction Pipeline for Logical Evidence and Reasoning**

Multimodal fact-verification system that decomposes natural-language claims, retrieves and ranks web evidence, and produces calibrated verdicts through multi-LLM consensus. Built for high-throughput, fault-tolerant processing with full stage-level traceability.

## Highlights

| Area | Result |
|------|--------|
| **FEVER benchmark** | **73.3%** label accuracy on the FEVER dev set |
| **Pipeline throughput** | 8-stage distributed architecture with async stage handoff |
| **Latency** | **~40%** reduction vs. sequential baseline via parallel verification and optimized ingestion |
| **Ingestion** | **10+** external data sources with unified fault handling |

## What It Does

KEPLER accepts text or multimodal claims and returns a structured verdict (`SUPPORTED`, `REFUTED`, `NOT_ENOUGH_INFO`) with confidence scores, evidence citations, reasoning chains, and per-model breakdowns. Every stage emits structured trace events for debugging and audit.

**Core capabilities**

- Multimodal input (text + optional image)
- Atomic claim decomposition for compound statements
- Web, image, and reverse-image evidence retrieval
- Domain-aware evidence reranking and credibility scoring
- Parallel multi-LLM verification with consensus aggregation
- Graceful degradation when upstream services fail

## Architecture

Production deployments decouple pipeline stages with **Apache Kafka** for asynchronous, high-throughput claim processing. Batch evaluation on the **FEVER** dataset runs on **Apache Spark**, enabling parallel scoring across large claim sets while reusing the same agent logic.

```
                    ┌─────────────────────────────────────────────┐
  Claim Request ──► │  Kafka Topics (stage-to-stage handoff)     │
                    └─────────────────────────────────────────────┘
                                           │
     ┌─────────────────────────────────────┼─────────────────────────────────────┐
     ▼                                     ▼                                     ▼
 Input ─► Decompose ─► Retrieve ─► Rerank ─► Aggregate ─► Verify ─► Consensus ─► Score
     │                                     │                                     │
     └─────────────────────────────────────┴─────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
              FastAPI + React UI                          Spark (FEVER batch eval)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for stage contracts, resilience patterns, and data-source integration details.

## Eight-Stage Pipeline

Each stage is an independent agent with explicit inputs, outputs, and trace logging. Stages communicate asynchronously in distributed deployments and sequentially in local/API mode.

| Stage | Agent | Responsibility |
|-------|--------|----------------|
| 1 | Input Processor | Validate multimodal input and model selection |
| 2 | Claim Decomposition | Split compound claims into atomic units |
| 3 | Evidence Retrieval | Fetch text, image, and reverse-image evidence |
| 4 | Evidence Reranking | Score relevance, credibility, and recency |
| 5 | Evidence Aggregation | Synthesize multimodal evidence with chain-of-thought |
| 6 | Multi-Model Verification | Run parallel LLM verdicts per claim |
| 7 | Consensus Aggregation | Combine model outputs into a single verdict |
| 8 | Confidence Scoring | Calibrate confidence from agreement and evidence quality |

## Resilience

The ingestion layer is designed for unreliable external APIs and heterogeneous data sources:

- **Automated dependency management** — stages declare upstream/downstream contracts; the orchestrator enforces ordering and partial-result propagation
- **Rate limiting** — detects HTTP 429 / provider rate-limit responses and backs off before retry
- **Exponential backoff retries** — configurable retry with jitter on transient LLM, search, and scrape failures
- **Graceful degradation** — empty or failed retrieval yields `NOT_ENOUGH_INFO` instead of hard failure
- **Dead-letter handling** — claims that exhaust retries are routed to a DLQ topic (Kafka) or captured in the trace log (local mode) for replay and inspection

Integrated data sources include OpenAI, Anthropic, Google Custom Search, Bing Search, Google Vision, web scraping, image search, reverse image search, Wikipedia, and curated domain credibility databases.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Core pipeline | Python 3.9+, modular agent architecture |
| API | FastAPI, Uvicorn, Pydantic |
| Frontend | React 18, TypeScript, Vite |
| Distributed processing | Apache Kafka, Apache Spark |
| LLMs | OpenAI GPT, Anthropic Claude |
| Evidence | Google/Bing Search, web scraping, vision APIs |
| Testing | pytest, Hypothesis (property-based) |
| Deployment | Docker, Railway, Vercel (frontend) |

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for the web UI)
- API keys for OpenAI, Anthropic, and Google Custom Search

### Backend

```bash
git clone https://github.com/<your-org>/KEPLER.git
cd KEPLER

pip install -r requirements.txt
pip install -e .

cp .env.example .env
# Edit .env with your API keys

# CLI verification
python -m src.main --text "Water boils at 100°C at sea level" --models openai:gpt-4

# API server
python start.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The UI expects the API at `http://localhost:8000` by default.

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `GOOGLE_SEARCH_API_KEY` | Yes | Google Custom Search API key |
| `GOOGLE_SEARCH_ENGINE_ID` | Yes | Programmable Search Engine ID |
| `BING_SEARCH_API_KEY` | No | Bing Search fallback |
| `GOOGLE_VISION_API_KEY` | No | Image analysis |

You can also use `config.json` derived from `config.example.json`. Never commit files containing real credentials.

## Python API

```python
from datetime import datetime
from src.pipeline import PipelineOrchestrator
from src.models.data_models import MultimodalInput, LLM

llm = LLM(
    model_id="openai/gpt-4",
    provider="openai",
    version="v1",
    api_endpoint="https://api.openai.com/v1",
)

pipeline = PipelineOrchestrator()
result = pipeline.process_claim(
    MultimodalInput(
        text="The Earth orbits the Sun.",
        image=None,
        image_metadata=None,
        timestamp=datetime.now(),
        selected_llms=[llm],
        decomposition_model=llm,
    )
)

print(result.consensus_verdict.final_classification.value)
print(f"Confidence: {result.confidence_score.overall_score:.1%}")
```

## Evaluation

KEPLER was evaluated on the [FEVER benchmark](https://fever.ai/) (Fact Extraction and VERification) using a Spark-based batch job that runs the same eight-stage pipeline over the dev split.

| Dataset | Metric | Score |
|---------|--------|-------|
| FEVER dev | Label accuracy | **73.3%** |

Details on evaluation methodology and reproducibility are in [evaluation/README.md](evaluation/README.md).

## Distributed Processing (Kafka + Spark)

Install optional dependencies:

```bash
pip install -r requirements-distributed.txt
```

### Kafka — async eight-stage pipeline

Start Kafka locally:

```bash
docker compose -f infrastructure/docker-compose.yml up -d
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

Initialize topics and run one worker per stage (separate terminals):

```bash
python -m src.streaming --stage input_processing --init-topics
python -m src.streaming --stage claim_decomposition
python -m src.streaming --stage evidence_retrieval
# ... repeat for all eight stages (see docs/ARCHITECTURE.md)
```

Submit a claim:

```bash
python -m src.streaming.submit --text "The Eiffel Tower is in Paris."
```

Failed jobs after retries are routed to the `kepler.dlq.failed` dead-letter topic.

### Spark — FEVER batch evaluation

```bash
python evaluation/download_fever.py --split dev

spark-submit evaluation/spark_fever_eval.py \
  --input evaluation/data/fever_dev.jsonl \
  --output evaluation/results/fever_spark_metrics.json
```

Optional Spark containers:

```bash
docker compose -f infrastructure/docker-compose.yml --profile spark up -d
```

## Testing

```bash
# Full suite
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Integration and property-based tests
pytest tests/test_integration.py tests/test_data_models.py -v
```

## Project Structure

```
KEPLER/
├── src/                  # Core pipeline agents, API, and utilities
│   ├── agents/           # Decomposition, retrieval, verification, scoring
│   ├── api/              # FastAPI application
│   ├── streaming/        # Kafka producers, stage workers, DLQ routing
│   ├── models/           # Shared data models
│   └── utils/            # LLM client, search, retry, scraping
├── infrastructure/       # Docker Compose (Kafka, Spark)
├── frontend/             # React web interface
├── tests/                # Unit, integration, and property tests
├── evaluation/           # Spark FEVER evaluation scripts
├── docs/                 # Architecture and design notes
├── tools/                # Cost estimation utilities
├── config.example.json
├── Dockerfile
└── start.py              # Production API entrypoint
```

## License

MIT — see [LICENSE](LICENSE).
