"""Property-based tests for Claim Decomposition Agent

This module tests the ClaimDecompositionAgent to ensure it correctly
decomposes claims according to the specification.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.agents import ClaimDecompositionAgent
from src.models import LLM, AtomicClaim


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
def non_empty_text_strategy(draw):
    """Generate non-empty text strings"""
    # Generate text that contains at least one non-whitespace character
    text = draw(st.text(min_size=1, max_size=1000))
    assume(text.strip())  # Ensure it's not just whitespace
    return text


@st.composite
def compound_claim_strategy(draw):
    """Generate compound claims (multiple factual statements)"""
    # Generate multiple simple statements and join them
    num_statements = draw(st.integers(min_value=2, max_value=5))
    
    # Simple factual statement templates
    templates = [
        "The sky is {color}",
        "Water boils at {temp} degrees",
        "The capital of {country} is {city}",
        "The population is {number}",
        "{person} was born in {year}",
    ]
    
    statements = []
    for _ in range(num_statements):
        template = draw(st.sampled_from(templates))
        
        # Fill in template with random values
        if "{color}" in template:
            statement = template.format(color=draw(st.sampled_from(["blue", "red", "green"])))
        elif "{temp}" in template:
            statement = template.format(temp=draw(st.integers(min_value=0, max_value=200)))
        elif "{country}" in template and "{city}" in template:
            statement = template.format(
                country=draw(st.sampled_from(["France", "Japan", "Brazil"])),
                city=draw(st.sampled_from(["Paris", "Tokyo", "Brasilia"]))
            )
        elif "{number}" in template:
            statement = template.format(number=draw(st.integers(min_value=1000, max_value=1000000)))
        elif "{person}" in template and "{year}" in template:
            statement = template.format(
                person=draw(st.sampled_from(["Einstein", "Newton", "Curie"])),
                year=draw(st.integers(min_value=1800, max_value=2000))
            )
        else:
            statement = template
        
        statements.append(statement)
    
    # Join with "and" or ". " to create compound claim
    connector = draw(st.sampled_from([" and ", ". "]))
    compound_text = connector.join(statements)
    
    return compound_text


# Property 5: Claim extraction non-emptiness
@given(
    text=non_empty_text_strategy(),
    model=llm_strategy(),
)
@settings(max_examples=100)
def test_property_5_claim_extraction_non_emptiness(text, model):
    """**Feature: kepler-fact-verification, Property 5: Claim extraction non-emptiness**
    
    For any non-empty input text, the claim decomposition should produce
    at least one atomic claim.
    
    **Validates: Requirements 2.1**
    """
    # Arrange
    agent = ClaimDecompositionAgent()
    
    # Act
    claims = agent.decompose(text, model)
    
    # Assert
    assert len(claims) >= 1, \
        f"Expected at least one claim from non-empty text, got {len(claims)} claims"
    
    # Verify all claims are AtomicClaim objects
    assert all(isinstance(claim, AtomicClaim) for claim in claims), \
        "All returned items should be AtomicClaim objects"
    
    # Verify all claims have non-empty text
    assert all(claim.text.strip() for claim in claims), \
        "All claims should have non-empty text"


# Property 6: Compound claim decomposition
@given(
    compound_text=compound_claim_strategy(),
    model=llm_strategy(),
)
@settings(max_examples=100)
def test_property_6_compound_claim_decomposition(compound_text, model):
    """**Feature: kepler-fact-verification, Property 6: Compound claim decomposition**
    
    For any input text containing multiple factual statements (compound claim),
    the decomposition should produce more than one atomic claim.
    
    **Validates: Requirements 2.4**
    """
    # Arrange
    agent = ClaimDecompositionAgent()
    
    # Act
    claims = agent.decompose(compound_text, model)
    
    # Assert
    assert len(claims) > 1, \
        f"Expected more than one claim from compound text, got {len(claims)} claims. " \
        f"Text: {compound_text}"
    
    # Verify all claims are AtomicClaim objects
    assert all(isinstance(claim, AtomicClaim) for claim in claims), \
        "All returned items should be AtomicClaim objects"
    
    # Verify all claims reference the parent claim
    assert all(claim.parent_claim == compound_text for claim in claims), \
        "All atomic claims should reference the original compound claim as parent"


# Additional unit tests for specific behaviors
def test_decompose_empty_text():
    """Test that decompose handles empty text correctly"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    # Empty string
    claims = agent.decompose("", model)
    assert len(claims) == 0
    
    # Whitespace only
    claims = agent.decompose("   ", model)
    assert len(claims) == 0


def test_decompose_simple_claim():
    """Test decomposition of a simple, already-atomic claim"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    text = "The Earth orbits the Sun."
    claims = agent.decompose(text, model)
    
    assert len(claims) >= 1
    assert all(isinstance(claim, AtomicClaim) for claim in claims)
    assert all(claim.parent_claim == text for claim in claims)


def test_decompose_compound_claim_with_and():
    """Test decomposition of a compound claim with 'and'"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    text = "The sky is blue and water is wet."
    claims = agent.decompose(text, model)
    
    # Should produce multiple claims
    assert len(claims) > 1
    assert all(isinstance(claim, AtomicClaim) for claim in claims)


def test_decompose_multiple_sentences():
    """Test decomposition of multiple sentences"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    text = "Paris is the capital of France. The Eiffel Tower is in Paris."
    claims = agent.decompose(text, model)
    
    # Should produce multiple claims
    assert len(claims) > 1
    assert all(isinstance(claim, AtomicClaim) for claim in claims)


def test_validate_atomicity_simple_claim():
    """Test atomicity validation for simple claims"""
    agent = ClaimDecompositionAgent()
    
    # Simple atomic claim
    claim = AtomicClaim(
        id="test-1",
        text="The Earth is round.",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    assert agent.validate_atomicity(claim) is True


def test_validate_atomicity_compound_claim():
    """Test atomicity validation rejects compound claims"""
    agent = ClaimDecompositionAgent()
    
    # Compound claim with multiple sentences
    claim = AtomicClaim(
        id="test-2",
        text="The Earth is round. The Moon orbits Earth.",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    assert agent.validate_atomicity(claim) is False


def test_validate_atomicity_empty_claim():
    """Test atomicity validation rejects empty claims"""
    agent = ClaimDecompositionAgent()
    
    # Empty claim
    claim = AtomicClaim(
        id="test-3",
        text="",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    assert agent.validate_atomicity(claim) is False


def test_validate_atomicity_multiple_conjunctions():
    """Test atomicity validation rejects claims with multiple conjunctions"""
    agent = ClaimDecompositionAgent()
    
    # Claim with multiple compound indicators
    claim = AtomicClaim(
        id="test-4",
        text="The sky is blue and water is wet but ice is cold.",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    assert agent.validate_atomicity(claim) is False


def test_claim_has_unique_id():
    """Test that each claim gets a unique ID"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    text = "The sky is blue and water is wet."
    claims = agent.decompose(text, model)
    
    # All IDs should be unique
    ids = [claim.id for claim in claims]
    assert len(ids) == len(set(ids)), "All claim IDs should be unique"


def test_claim_verification_status_is_none():
    """Test that new claims have no verification status"""
    agent = ClaimDecompositionAgent()
    model = LLM("test", "openai", "1.0", "http://test")
    
    text = "The Earth orbits the Sun."
    claims = agent.decompose(text, model)
    
    # All claims should have None verification status initially
    assert all(claim.verification_status is None for claim in claims), \
        "New claims should have no verification status"
