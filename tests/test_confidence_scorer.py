"""Property-based tests for ConfidenceScorer

This module contains property-based tests to verify the correctness properties
of the ConfidenceScorer as specified in the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from src.agents.confidence_scorer import ConfidenceScorer
from src.models.data_models import (
    ConsensusVerdict,
    ConfidenceScore,
    EvidencePiece,
    Verdict,
    VerdictType,
    Source,
    ReasoningChain,
    ReasoningStep,
    Agreement,
    Conflict,
    InformationGap,
)
import uuid


# Test data generators
@st.composite
def source_strategy(draw, with_date=True):
    """Generate random sources"""
    domain_options = [
        "arxiv.org",
        "reuters.com",
        "bbc.com",
        "nytimes.com",
        "example-blog.com",
        "research-journal.edu",
    ]
    
    domain = draw(st.sampled_from(domain_options))
    url = f"https://{domain}/article-{draw(st.integers(min_value=1, max_value=10000))}"
    title = f"Article about {draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))))}"
    
    if with_date:
        # Generate dates within the last 5 years
        days_ago = draw(st.integers(min_value=0, max_value=1825))
        publish_date = datetime.now() - timedelta(days=days_ago)
    else:
        publish_date = None
    
    content_type = draw(st.sampled_from(["text", "image", "video"]))
    
    return Source(
        url=url,
        title=title,
        publish_date=publish_date,
        domain=domain,
        content_type=content_type,
    )


@st.composite
def evidence_piece_strategy(draw, with_scores=True, with_date=True):
    """Generate random evidence pieces"""
    source = draw(source_strategy(with_date=with_date))
    
    summary = f"Summary: {draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N'))))}"
    raw_content = f"Content: {draw(st.text(min_size=20, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N'))))}"
    
    if with_scores:
        relevance_score = draw(st.floats(min_value=0.0, max_value=1.0))
        credibility_score = draw(st.floats(min_value=0.0, max_value=1.0))
        recency_score = draw(st.floats(min_value=0.0, max_value=1.0))
        final_rank_score = draw(st.floats(min_value=0.0, max_value=1.0))
    else:
        relevance_score = None
        credibility_score = None
        recency_score = None
        final_rank_score = None
    
    return EvidencePiece(
        id=str(uuid.uuid4()),
        source=source,
        summary=summary,
        raw_content=raw_content,
        relevance_score=relevance_score,
        credibility_score=credibility_score,
        recency_score=recency_score,
        final_rank_score=final_rank_score,
    )


@st.composite
def evidence_list_strategy(draw, min_size=1, max_size=10, with_scores=True, with_date=True):
    """Generate a list of evidence pieces"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    evidence = []
    
    for i in range(size):
        evidence.append(draw(evidence_piece_strategy(with_scores=with_scores, with_date=with_date)))
    
    return evidence


@st.composite
def verdict_strategy(draw, classification=None):
    """Generate random verdicts"""
    if classification is None:
        classification = draw(st.sampled_from([
            VerdictType.SUPPORTED,
            VerdictType.REFUTED,
            VerdictType.NOT_ENOUGH_INFO,
        ]))
    
    model_id = f"model-{draw(st.integers(min_value=1, max_value=1000))}"
    justification = f"Justification: {draw(st.text(min_size=20, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N'))))}"
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    num_refs = draw(st.integers(min_value=0, max_value=5))
    evidence_refs = [f"https://source{i}.com/article" for i in range(num_refs)]
    
    return Verdict(
        model_id=model_id,
        classification=classification,
        justification=justification,
        confidence=confidence,
        evidence_references=evidence_refs,
    )


@st.composite
def verdict_list_strategy(draw, min_size=1, max_size=10):
    """Generate a list of verdicts"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    verdicts = []
    
    for i in range(size):
        verdicts.append(draw(verdict_strategy()))
    
    return verdicts


@st.composite
def consensus_verdict_strategy(draw):
    """Generate a consensus verdict"""
    verdicts = draw(verdict_list_strategy(min_size=1, max_size=10))
    
    # Use majority classification
    from collections import Counter
    classification_counts = Counter(v.classification for v in verdicts)
    final_classification = classification_counts.most_common(1)[0][0]
    
    consensus_justification = f"Consensus: {draw(st.text(min_size=20, max_size=150, alphabet=st.characters(whitelist_categories=('L', 'N'))))}"
    
    # Calculate agreement level
    agreeing_count = sum(1 for v in verdicts if v.classification == final_classification)
    agreement_level = agreeing_count / len(verdicts)
    
    return ConsensusVerdict(
        final_classification=final_classification,
        consensus_justification=consensus_justification,
        individual_verdicts=verdicts,
        agreement_level=agreement_level,
    )


@st.composite
def reasoning_chain_strategy(draw):
    """Generate a reasoning chain"""
    num_steps = draw(st.integers(min_value=1, max_value=5))
    steps = []
    
    for i in range(num_steps):
        step = ReasoningStep(
            step_number=i + 1,
            description=f"Step {i+1}: {draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))))}",
            evidence_used=[str(uuid.uuid4()) for _ in range(draw(st.integers(min_value=0, max_value=3)))],
            conclusion=f"Conclusion: {draw(st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))))}",
        )
        steps.append(step)
    
    agreements = []
    conflicts = []
    gaps = []
    
    return ReasoningChain(
        steps=steps,
        agreements=agreements,
        conflicts=conflicts,
        gaps=gaps,
    )


# Property 31: Confidence factors influence
@given(
    consensus1=consensus_verdict_strategy(),
    consensus2=consensus_verdict_strategy(),
    evidence1=evidence_list_strategy(min_size=2, max_size=5, with_scores=True, with_date=True),
    evidence2=evidence_list_strategy(min_size=2, max_size=5, with_scores=True, with_date=True),
    reasoning_chain=reasoning_chain_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_31_confidence_factors_influence(
    consensus1, consensus2, evidence1, evidence2, reasoning_chain
):
    """**Feature: kepler-fact-verification, Property 31: Confidence factors influence**
    
    For any two consensus verdicts with different source reliability, model agreement, 
    or evidence recency, the confidence scores should differ accordingly.
    **Validates: Requirements 8.1, 8.2, 8.3**
    """
    scorer = ConfidenceScorer()
    
    # Calculate confidence for both scenarios
    confidence1 = scorer.calculate_confidence(consensus1, evidence1, reasoning_chain)
    confidence2 = scorer.calculate_confidence(consensus2, evidence2, reasoning_chain)
    
    # Check if any factors differ
    source_reliability_differs = abs(
        confidence1.source_reliability - confidence2.source_reliability
    ) > 0.01
    
    model_agreement_differs = abs(
        confidence1.model_agreement - confidence2.model_agreement
    ) > 0.01
    
    evidence_recency_differs = abs(
        confidence1.evidence_recency - confidence2.evidence_recency
    ) > 0.01
    
    # If any factor differs significantly, overall scores should differ
    if source_reliability_differs or model_agreement_differs or evidence_recency_differs:
        # The overall scores should differ
        assert confidence1.overall_score != confidence2.overall_score, \
            "When component factors differ, overall confidence scores should differ"
    
    # Verify that the overall score is influenced by all three factors
    # by checking the formula: 0.35 * source + 0.40 * model + 0.25 * recency
    expected_score1 = (
        0.35 * confidence1.source_reliability +
        0.40 * confidence1.model_agreement +
        0.25 * confidence1.evidence_recency
    )
    
    assert abs(confidence1.overall_score - expected_score1) < 0.001, \
        "Overall score should follow the weighted formula"


# Property 32: Confidence score presence
@given(
    consensus=consensus_verdict_strategy(),
    evidence=evidence_list_strategy(min_size=1, max_size=10, with_scores=True, with_date=True),
    reasoning_chain=reasoning_chain_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_32_confidence_score_presence(consensus, evidence, reasoning_chain):
    """**Feature: kepler-fact-verification, Property 32: Confidence score presence**
    
    For any final output, a confidence score in the range [0.0, 1.0] should be present.
    **Validates: Requirements 8.4**
    """
    scorer = ConfidenceScorer()
    
    # Calculate confidence
    confidence = scorer.calculate_confidence(consensus, evidence, reasoning_chain)
    
    # Verify confidence score is present and in valid range
    assert confidence.overall_score is not None, \
        "Confidence score should be present"
    
    assert 0.0 <= confidence.overall_score <= 1.0, \
        f"Confidence score should be in range [0.0, 1.0], got {confidence.overall_score}"
    
    # Verify all component scores are also in valid range
    assert 0.0 <= confidence.source_reliability <= 1.0, \
        "Source reliability should be in range [0.0, 1.0]"
    
    assert 0.0 <= confidence.model_agreement <= 1.0, \
        "Model agreement should be in range [0.0, 1.0]"
    
    assert 0.0 <= confidence.evidence_recency <= 1.0, \
        "Evidence recency should be in range [0.0, 1.0]"


# Property 33: Source-linked justifications
@given(
    consensus=consensus_verdict_strategy(),
    evidence=evidence_list_strategy(min_size=1, max_size=10, with_scores=True, with_date=True),
    reasoning_chain=reasoning_chain_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_33_source_linked_justifications(consensus, evidence, reasoning_chain):
    """**Feature: kepler-fact-verification, Property 33: Source-linked justifications**
    
    For any structured justification, all referenced evidence should include source URLs.
    **Validates: Requirements 8.5**
    """
    scorer = ConfidenceScorer()
    
    # Calculate confidence
    confidence = scorer.calculate_confidence(consensus, evidence, reasoning_chain)
    
    # Get structured justification
    structured_justification = confidence.structured_justification
    
    # Verify source links are present
    assert structured_justification.source_links is not None, \
        "Source links should be present in structured justification"
    
    assert len(structured_justification.source_links) > 0, \
        "Source links list should not be empty when evidence is provided"
    
    # Verify all source links are valid URLs
    for link in structured_justification.source_links:
        assert isinstance(link, str), \
            "Source link should be a string"
        
        assert link.startswith("http://") or link.startswith("https://"), \
            f"Source link should be a valid URL, got {link}"
    
    # Verify that source links correspond to evidence sources
    evidence_urls = {e.source.url for e in evidence}
    justification_urls = set(structured_justification.source_links)
    
    # All justification URLs should come from evidence
    assert justification_urls.issubset(evidence_urls), \
        "All source links in justification should come from provided evidence"


# Additional unit tests for core functionality

def test_assess_source_reliability_with_scores():
    """Test source reliability assessment with credibility scores"""
    scorer = ConfidenceScorer()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/1",
                title="Article 1",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="Summary 1",
            raw_content="Content 1",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.7,
            final_rank_score=0.8,
        ),
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/2",
                title="Article 2",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="Summary 2",
            raw_content="Content 2",
            relevance_score=0.7,
            credibility_score=0.7,
            recency_score=0.6,
            final_rank_score=0.7,
        ),
    ]
    
    reliability = scorer.assess_source_reliability(evidence)
    
    # Should be average of credibility scores: (0.9 + 0.7) / 2 = 0.8
    assert abs(reliability - 0.8) < 0.001


def test_assess_source_reliability_no_evidence():
    """Test source reliability with no evidence returns neutral score"""
    scorer = ConfidenceScorer()
    
    reliability = scorer.assess_source_reliability([])
    
    assert reliability == 0.5  # Neutral score


def test_assess_source_reliability_no_scores():
    """Test source reliability with no credibility scores returns neutral"""
    scorer = ConfidenceScorer()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/1",
                title="Article 1",
                publish_date=datetime.now(),
                domain="example.com",
                content_type="text",
            ),
            summary="Summary 1",
            raw_content="Content 1",
            relevance_score=None,
            credibility_score=None,
            recency_score=None,
            final_rank_score=None,
        ),
    ]
    
    reliability = scorer.assess_source_reliability(evidence)
    
    assert reliability == 0.5  # Neutral score


def test_assess_model_agreement_unanimous():
    """Test model agreement with unanimous verdicts"""
    scorer = ConfidenceScorer()
    
    verdicts = [
        Verdict(
            model_id=f"model-{i}",
            classification=VerdictType.SUPPORTED,
            justification=f"Justification {i}",
            confidence=0.8,
            evidence_references=[],
        )
        for i in range(5)
    ]
    
    agreement = scorer.assess_model_agreement(verdicts)
    
    assert agreement == 1.0  # Perfect agreement


def test_assess_model_agreement_split():
    """Test model agreement with split verdicts"""
    scorer = ConfidenceScorer()
    
    verdicts = [
        Verdict(
            model_id="model-1",
            classification=VerdictType.SUPPORTED,
            justification="Supported",
            confidence=0.8,
            evidence_references=[],
        ),
        Verdict(
            model_id="model-2",
            classification=VerdictType.SUPPORTED,
            justification="Supported",
            confidence=0.8,
            evidence_references=[],
        ),
        Verdict(
            model_id="model-3",
            classification=VerdictType.REFUTED,
            justification="Refuted",
            confidence=0.7,
            evidence_references=[],
        ),
    ]
    
    agreement = scorer.assess_model_agreement(verdicts)
    
    # 2 out of 3 agree on SUPPORTED
    assert abs(agreement - 0.6667) < 0.01


def test_assess_model_agreement_no_verdicts():
    """Test model agreement with no verdicts"""
    scorer = ConfidenceScorer()
    
    agreement = scorer.assess_model_agreement([])
    
    assert agreement == 0.0


def test_assess_evidence_recency_recent():
    """Test evidence recency with recent evidence"""
    scorer = ConfidenceScorer()
    
    # Evidence from 1 day ago
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/1",
                title="Recent Article",
                publish_date=datetime.now() - timedelta(days=1),
                domain="example.com",
                content_type="text",
            ),
            summary="Summary",
            raw_content="Content",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.9,
            final_rank_score=0.9,
        ),
    ]
    
    recency = scorer.assess_evidence_recency(evidence)
    
    # Should be very high (close to 1.0) for recent evidence
    assert recency > 0.95


def test_assess_evidence_recency_old():
    """Test evidence recency with old evidence"""
    scorer = ConfidenceScorer()
    
    # Evidence from 2 years ago
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/1",
                title="Old Article",
                publish_date=datetime.now() - timedelta(days=730),
                domain="example.com",
                content_type="text",
            ),
            summary="Summary",
            raw_content="Content",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.2,
            final_rank_score=0.7,
        ),
    ]
    
    recency = scorer.assess_evidence_recency(evidence)
    
    # Should be lower for old evidence (e^(-730/365) ≈ 0.135)
    assert recency < 0.2


def test_assess_evidence_recency_no_dates():
    """Test evidence recency with no publish dates returns neutral"""
    scorer = ConfidenceScorer()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://example.com/1",
                title="Article",
                publish_date=None,
                domain="example.com",
                content_type="text",
            ),
            summary="Summary",
            raw_content="Content",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=None,
            final_rank_score=0.8,
        ),
    ]
    
    recency = scorer.assess_evidence_recency(evidence)
    
    assert recency == 0.5  # Neutral score


def test_calculate_confidence_complete():
    """Test complete confidence calculation"""
    scorer = ConfidenceScorer()
    
    # Create test data
    verdicts = [
        Verdict(
            model_id=f"model-{i}",
            classification=VerdictType.SUPPORTED,
            justification=f"Justification {i}",
            confidence=0.85,
            evidence_references=[f"https://source{i}.com"],
        )
        for i in range(3)
    ]
    
    consensus = ConsensusVerdict(
        final_classification=VerdictType.SUPPORTED,
        consensus_justification="All models agree this is supported.",
        individual_verdicts=verdicts,
        agreement_level=1.0,
    )
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url=f"https://source{i}.com",
                title=f"Article {i}",
                publish_date=datetime.now() - timedelta(days=i*10),
                domain=f"source{i}.com",
                content_type="text",
            ),
            summary=f"Summary {i}",
            raw_content=f"Content {i}",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.8,
            final_rank_score=0.85,
        )
        for i in range(3)
    ]
    
    reasoning_chain = ReasoningChain(
        steps=[
            ReasoningStep(
                step_number=1,
                description="Analyzed evidence",
                evidence_used=[e.id for e in evidence],
                conclusion="Evidence supports claim",
            ),
        ],
        agreements=[],
        conflicts=[],
        gaps=[],
    )
    
    confidence = scorer.calculate_confidence(consensus, evidence, reasoning_chain)
    
    # Verify structure
    assert isinstance(confidence, ConfidenceScore)
    assert 0.0 <= confidence.overall_score <= 1.0
    assert 0.0 <= confidence.source_reliability <= 1.0
    assert 0.0 <= confidence.model_agreement <= 1.0
    assert 0.0 <= confidence.evidence_recency <= 1.0
    assert confidence.structured_justification is not None
    assert len(confidence.structured_justification.source_links) == 3


def test_select_key_evidence():
    """Test key evidence selection"""
    scorer = ConfidenceScorer()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url=f"https://source{i}.com",
                title=f"Article {i}",
                publish_date=datetime.now(),
                domain=f"source{i}.com",
                content_type="text",
            ),
            summary=f"Summary {i}",
            raw_content=f"Content {i}",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.8,
            final_rank_score=float(i) / 10.0,  # Scores from 0.0 to 0.9
        )
        for i in range(10)
    ]
    
    key_evidence = scorer._select_key_evidence(evidence, max_pieces=5)
    
    # Should return top 5 pieces
    assert len(key_evidence) == 5
    
    # Should be sorted by rank (highest first)
    for i in range(len(key_evidence) - 1):
        assert key_evidence[i].final_rank_score >= key_evidence[i + 1].final_rank_score


def test_select_key_evidence_fewer_than_max():
    """Test key evidence selection with fewer pieces than max"""
    scorer = ConfidenceScorer()
    
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url=f"https://source{i}.com",
                title=f"Article {i}",
                publish_date=datetime.now(),
                domain=f"source{i}.com",
                content_type="text",
            ),
            summary=f"Summary {i}",
            raw_content=f"Content {i}",
            relevance_score=0.8,
            credibility_score=0.9,
            recency_score=0.8,
            final_rank_score=float(i) / 10.0,
        )
        for i in range(3)
    ]
    
    key_evidence = scorer._select_key_evidence(evidence, max_pieces=5)
    
    # Should return all 3 pieces
    assert len(key_evidence) == 3
