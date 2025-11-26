# KEPLER
Knowledge Extraction Pipeline for Logical Evidence and Reasoning

## Overview

KEPLER is a real-time, multimodal, and interpretable fact-verification system designed to automatically verify factual claims expressed in text or images. The system combines dynamic web retrieval, multi-hop reasoning, and confidence-calibrated verdict generation through a modular pipeline of specialized agents.

## Features

- **Multimodal Input Support**: Process text claims with optional accompanying images
- **Multi-LLM Consensus**: Leverage multiple language models to reduce bias and improve reliability
- **Evidence-Based Verification**: Retrieve and rank evidence from the web using multiple search strategies
- **Complete Traceability**: Every decision is logged and can be inspected at each pipeline stage
- **Confidence Scoring**: Receive confidence scores based on source reliability, model agreement, and evidence recency
- **Graceful Error Handling**: Robust error handling with retry logic and graceful degradation

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd KEPLER

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Configuration

Create a configuration file based on `config.example.json`:

```bash
cp config.example.json config.json
```

Edit `config.json` to add your API keys:

```json
{
  "api": {
    "openai_api_key": "your-openai-api-key",
    "anthropic_api_key": "your-anthropic-api-key",
    "google_search_api_key": "your-google-search-api-key",
    "google_search_engine_id": "your-search-engine-id"
  }
}
```

Alternatively, set environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GOOGLE_SEARCH_API_KEY="your-google-search-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
```

## Usage

### Command Line Interface

Verify a simple text claim:

```bash
python -m src.main --text "The Earth orbits around the Sun" --models openai:gpt-4
```

Verify with multiple models for consensus:

```bash
python -m src.main --text "Water boils at 100°C" --models openai:gpt-4 anthropic:claude-3
```

Verify a claim with an accompanying image:

```bash
python -m src.main --text "This is the Eiffel Tower" --image photo.jpg --models openai:gpt-4v
```

Output results as JSON:

```bash
python -m src.main --text "The Moon is made of cheese" --models openai:gpt-4 --format json
```

Save trace log for debugging:

```bash
python -m src.main --text "Python is a programming language" --models openai:gpt-4 --trace trace.json
```

Use a custom configuration file:

```bash
python -m src.main --text "Test claim" --models openai:gpt-4 --config config.json
```

### Python API

```python
from datetime import datetime
from src.pipeline import PipelineOrchestrator
from src.models.data_models import MultimodalInput, LLM

# Create LLM configurations
llm1 = LLM(
    model_id="openai/gpt-4",
    provider="openai",
    version="v1",
    api_endpoint="https://api.openai.com/v1"
)

llm2 = LLM(
    model_id="anthropic/claude-3",
    provider="anthropic",
    version="v1",
    api_endpoint="https://api.anthropic.com/v1"
)

# Create input
multimodal_input = MultimodalInput(
    text="The Earth is round.",
    image=None,
    image_metadata=None,
    timestamp=datetime.now(),
    selected_llms=[llm1, llm2],
    decomposition_model=llm1
)

# Initialize pipeline
pipeline = PipelineOrchestrator()

# Process claim
final_output = pipeline.process_claim(multimodal_input)

# Access results
print(f"Verdict: {final_output.consensus_verdict.final_classification.value}")
print(f"Confidence: {final_output.confidence_score.overall_score:.2%}")
print(f"Justification: {final_output.consensus_verdict.consensus_justification}")

# Inspect trace log
for entry in final_output.trace_log:
    print(f"{entry['stage']}: {entry['event']}")
```

## Architecture

KEPLER follows a sequential pipeline architecture with seven distinct stages:

1. **Input Processing**: Accept and validate multimodal inputs
2. **Claim Decomposition**: Extract atomic claims from complex input text
3. **Evidence Retrieval**: Collect relevant evidence from the web
4. **Evidence Reranking**: Filter and prioritize evidence by quality
5. **Evidence Aggregation**: Synthesize multimodal evidence with chain-of-thought reasoning
6. **Verification**: Generate verdicts using multiple LLMs in parallel
7. **Confidence Scoring**: Calculate confidence based on multiple factors

Each stage is implemented as an independent agent with complete traceability.

## Testing

Run all tests:

```bash
pytest tests/
```

Run specific test suites:

```bash
# Integration tests
pytest tests/test_integration.py -v

# Pipeline tests
pytest tests/test_pipeline.py -v

# Property-based tests
pytest tests/test_data_models.py -v
```

Run tests with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Development

The project follows a spec-driven development methodology with:

- **Requirements**: Formal requirements using EARS patterns
- **Design**: Comprehensive design with correctness properties
- **Implementation**: Modular agents with clear interfaces
- **Testing**: Both unit tests and property-based tests

See `.kiro/specs/kepler-fact-verification/` for complete specifications.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
