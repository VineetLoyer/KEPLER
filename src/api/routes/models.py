"""Models endpoint"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    provider: str
    version: str


class ModelsResponse(BaseModel):
    """Models list response"""
    models: List[ModelInfo]


@router.get("/models", response_model=ModelsResponse)
async def get_available_models():
    """Get list of available LLM models
    
    Returns:
        List of available models with metadata
    """
    logger.info("Fetching available models")
    
    return ModelsResponse(
        models=[
            ModelInfo(
                id="gpt-4",
                name="GPT-4",
                provider="OpenAI",
                version="gpt-4"
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="OpenAI",
                version="gpt-3.5-turbo"
            ),
            ModelInfo(
                id="claude-3-opus",
                name="Claude 3 Opus",
                provider="Anthropic",
                version="claude-3-opus-20240229"
            ),
            ModelInfo(
                id="claude-3-sonnet",
                name="Claude 3.5 Sonnet",
                provider="Anthropic",
                version="claude-3-5-sonnet-20240620"
            ),
            ModelInfo(
                id="claude-3-haiku",
                name="Claude 3 Haiku",
                provider="Anthropic",
                version="claude-3-haiku-20240307"
            ),
        ]
    )
