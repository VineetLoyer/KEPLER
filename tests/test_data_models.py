"""Property-based tests for data model validation

This module tests the core data models to ensure they accept valid inputs
and create proper data structures.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from src.models import (
    MultimodalInput,
    ImageMetadata,
    LLM,
)


# Strategies for generating test data
@st.composite
def llm_strategy(draw):
    """Generate valid LLM configurations"""
    return LLM(
        model_id=draw(st.text(min_size=1, max_size=50)),
        provider=draw(st.sampled_from(["openai", "anthropic", "huggingface"])),
        version=draw(st.text(min_size=1, max_size=20)),
        api_endpoint=draw(st.text(min_size=1, max_size=100)),
    )


@st.composite
def image_metadata_strategy(draw):
    """Generate valid image metadata"""
    width = draw(st.integers(min_value=1, max_value=10000))
    height = draw(st.integers(min_value=1, max_value=10000))
    return ImageMetadata(
        format=draw(st.sampled_from(["JPEG", "PNG", "GIF", "WEBP"])),
        size_bytes=draw(st.integers(min_value=1, max_value=100_000_000)),
        dimensions=(width, height),
        hash=draw(st.text(min_size=32, max_size=64)),
    )


# Property 1: Input acceptance for text
@given(
    text=st.text(min_size=1, max_size=10000),
    selected_llms=st.lists(llm_strategy(), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_property_1_input_acceptance_for_text(text, selected_llms):
    """**Feature: kepler-fact-verification, Property 1: Input acceptance for text**
    
    For any valid text string, the system should accept it as input without error
    and create a MultimodalInput object.
    
    **Validates: Requirements 1.1**
    """
    # Arrange
    timestamp = datetime.now()
    decomposition_model = selected_llms[0]
    
    # Act - should not raise any exception
    multimodal_input = MultimodalInput(
        text=text,
        image=None,
        image_metadata=None,
        timestamp=timestamp,
        selected_llms=selected_llms,
        decomposition_model=decomposition_model,
    )
    
    # Assert
    assert multimodal_input is not None
    assert multimodal_input.text == text
    assert multimodal_input.image is None
    assert multimodal_input.timestamp == timestamp
    assert multimodal_input.selected_llms == selected_llms
    assert multimodal_input.decomposition_model == decomposition_model


# Property 2: Input acceptance for images
@given(
    image=st.binary(min_size=1, max_size=100000),
    image_metadata=image_metadata_strategy(),
    selected_llms=st.lists(llm_strategy(), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_property_2_input_acceptance_for_images(image, image_metadata, selected_llms):
    """**Feature: kepler-fact-verification, Property 2: Input acceptance for images**
    
    For any valid image data, the system should accept it as input without error
    and create a MultimodalInput object.
    
    **Validates: Requirements 1.2**
    """
    # Arrange
    timestamp = datetime.now()
    decomposition_model = selected_llms[0]
    
    # Act - should not raise any exception
    multimodal_input = MultimodalInput(
        text=None,
        image=image,
        image_metadata=image_metadata,
        timestamp=timestamp,
        selected_llms=selected_llms,
        decomposition_model=decomposition_model,
    )
    
    # Assert
    assert multimodal_input is not None
    assert multimodal_input.text is None
    assert multimodal_input.image == image
    assert multimodal_input.image_metadata == image_metadata
    assert multimodal_input.timestamp == timestamp
    assert multimodal_input.selected_llms == selected_llms
    assert multimodal_input.decomposition_model == decomposition_model
