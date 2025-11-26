"""Property-based tests for Input Processing Module

This module tests the InputProcessor to ensure it correctly handles
LLM selection and designation according to the specification.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.services import InputProcessor, InputValidationError
from src.models import LLM


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


# Property 3: LLM selection validity
@given(
    available_models=st.lists(llm_strategy(), min_size=1, max_size=20),
    n=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_property_3_llm_selection_validity(available_models, n):
    """**Feature: kepler-fact-verification, Property 3: LLM selection validity**
    
    For any positive integer n and any pool of available LLMs where n ≤ pool size,
    the system should allow selection of exactly n models from the pool.
    
    **Validates: Requirements 1.4**
    """
    # Arrange
    processor = InputProcessor()
    
    # Only test cases where n <= pool size (as per property specification)
    assume(n <= len(available_models))
    
    # Act
    selected = processor.select_llms(available_models, n)
    
    # Assert
    assert len(selected) == n, f"Expected {n} models, got {len(selected)}"
    assert all(model in available_models for model in selected), \
        "All selected models should be from the available pool"


# Property 4: Decomposition model designation
@given(
    selected_models=st.lists(llm_strategy(), min_size=1, max_size=20),
)
@settings(max_examples=100)
def test_property_4_decomposition_model_designation(selected_models):
    """**Feature: kepler-fact-verification, Property 4: Decomposition model designation**
    
    For any set of selected LLMs, the designated decomposition model should be
    a member of that set.
    
    **Validates: Requirements 1.5**
    """
    # Arrange
    processor = InputProcessor()
    
    # Act
    designated = processor.designate_decomposition_model(selected_models)
    
    # Assert
    assert designated in selected_models, \
        "Designated decomposition model must be a member of selected models"


# Additional edge case tests for input validation
@given(
    text=st.text(min_size=1, max_size=1000),
    selected_llms=st.lists(llm_strategy(), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_accept_input_with_text(text, selected_llms):
    """Test that accept_input works correctly with text input"""
    # Exclude whitespace-only strings - they are not valid claims
    assume(text.strip() != "")
    
    processor = InputProcessor()
    decomposition_model = selected_llms[0]
    
    result = processor.accept_input(
        text=text,
        selected_llms=selected_llms,
        decomposition_model=decomposition_model,
    )
    
    assert result.text == text
    assert result.image is None
    assert result.selected_llms == selected_llms
    assert result.decomposition_model == decomposition_model


@given(
    image=st.binary(min_size=1, max_size=10000),
    selected_llms=st.lists(llm_strategy(), min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_accept_input_with_image(image, selected_llms):
    """Test that accept_input works correctly with image input"""
    processor = InputProcessor()
    decomposition_model = selected_llms[0]
    
    result = processor.accept_input(
        image=image,
        selected_llms=selected_llms,
        decomposition_model=decomposition_model,
    )
    
    assert result.text is None
    assert result.image == image
    assert result.image_metadata is not None
    assert result.selected_llms == selected_llms
    assert result.decomposition_model == decomposition_model


def test_accept_input_rejects_no_input():
    """Test that accept_input rejects when neither text nor image is provided"""
    processor = InputProcessor()
    llm = LLM("test", "openai", "1.0", "http://test")
    
    with pytest.raises(InputValidationError, match="At least one of text or image"):
        processor.accept_input(
            selected_llms=[llm],
            decomposition_model=llm,
        )


def test_accept_input_rejects_empty_llm_list():
    """Test that accept_input rejects empty LLM list"""
    processor = InputProcessor()
    
    with pytest.raises(InputValidationError, match="At least one LLM must be selected"):
        processor.accept_input(
            text="test",
            selected_llms=[],
            decomposition_model=None,
        )


def test_accept_input_rejects_decomposition_model_not_in_selected():
    """Test that accept_input rejects decomposition model not in selected LLMs"""
    processor = InputProcessor()
    llm1 = LLM("test1", "openai", "1.0", "http://test1")
    llm2 = LLM("test2", "anthropic", "1.0", "http://test2")
    
    with pytest.raises(InputValidationError, match="Decomposition model must be one of the selected"):
        processor.accept_input(
            text="test",
            selected_llms=[llm1],
            decomposition_model=llm2,
        )


def test_select_llms_rejects_invalid_n():
    """Test that select_llms rejects invalid n values"""
    processor = InputProcessor()
    llm = LLM("test", "openai", "1.0", "http://test")
    
    # Test n = 0
    with pytest.raises(InputValidationError, match="must be positive"):
        processor.select_llms([llm], 0)
    
    # Test n < 0
    with pytest.raises(InputValidationError, match="must be positive"):
        processor.select_llms([llm], -1)
    
    # Test n > available
    with pytest.raises(InputValidationError, match="Cannot select"):
        processor.select_llms([llm], 5)


def test_designate_decomposition_model_rejects_empty_list():
    """Test that designate_decomposition_model rejects empty list"""
    processor = InputProcessor()
    
    with pytest.raises(InputValidationError, match="Cannot designate model from empty list"):
        processor.designate_decomposition_model([])
