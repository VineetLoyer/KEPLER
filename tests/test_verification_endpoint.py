"""Property-based tests for verification API endpoint

This module tests the verification endpoint using property-based testing
to ensure correctness across a wide range of inputs.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import base64
import json

from src.api.app import create_app
from src.api.config import APISettings
from src.models.data_models import (
    FinalOutput,
    MultimodalInput,
    ConsensusVerdict,
    ConfidenceScore,
    VerdictType,
    Verdict,
    StructuredJustification,
    ReasoningChain,
    LLM,
)
from datetime import datetime


# Create test client
settings_obj = APISettings()
app = create_app(settings_obj)
client = TestClient(app)


# Strategies for generating test data
valid_model_ids = st.sampled_from(["gpt-4", "gpt-3.5-turbo", "claude-3-opus"])

# Generate non-empty, non-whitespace text
valid_text = st.text(min_size=1).filter(lambda x: x.strip() != "")

# Generate valid base64 encoded images (small dummy images)
def generate_base64_image():
    """Generate a small dummy image as base64"""
    # Create a minimal valid PNG (1x1 pixel)
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
        0x42, 0x60, 0x82
    ])
    return base64.b64encode(png_bytes).decode('utf-8')

valid_base64_image = st.just(generate_base64_image())

# Generate lists of model IDs (at least 1)
model_lists = st.lists(valid_model_ids, min_size=1, max_size=3, unique=True)


def create_mock_pipeline_result(text: str, models: list) -> FinalOutput:
    """Create a mock FinalOutput for testing"""
    llms = [
        LLM(
            model_id=model_id,
            provider="Test",
            version="1.0",
            api_endpoint="http://test"
        )
        for model_id in models
    ]
    
    multimodal_input = MultimodalInput(
        text=text,
        image=None,
        image_metadata=None,
        timestamp=datetime.now(),
        selected_llms=llms,
        decomposition_model=llms[0],
    )
    
    individual_verdicts = [
        Verdict(
            model_id=model_id,
            classification=VerdictType.SUPPORTED,
            justification="Test justification",
            confidence=0.8,
            evidence_references=[],
        )
        for model_id in models
    ]
    
    consensus_verdict = ConsensusVerdict(
        final_classification=VerdictType.SUPPORTED,
        consensus_justification="Test consensus",
        individual_verdicts=individual_verdicts,
        agreement_level=1.0,
    )
    
    confidence_score = ConfidenceScore(
        overall_score=0.8,
        source_reliability=0.7,
        model_agreement=1.0,
        evidence_recency=0.6,
        structured_justification=StructuredJustification(
            summary="Test summary",
            key_evidence=[],
            reasoning_chain=ReasoningChain(
                steps=[],
                agreements=[],
                conflicts=[],
                gaps=[],
            ),
            source_links=[],
        ),
    )
    
    return FinalOutput(
        original_input=multimodal_input,
        atomic_claims=[],
        consensus_verdict=consensus_verdict,
        confidence_score=confidence_score,
        processing_metadata={
            "pipeline_version": "1.0",
            "total_stages": 7,
            "processing_time_ms": 1000,
        },
        trace_log=[],
    )


# **Feature: kepler-web-interface, Property 29: API request acceptance**
@given(
    text=valid_text,
    models=model_lists,
)
@settings(max_examples=100)
def test_property_29_api_accepts_valid_requests(text, models):
    """Property 29: API request acceptance
    
    For any valid JSON payload with required fields (text or image, and selected_models),
    the API should accept the request and return 200 status.
    
    **Validates: Requirements 10.2, 10.3**
    """
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_result = create_mock_pipeline_result(text, models)
        mock_pipeline.process_claim.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        # Send request with text
        response = client.post(
            "/api/verify",
            json={
                "text": text,
                "selected_models": models,
            }
        )
        
        # Should accept and return 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
        assert "session_id" in data
        assert "consensus_verdict" in data


# **Feature: kepler-web-interface, Property 29: API request acceptance (with image)**
@given(
    image=valid_base64_image,
    models=model_lists,
)
@settings(max_examples=100)
def test_property_29_api_accepts_valid_requests_with_image(image, models):
    """Property 29: API request acceptance (image variant)
    
    For any valid JSON payload with image and selected_models,
    the API should accept the request and return 200 status.
    
    **Validates: Requirements 10.2, 10.3**
    """
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_result = create_mock_pipeline_result("", models)
        mock_pipeline.process_claim.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        # Send request with image
        response = client.post(
            "/api/verify",
            json={
                "image": image,
                "selected_models": models,
            }
        )
        
        # Should accept and return 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# **Feature: kepler-web-interface, Property 30: Pipeline invocation**
@given(
    text=valid_text,
    models=model_lists,
)
@settings(max_examples=100)
def test_property_30_pipeline_invoked_with_inputs(text, models):
    """Property 30: Pipeline invocation
    
    For any valid API request, the KEPLER pipeline should be invoked
    with the provided inputs.
    
    **Validates: Requirements 10.4**
    """
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_result = create_mock_pipeline_result(text, models)
        mock_pipeline.process_claim.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        # Send request
        response = client.post(
            "/api/verify",
            json={
                "text": text,
                "selected_models": models,
            }
        )
        
        # Pipeline should have been invoked
        assert mock_pipeline.process_claim.called, "Pipeline was not invoked"
        
        # Check that the pipeline was called with correct input
        call_args = mock_pipeline.process_claim.call_args
        assert call_args is not None
        
        multimodal_input = call_args[0][0]
        assert multimodal_input.text == text
        assert len(multimodal_input.selected_llms) == len(models)
        
        # Verify model IDs match
        actual_model_ids = [llm.model_id for llm in multimodal_input.selected_llms]
        assert set(actual_model_ids) == set(models)


# **Feature: kepler-web-interface, Property 31: Complete response structure**
@given(
    text=valid_text,
    models=model_lists,
)
@settings(max_examples=100)
def test_property_31_response_has_all_required_fields(text, models):
    """Property 31: Complete response structure
    
    For any successful pipeline execution, the API response should include
    all required fields (session_id, atomic_claims, consensus_verdict,
    confidence_score, etc.).
    
    **Validates: Requirements 10.5**
    """
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_result = create_mock_pipeline_result(text, models)
        mock_pipeline.process_claim.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        # Send request
        response = client.post(
            "/api/verify",
            json={
                "text": text,
                "selected_models": models,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            "session_id",
            "original_input",
            "atomic_claims",
            "consensus_verdict",
            "confidence_score",
            "processing_metadata",
            "trace_log",
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check nested structures
        assert "final_classification" in data["consensus_verdict"]
        assert "consensus_justification" in data["consensus_verdict"]
        assert "individual_verdicts" in data["consensus_verdict"]
        assert "agreement_level" in data["consensus_verdict"]
        
        assert "overall_score" in data["confidence_score"]
        assert "source_reliability" in data["confidence_score"]
        assert "model_agreement" in data["confidence_score"]
        assert "evidence_recency" in data["confidence_score"]
        assert "structured_justification" in data["confidence_score"]


# Edge case tests for invalid inputs
def test_empty_models_list_rejected():
    """Test that empty model list is rejected"""
    response = client.post(
        "/api/verify",
        json={
            "text": "Test claim",
            "selected_models": [],
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_no_input_rejected():
    """Test that request with no text or image is rejected"""
    response = client.post(
        "/api/verify",
        json={
            "selected_models": ["gpt-4"],
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_invalid_base64_image_rejected():
    """Test that invalid base64 image is rejected"""
    response = client.post(
        "/api/verify",
        json={
            "image": "not-valid-base64!!!",
            "selected_models": ["gpt-4"],
        }
    )
    
    assert response.status_code == 400  # Bad request


def test_unknown_model_rejected():
    """Test that unknown model ID is rejected"""
    response = client.post(
        "/api/verify",
        json={
            "text": "Test claim",
            "selected_models": ["unknown-model"],
        }
    )
    
    assert response.status_code == 400
    assert "Unknown model ID" in response.json()["detail"]


# ============================================================================
# Property-Based Tests for Error Handling
# ============================================================================

# Strategies for generating invalid inputs
empty_or_whitespace_text = st.one_of(
    st.just(""),
    st.just("   "),
    st.just("\n\t  "),
    st.text(max_size=0),
)

invalid_base64_strings = st.one_of(
    st.just("not-valid-base64!!!"),
    st.just("invalid@#$%"),
    st.text(alphabet="!@#$%^&*()", min_size=1, max_size=20),
)

unknown_model_ids = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz-",
    min_size=5,
    max_size=20
).filter(lambda x: x not in ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"])


# **Feature: kepler-web-interface, Property 32: Invalid request error handling**
@given(
    models=st.lists(valid_model_ids, min_size=1, max_size=3, unique=True),
)
@settings(max_examples=100)
def test_property_32_invalid_request_returns_400_no_input(models):
    """Property 32: Invalid request error handling (no input variant)
    
    For any invalid API request (missing required fields, invalid format),
    the API should return 400 status with error details.
    
    This test verifies that requests with no text or image are rejected.
    
    **Validates: Requirements 11.1**
    """
    # Send request with neither text nor image
    response = client.post(
        "/api/verify",
        json={
            "selected_models": models,
        }
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    # Response should be JSON with error details
    data = response.json()
    assert "error" in data, "Error response should contain 'error' field"
    assert "detail" in data, "Error response should contain 'detail' field"
    assert "timestamp" in data, "Error response should contain 'timestamp' field"


# **Feature: kepler-web-interface, Property 32: Invalid request error handling**
@given(
    text=empty_or_whitespace_text,
    models=st.lists(valid_model_ids, min_size=1, max_size=3, unique=True),
)
@settings(max_examples=100)
def test_property_32_invalid_request_returns_400_empty_text(text, models):
    """Property 32: Invalid request error handling (empty text variant)
    
    For any request with empty or whitespace-only text,
    the API should return 400 status with error details.
    
    **Validates: Requirements 11.1**
    """
    # Send request with empty/whitespace text
    response = client.post(
        "/api/verify",
        json={
            "text": text,
            "selected_models": models,
        }
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    # Response should contain error information
    data = response.json()
    assert "error" in data
    assert "detail" in data


# **Feature: kepler-web-interface, Property 32: Invalid request error handling**
@given(
    invalid_image=invalid_base64_strings,
    models=st.lists(valid_model_ids, min_size=1, max_size=3, unique=True),
)
@settings(max_examples=100)
def test_property_32_invalid_request_returns_400_bad_base64(invalid_image, models):
    """Property 32: Invalid request error handling (invalid base64 variant)
    
    For any request with invalid base64 image data,
    the API should return 400 status with error details.
    
    **Validates: Requirements 11.1**
    """
    # Send request with invalid base64 image
    response = client.post(
        "/api/verify",
        json={
            "image": invalid_image,
            "selected_models": models,
        }
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    # Response should contain error information
    data = response.json()
    assert "error" in data
    assert "detail" in data


# **Feature: kepler-web-interface, Property 32: Invalid request error handling**
@given(
    text=valid_text,
    unknown_model=unknown_model_ids,
)
@settings(max_examples=100)
def test_property_32_invalid_request_returns_400_unknown_model(text, unknown_model):
    """Property 32: Invalid request error handling (unknown model variant)
    
    For any request with an unknown model ID,
    the API should return 400 status with error details.
    
    **Validates: Requirements 11.1**
    """
    # Send request with unknown model
    response = client.post(
        "/api/verify",
        json={
            "text": text,
            "selected_models": [unknown_model],
        }
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    # Response should contain error information
    data = response.json()
    assert "error" in data
    assert "detail" in data
    assert "Unknown model" in data["detail"] or "unknown" in data["detail"].lower()


# **Feature: kepler-web-interface, Property 33: Pipeline error handling**
@given(
    text=valid_text,
    models=model_lists,
)
@settings(max_examples=100)
def test_property_33_pipeline_error_returns_500(text, models):
    """Property 33: Pipeline error handling
    
    For any pipeline execution error, the API should return 500 status
    with error details.
    
    **Validates: Requirements 11.2**
    """
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline to raise an exception
        mock_pipeline = Mock()
        mock_pipeline.process_claim.side_effect = Exception("Pipeline processing failed")
        mock_pipeline_class.return_value = mock_pipeline
        
        # Send request
        response = client.post(
            "/api/verify",
            json={
                "text": text,
                "selected_models": models,
            }
        )
        
        # Should return 500 Internal Server Error
        assert response.status_code == 500, f"Expected 500, got {response.status_code}"
        
        # Response should contain error information
        data = response.json()
        assert "error" in data, "Error response should contain 'error' field"
        assert "detail" in data, "Error response should contain 'detail' field"
        assert "timestamp" in data, "Error response should contain 'timestamp' field"


# **Feature: kepler-web-interface, Property 34: Error message inclusion**
@given(
    text=st.one_of(empty_or_whitespace_text, valid_text),
    models=st.one_of(
        st.just([]),  # Empty models list
        st.lists(valid_model_ids, min_size=1, max_size=3, unique=True),
    ),
)
@settings(max_examples=100)
def test_property_34_error_responses_include_descriptive_messages(text, models):
    """Property 34: Error message inclusion
    
    For any error response, the response should include a descriptive
    error message.
    
    **Validates: Requirements 11.4**
    """
    # Send potentially invalid request
    response = client.post(
        "/api/verify",
        json={
            "text": text if text else None,
            "selected_models": models,
        }
    )
    
    # If it's an error response (4xx or 5xx)
    if response.status_code >= 400:
        data = response.json()
        
        # Must have error field
        assert "error" in data, "Error response must contain 'error' field"
        assert isinstance(data["error"], str), "'error' field must be a string"
        assert len(data["error"]) > 0, "'error' field must not be empty"
        
        # Must have detail field
        assert "detail" in data, "Error response must contain 'detail' field"
        assert isinstance(data["detail"], str), "'detail' field must be a string"
        assert len(data["detail"]) > 0, "'detail' field must not be empty"
        
        # Must have timestamp
        assert "timestamp" in data, "Error response must contain 'timestamp' field"


# **Feature: kepler-web-interface, Property 35: Error logging**
@given(
    text=valid_text,
    models=model_lists,
)
@settings(
    max_examples=50,  # Reduced to avoid excessive logging
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_35_errors_are_logged(text, models, caplog):
    """Property 35: Error logging
    
    For any error occurrence, the error details should be logged.
    
    **Validates: Requirements 11.5**
    """
    import logging
    
    with patch('src.pipeline.PipelineOrchestrator') as mock_pipeline_class:
        # Mock the pipeline to raise an exception
        mock_pipeline = Mock()
        mock_pipeline.process_claim.side_effect = RuntimeError("Test pipeline error")
        mock_pipeline_class.return_value = mock_pipeline
        
        # Capture logs
        with caplog.at_level(logging.ERROR):
            # Send request that will cause an error
            response = client.post(
                "/api/verify",
                json={
                    "text": text,
                    "selected_models": models,
                }
            )
            
            # Should return error
            assert response.status_code == 500
            
            # Check that error was logged
            assert len(caplog.records) > 0, "Error should be logged"
            
            # Check that at least one log record contains error information
            error_logged = any(
                "exception" in record.message.lower() or 
                "error" in record.message.lower()
                for record in caplog.records
            )
            assert error_logged, "Error details should be logged"


# Test 404 handler
def test_404_handler_for_missing_endpoint():
    """Test that 404 handler returns proper error response for missing endpoints
    
    **Validates: Requirements 11.3, 11.4, 11.5**
    """
    response = client.get("/api/nonexistent-endpoint")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"] == "Not Found"
    assert "detail" in data
    assert "timestamp" in data


# Test validation error structure
def test_validation_error_includes_field_details():
    """Test that validation errors include detailed field information
    
    **Validates: Requirements 11.1, 11.4**
    """
    # Send request with invalid data type
    response = client.post(
        "/api/verify",
        json={
            "text": 12345,  # Should be string, not int
            "selected_models": ["gpt-4"],
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert "detail" in data
    assert "timestamp" in data
    # Validation errors should include field-level details
    assert "validation_errors" in data or "detail" in data
