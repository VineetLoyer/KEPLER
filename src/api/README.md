# KEPLER REST API

REST API backend for the KEPLER fact-verification system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the API

### Development Mode
```bash
python -m src.api.server
```

The API will start on `http://localhost:8000` by default.

### Production Mode
```bash
KEPLER_API_ENVIRONMENT=production python -m src.api.server
```

Or using uvicorn directly:
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI Schema: http://localhost:8000/api/openapi.json

## Endpoints

### Health Check
```
GET /api/health
```

Returns the health status and version of the API.

### Verify Claim
```
POST /api/verify
```

Process a fact-verification request. (Implementation in progress)

### Get Available Models
```
GET /api/models
```

Get list of available LLM models for verification.

## Configuration

Environment variables:
- `KEPLER_API_HOST`: API server host (default: 0.0.0.0)
- `KEPLER_API_PORT`: API server port (default: 8000)
- `KEPLER_API_CORS_ORIGINS`: Comma-separated list of allowed CORS origins (default: *)
- `KEPLER_API_ENVIRONMENT`: Environment (development/production, default: development)
- `KEPLER_API_LOG_LEVEL`: Logging level (default: INFO)

## Testing

Run the API tests:
```bash
pytest tests/test_api_setup.py -v
```

## Project Structure

```
src/api/
├── __init__.py          # Package initialization
├── app.py               # FastAPI application factory
├── config.py            # Configuration settings
├── server.py            # Server entry point
└── routes/              # API route modules
    ├── __init__.py
    ├── health.py        # Health check endpoint
    ├── verification.py  # Verification endpoint
    └── models.py        # Models list endpoint
```
