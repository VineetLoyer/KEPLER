"""Property-based tests for AggregatorAgent

This module contains property-based tests to verify the correctness properties
of the AggregatorAgent as specified in the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from src.agents.aggregator_agent import AggregatorAgent
from src.models.data_models import (
    EvidencePiece,
    AtomicClaim,
    Source,
    ConsolidatedEvidence,
    ReasoningChain,
)
import uuid


# Test data generators
@st.composite
def atomic_claim_strategy(draw):
    """Generate random atomic claims"""
    claim_text = draw(st.text(min_size=10, max_size=200))
    return AtomicClaim(
        id=str(uuid.uuid4()),
        text=claim_text,
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )


@st.composite
def source_strategy(draw, content_type=None):
    """Generate random sources"""
    domain = draw(st.sampled_from([
        'example.com', 'test.org', 'news.net', 'blog.io',
        'arxiv.org', 'reuters.com', 'medium.com'
    ]))
    url = f"https://{domain}/article-{draw(st.integers(min_value=1, max_value=1000))}"
    
    # Generate publish date
    days_ago = draw(st.integers(min_value=1, max_value=365))
    publish_date = datetime.now() - timedelta(days=days_ago)
    
    # Use provided content_type or generate one
    if content_type is None:
        content_type = draw(st.sampled_from(['text', 'image', 'video']))
    
    return Source(
        url=url,
        title=draw(st.text(min_size=5, max_size=100)),
        publish_date=publish_date,
        domain=domain,
        content_type=content_type,
    )


@st.composite
def evidence_piece_strategy(draw, content_type=None):
    """Generate random evidence pieces"""
    source = draw(source_strategy(content_type=content_type))
    
    return EvidencePiece(
        id=str(uuid.uuid4()),
        source=source,
        summary=draw(st.text(min_size=10, max_size=200)),
        raw_content=draw(st.text(min_size=50, max_size=500)),
        relevance_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        credibility_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        recency_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        final_rank_score=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


@st.composite
def evidence_list_strategy(draw, min_size=1, max_size=20):
    """Generate list of evidence pieces"""
    return draw(st.lists(
        evidence_piece_strategy(),
        min_size=min_size,
        max_size=max_size
    ))


@st.composite
def multimodal_evidence_strategy(draw):
    """Generate evidence with mixed content types (text, images, metadata)"""
    # Generate at least one of each type
    text_evidence = draw(st.lists(
        evidence_piece_strategy(content_type='text'),
        min_size=1,
        max_size=5
    ))
    
    image_evidence = draw(st.lists(
        evidence_piece_strategy(content_type='image'),
        min_size=1,
        max_size=3
    ))
    
    # Combine them
    all_evidence = text_evidence + image_evidence
    
    return all_evidence


# Property 18: Multimodal evidence consolidation
@given(
    evidence=multimodal_evidence_strategy(),
)
@settings(max_examples=100)
def test_property_18_multimodal_evidence_consolidation(evidence):
    """**Feature: kepler-fact-verification, Property 18: Multimodal evidence consolidation**
    
    For any set of ranked evidence containing text, images, and metadata, the aggregator 
    output should contain consolidated representations of all three types.
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    # Create agent
    agent = AggregatorAgent()
    
    # Consolidate evidence
    consolidated = agent.consolidate_evidence(evidence)
    
    # Verify consolidated evidence has all three types
    assert isinstance(consolidated, ConsolidatedEvidence), \
        "Output should be ConsolidatedEvidence"
    
    # Check textual evidence
    assert isinstance(consolidated.textual_evidence, list), \
        "Textual evidence should be a list"
    
    # Check visual evidence
    assert isinstance(consolidated.visual_evidence, list), \
        "Visual evidence should be a list"
    
    # Check metadata
    assert isinstance(consolidated.metadata, dict), \
        "Metadata should be a dictionary"
    
    # Verify that text evidence is present (we generated at least 1)
    text_count = sum(1 for e in evidence if e.source.content_type == 'text')
    assert len(consolidated.textual_evidence) == text_count, \
        f"Should have {text_count} textual evidence pieces"
    
    # Verify that image evidence is present (we generated at least 1)
    image_count = sum(1 for e in evidence if e.source.content_type == 'image')
    assert len(consolidated.visual_evidence) == image_count, \
        f"Should have {image_count} visual evidence pieces"
    
    # Verify metadata is populated
    assert len(consolidated.metadata) > 0, \
        "Metadata should contain information about sources"


# Property 19: Chain-of-thought generation
@given(
    evidence=evidence_list_strategy(min_size=1, max_size=10),
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_19_chain_of_thought_generation(evidence, claim):
    """**Feature: kepler-fact-verification, Property 19: Chain-of-thought generation**
    
    For any consolidated evidence, the aggregator should produce a ReasoningChain 
    with at least one reasoning step.
    **Validates: Requirements 5.4**
    """
    # Create agent
    agent = AggregatorAgent()
    
    # Consolidate evidence first
    consolidated = agent.consolidate_evidence(evidence)
    
    # Apply chain-of-thought reasoning
    reasoning_chain = agent.apply_chain_of_thought(consolidated, claim)
    
    # Verify reasoning chain is created
    assert isinstance(reasoning_chain, ReasoningChain), \
        "Output should be a ReasoningChain"
    
    # Verify at least one reasoning step exists
    assert len(reasoning_chain.steps) >= 1, \
        "ReasoningChain should have at least one reasoning step"
    
    # Verify reasoning steps have required fields
    for step in reasoning_chain.steps:
        assert step.step_number > 0, "Step number should be positive"
        assert isinstance(step.description, str), "Description should be a string"
        assert len(step.description) > 0, "Description should not be empty"
        assert isinstance(step.evidence_used, list), "Evidence used should be a list"
        assert isinstance(step.conclusion, str), "Conclusion should be a string"


# Property 20: Agreement detection
@given(
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100)
def test_property_20_agreement_detection(claim):
    """**Feature: kepler-fact-verification, Property 20: Agreement detection**
    
    For any set of evidence where multiple pieces support the same assertion, 
    the aggregator should identify and record at least one Agreement.
    **Validates: Requirements 5.5**
    """
    # Create agent
    agent = AggregatorAgent()
    
    # Create evidence with similar content (agreement)
    common_text = "The Earth orbits the Sun"
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url=f"https://source{i}.com/article",
                title=f"Article {i}",
                publish_date=datetime.now(),
                domain=f"source{i}.com",
                content_type="text",
            ),
            summary=f"{common_text} according to scientific evidence",
            raw_content=f"Scientific research shows that {common_text}",
            relevance_score=0.9,
            credibility_score=0.8,
            recency_score=0.7,
            final_rank_score=0.8,
        )
        for i in range(3)  # Create 3 similar pieces
    ]
    
    # Identify agreements
    agreements = agent.identify_agreements(evidence)
    
    # Verify at least one agreement is detected
    assert len(agreements) >= 1, \
        "Should detect at least one agreement when multiple pieces have similar content"
    
    # Verify agreement structure
    for agreement in agreements:
        assert len(agreement.evidence_ids) >= 2, \
            "Agreement should involve at least 2 evidence pieces"
        assert isinstance(agreement.common_assertion, str), \
            "Common assertion should be a string"
        assert len(agreement.common_assertion) > 0, \
            "Common assertion should not be empty"
        assert 0.0 <= agreement.strength <= 1.0, \
            "Agreement strength should be between 0 and 1"


# Property 21: Conflict detection
@given(
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100)
def test_property_21_conflict_detection(claim):
    """**Feature: kepler-fact-verification, Property 21: Conflict detection**
    
    For any set of evidence where pieces contradict each other, the aggregator 
    should identify and record at least one Conflict.
    **Validates: Requirements 5.6**
    """
    # Create agent
    agent = AggregatorAgent()
    
    # Create evidence with conflicting content
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://source1.com/article",
                title="Article 1",
                publish_date=datetime.now(),
                domain="source1.com",
                content_type="text",
            ),
            summary="The Earth is flat according to this theory",
            raw_content="This article claims the Earth is flat",
            relevance_score=0.9,
            credibility_score=0.3,
            recency_score=0.7,
            final_rank_score=0.6,
        ),
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://source2.com/article",
                title="Article 2",
                publish_date=datetime.now(),
                domain="source2.com",
                content_type="text",
            ),
            summary="The Earth is not flat but spherical",
            raw_content="Scientific evidence shows the Earth is not flat",
            relevance_score=0.9,
            credibility_score=0.9,
            recency_score=0.7,
            final_rank_score=0.85,
        ),
    ]
    
    # Identify conflicts
    conflicts = agent.identify_conflicts(evidence)
    
    # Verify at least one conflict is detected
    assert len(conflicts) >= 1, \
        "Should detect at least one conflict when pieces contradict each other"
    
    # Verify conflict structure
    for conflict in conflicts:
        assert len(conflict.evidence_ids) >= 2, \
            "Conflict should involve at least 2 evidence pieces"
        assert isinstance(conflict.conflicting_assertions, list), \
            "Conflicting assertions should be a list"
        assert len(conflict.conflicting_assertions) >= 2, \
            "Should have at least 2 conflicting assertions"
        assert 0.0 <= conflict.severity <= 1.0, \
            "Conflict severity should be between 0 and 1"


# Property 22: Information gap detection
@given(
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100)
def test_property_22_information_gap_detection(claim):
    """**Feature: kepler-fact-verification, Property 22: Information gap detection**
    
    For any claim with aspects not covered by retrieved evidence, the aggregator 
    should identify and record at least one InformationGap.
    **Validates: Requirements 5.7**
    """
    # Create agent
    agent = AggregatorAgent()
    
    # Create a claim with multiple aspects
    specific_claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The Eiffel Tower was built in 1889 and is located in Paris",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    # Create evidence that only covers one aspect (location, not date)
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/article",
                title="Paris Landmarks",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="The Eiffel Tower is located in Paris",
            raw_content="Paris is home to the famous Eiffel Tower",
            relevance_score=0.7,
            credibility_score=0.8,
            recency_score=0.7,
            final_rank_score=0.75,
        ),
    ]
    
    # Identify gaps
    gaps = agent.identify_gaps(evidence, specific_claim)
    
    # Verify at least one gap is detected
    assert len(gaps) >= 1, \
        "Should detect at least one information gap when claim aspects are not covered"
    
    # Verify gap structure
    for gap in gaps:
        assert isinstance(gap.missing_aspect, str), \
            "Missing aspect should be a string"
        assert len(gap.missing_aspect) > 0, \
            "Missing aspect should not be empty"
        assert 0.0 <= gap.importance <= 1.0, \
            "Gap importance should be between 0 and 1"


# Additional unit tests for core functionality

def test_consolidate_evidence_basic():
    """Test basic evidence consolidation"""
    agent = AggregatorAgent()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/text",
                title="Text Article",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="This is a text summary",
            raw_content="This is text content",
            relevance_score=0.8,
            credibility_score=0.7,
            recency_score=0.6,
            final_rank_score=0.7,
        ),
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/image",
                title="Image",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="image",
            ),
            summary="This is an image",
            raw_content="Image data",
            relevance_score=0.7,
            credibility_score=0.6,
            recency_score=0.5,
            final_rank_score=0.6,
        ),
    ]
    
    consolidated = agent.consolidate_evidence(evidence)
    
    assert len(consolidated.textual_evidence) == 1
    assert len(consolidated.visual_evidence) == 1
    assert len(consolidated.metadata) == 2
    assert "example.com" in consolidated.evidence_map


def test_apply_chain_of_thought_basic():
    """Test basic chain-of-thought reasoning"""
    agent = AggregatorAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The sky is blue",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/article",
                title="Sky Colors",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="The sky appears blue due to light scattering",
            raw_content="Scientific explanation of why the sky is blue",
            relevance_score=0.9,
            credibility_score=0.8,
            recency_score=0.7,
            final_rank_score=0.8,
        ),
    ]
    
    consolidated = agent.consolidate_evidence(evidence)
    reasoning_chain = agent.apply_chain_of_thought(consolidated, claim)
    
    assert len(reasoning_chain.steps) >= 1
    assert isinstance(reasoning_chain.agreements, list)
    assert isinstance(reasoning_chain.conflicts, list)
    assert isinstance(reasoning_chain.gaps, list)


def test_identify_agreements_no_evidence():
    """Test agreement detection with insufficient evidence"""
    agent = AggregatorAgent()
    
    # Single piece of evidence - no agreements possible
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/article",
                title="Article",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="Some content",
            raw_content="Some content",
            relevance_score=0.8,
            credibility_score=0.7,
            recency_score=0.6,
            final_rank_score=0.7,
        ),
    ]
    
    agreements = agent.identify_agreements(evidence)
    
    assert len(agreements) == 0, "Should not detect agreements with single evidence piece"


def test_identify_conflicts_no_evidence():
    """Test conflict detection with insufficient evidence"""
    agent = AggregatorAgent()
    
    # Single piece of evidence - no conflicts possible
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/article",
                title="Article",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="Some content",
            raw_content="Some content",
            relevance_score=0.8,
            credibility_score=0.7,
            recency_score=0.6,
            final_rank_score=0.7,
        ),
    ]
    
    conflicts = agent.identify_conflicts(evidence)
    
    assert len(conflicts) == 0, "Should not detect conflicts with single evidence piece"


def test_identify_gaps_full_coverage():
    """Test gap detection when evidence covers all aspects"""
    agent = AggregatorAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The sky is blue",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    # Evidence that covers the claim
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/article",
                title="Sky Colors",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="The sky is blue due to light scattering",
            raw_content="The sky appears blue because of Rayleigh scattering",
            relevance_score=0.9,
            credibility_score=0.8,
            recency_score=0.7,
            final_rank_score=0.8,
        ),
    ]
    
    gaps = agent.identify_gaps(evidence, claim)
    
    # Should have no gaps since evidence covers the claim
    assert len(gaps) == 0, "Should not detect gaps when evidence covers all aspects"
