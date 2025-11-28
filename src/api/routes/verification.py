"""Verification endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict, Any
import logging
import base64
import uuid
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


class VerificationRequest(BaseModel):
    """Verification request model"""
    text: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded
    selected_models: List[str]
    
    @field_validator('selected_models')
    @classmethod
    def validate_models(cls, v):
        """Validate that at least one model is selected"""
        if len(v) < 1:
            raise ValueError('At least one model must be selected')
        return v
    
    @model_validator(mode='after')
    def validate_input(self):
        """Validate that either text or image is provided"""
        # Check if text is provided and not empty/whitespace-only
        has_valid_text = self.text and self.text.strip()
        has_image = self.image is not None
        
        if not has_valid_text and not has_image:
            raise ValueError('Either text or image must be provided')
        
        # If text is provided but is whitespace-only, reject it
        if self.text is not None and not self.text.strip():
            raise ValueError('Text cannot be empty or whitespace-only')
        
        return self


class VerificationResponse(BaseModel):
    """Verification response model"""
    session_id: str
    original_input: Dict[str, Any]
    atomic_claims: List[Dict[str, Any]]
    consensus_verdict: Dict[str, Any]
    confidence_score: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    trace_log: List[Dict[str, Any]]


@router.post("/verify", response_model=VerificationResponse)
async def verify_claim(request: VerificationRequest):
    """Process a fact-verification request
    
    Args:
        request: Verification request with claim text/image and selected models
        
    Returns:
        Complete verification results
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        logger.info(f"Received verification request with {len(request.selected_models)} models")
        
        # Decode image if provided
        image_bytes = None
        if request.image:
            try:
                # Validate base64 string before decoding
                image_bytes = base64.b64decode(request.image, validate=True)
                logger.info(f"Decoded image: {len(image_bytes)} bytes")
                
                # Ensure we got some data
                if len(image_bytes) == 0:
                    raise ValueError("Decoded image is empty")
            except Exception as e:
                logger.error(f"Failed to decode base64 image: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")
        
        # Import pipeline components
        from src.pipeline import PipelineOrchestrator
        from src.models.data_models import MultimodalInput, LLM
        
        # Create LLM objects from selected model IDs
        # For now, we'll use a simple mapping - in production this would come from config
        model_mapping = {
            "gpt-4": LLM(
                model_id="gpt-4",
                provider="OpenAI",
                version="gpt-4",
                api_endpoint="https://api.openai.com/v1/chat/completions"
            ),
            "gpt-3.5-turbo": LLM(
                model_id="gpt-3.5-turbo",
                provider="OpenAI",
                version="gpt-3.5-turbo",
                api_endpoint="https://api.openai.com/v1/chat/completions"
            ),
            "claude-3-opus": LLM(
                model_id="claude-3-opus-20240229",  # Use full model ID
                provider="Anthropic",
                version="claude-3-opus-20240229",
                api_endpoint="https://api.anthropic.com/v1/messages"
            ),
            "claude-3-sonnet": LLM(
                model_id="claude-3-5-sonnet-20241022",  # Latest Sonnet version
                provider="Anthropic",
                version="claude-3-5-sonnet-20241022",
                api_endpoint="https://api.anthropic.com/v1/messages"
            ),
            "claude-3-haiku": LLM(
                model_id="claude-3-5-haiku-20241022",  # Latest Haiku version
                provider="Anthropic",
                version="claude-3-5-haiku-20241022",
                api_endpoint="https://api.anthropic.com/v1/messages"
            ),
        }
        
        selected_llms = []
        for model_id in request.selected_models:
            if model_id not in model_mapping:
                raise HTTPException(status_code=400, detail=f"Unknown model ID: {model_id}")
            selected_llms.append(model_mapping[model_id])
        
        # Use first selected model as decomposition model
        decomposition_model = selected_llms[0]
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text=request.text,
            image=image_bytes,
            image_metadata=None,  # TODO: Extract image metadata if needed
            timestamp=datetime.now(),
            selected_llms=selected_llms,
            decomposition_model=decomposition_model,
        )
        
        # Create pipeline orchestrator
        pipeline = PipelineOrchestrator()
        
        # Process the claim
        logger.info("Invoking KEPLER pipeline")
        result = pipeline.process_claim(multimodal_input)
        
        # Convert result to response format
        response = VerificationResponse(
            session_id=str(uuid.uuid4()),
            original_input={
                "text": request.text,
                "has_image": request.image is not None,
                "selected_models": request.selected_models,
                "timestamp": result.original_input.timestamp.isoformat(),
            },
            atomic_claims=[
                {
                    "id": claim.id,
                    "text": claim.text,
                    "is_atomic": claim.is_atomic,
                    "parent_claim": claim.parent_claim,
                    "verification_status": claim.verification_status.value if claim.verification_status else None,
                    "confidence_score": {
                        "overall_score": claim.confidence_score.overall_score,
                        "source_reliability": claim.confidence_score.source_reliability,
                        "model_agreement": claim.confidence_score.model_agreement,
                        "evidence_recency": claim.confidence_score.evidence_recency,
                        "structured_justification": {
                            "summary": claim.confidence_score.structured_justification.summary,
                            "key_evidence": [
                                {
                                    "id": e.id,
                                    "source": {
                                        "url": e.source.url,
                                        "title": e.source.title,
                                        "domain": e.source.domain,
                                    },
                                    "summary": e.summary,
                                    "relevance_score": e.relevance_score,
                                    "credibility_score": e.credibility_score,
                                }
                                for e in claim.confidence_score.structured_justification.key_evidence
                            ],
                            "source_links": claim.confidence_score.structured_justification.source_links,
                        },
                    } if claim.confidence_score else None,
                    "consensus_verdict": {
                        "final_classification": claim.consensus_verdict.final_classification.value,
                        "consensus_justification": claim.consensus_verdict.consensus_justification,
                        "agreement_level": claim.consensus_verdict.agreement_level,
                    } if claim.consensus_verdict else None,
                }
                for claim in result.atomic_claims
            ],
            consensus_verdict={
                "final_classification": result.consensus_verdict.final_classification.value,
                "consensus_justification": result.consensus_verdict.consensus_justification,
                "individual_verdicts": [
                    {
                        "model_id": v.model_id,
                        "classification": v.classification.value,
                        "justification": v.justification,
                        "confidence": v.confidence,
                        "evidence_references": v.evidence_references,
                    }
                    for v in result.consensus_verdict.individual_verdicts
                ],
                "agreement_level": result.consensus_verdict.agreement_level,
            },
            confidence_score={
                "overall_score": result.confidence_score.overall_score,
                "source_reliability": result.confidence_score.source_reliability,
                "model_agreement": result.confidence_score.model_agreement,
                "evidence_recency": result.confidence_score.evidence_recency,
                "structured_justification": {
                    "summary": result.confidence_score.structured_justification.summary,
                    "key_evidence": [
                        {
                            "id": e.id,
                            "source": {
                                "url": e.source.url,
                                "title": e.source.title,
                                "domain": e.source.domain,
                            },
                            "summary": e.summary,
                            "relevance_score": e.relevance_score,
                            "credibility_score": e.credibility_score,
                        }
                        for e in result.confidence_score.structured_justification.key_evidence
                    ],
                    "reasoning_chain": {
                        "steps": [
                            {
                                "step_number": step.step_number,
                                "description": step.description,
                                "evidence_used": step.evidence_used,
                                "conclusion": step.conclusion,
                            }
                            for step in result.confidence_score.structured_justification.reasoning_chain.steps
                        ],
                        "agreements": [
                            {
                                "evidence_ids": a.evidence_ids,
                                "common_assertion": a.common_assertion,
                                "strength": a.strength,
                            }
                            for a in result.confidence_score.structured_justification.reasoning_chain.agreements
                        ],
                        "conflicts": [
                            {
                                "evidence_ids": c.evidence_ids,
                                "conflicting_assertions": c.conflicting_assertions,
                                "severity": c.severity,
                            }
                            for c in result.confidence_score.structured_justification.reasoning_chain.conflicts
                        ],
                        "gaps": [
                            {
                                "missing_aspect": g.missing_aspect,
                                "importance": g.importance,
                            }
                            for g in result.confidence_score.structured_justification.reasoning_chain.gaps
                        ],
                    },
                    "source_links": result.confidence_score.structured_justification.source_links,
                },
            },
            processing_metadata=result.processing_metadata,
            trace_log=result.trace_log,
        )
        
        logger.info(f"Verification complete: {response.consensus_verdict['final_classification']}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Verification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
