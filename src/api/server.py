"""API server entry point

Run with: python -m src.api.server
"""
import uvicorn
from src.api.app import app
from src.api.config import APISettings


def main():
    """Start the API server"""
    settings = APISettings.from_env()
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.environment == "development"),
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
