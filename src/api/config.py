"""API configuration settings

This module manages environment variables and settings for the REST API.
"""
import os
from typing import List
from pydantic import BaseModel, Field


class APISettings(BaseModel):
    """API configuration settings"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # Environment
    environment: str = Field(default="development", description="Environment (development/production)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        """Pydantic config"""
        env_prefix = "KEPLER_API_"
    
    @classmethod
    def from_env(cls) -> "APISettings":
        """Load settings from environment variables
        
        Returns:
            APISettings instance with values from environment
        """
        return cls(
            host=os.getenv("KEPLER_API_HOST", "0.0.0.0"),
            port=int(os.getenv("KEPLER_API_PORT", "8000")),
            cors_origins=os.getenv("KEPLER_API_CORS_ORIGINS", "*").split(","),
            environment=os.getenv("KEPLER_API_ENVIRONMENT", "development"),
            log_level=os.getenv("KEPLER_API_LOG_LEVEL", "INFO"),
        )
