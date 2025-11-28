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
                id="gpt-5.1-chat-latest",
                name="GPT-5.1 Chat (Latest)",
                provider="OpenAI",
                version="gpt-5.1-chat-latest"
            ),
            ModelInfo(
                id="gpt-5.1",
                name="GPT-5.1",
                provider="OpenAI",
                version="gpt-5.1"
            ),
            ModelInfo(
                id="gpt-4.1",
                name="GPT-4.1",
                provider="OpenAI",
                version="gpt-4.1"
            ),
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="OpenAI",
                version="gpt-4o"
            ),
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="OpenAI",
                version="gpt-4-turbo"
            ),
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
                id="gpt-3.5-turbo-16k",
                name="GPT-3.5 Turbo 16k",
                provider="OpenAI",
                version="gpt-3.5-turbo-16k"
            ),
            ModelInfo(
                id="claude-opus-4-5",
                name="Claude Opus 4.5",
                provider="Anthropic",
                version="claude-opus-4-5-20251101"
            ),
            ModelInfo(
                id="claude-sonnet-4-5",
                name="Claude Sonnet 4.5",
                provider="Anthropic",
                version="claude-sonnet-4-5-20250929"
            ),
            ModelInfo(
                id="claude-haiku-4-5",
                name="Claude Haiku 4.5",
                provider="Anthropic",
                version="claude-haiku-4-5-20251001"
            ),
        ]
    )

