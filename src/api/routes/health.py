"""Health check endpoint"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint
    
    Returns:
        Health status and API version
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )
