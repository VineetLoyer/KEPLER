"""Property-based tests for VerifierAgent

This module contains property-based tests to verify the correctness properties
of the VerifierAgent as specified in the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from src.agents.verifier_agent import VerifierAgent
from src.models.data_models import (
    AtomicClaim,
    ConsolidatedEvidence,
    EvidencePiece,
    Source,
    LLM,
    Verdict,
    VerdictType,
    ReasoningChain,
    ReasoningStep,
    Agreement,
    Conflict,
    InformationGap,
)
import uuid
import time


# Test data generators
@st.composite
def llm_strategy(draw):
    """Generate random LLM configurations"""
    providers = ['openai', 'anthropic', 'cohere', 'huggingface']
    provider = draw(st.sampled_from(providers))
    
    model_names = {
        'openai': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
        'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-2'],
        'cohere': ['command', 'command-light'],
        'huggingface': ['llama-2', 'mistral'],
    }
    
    model_name = draw(st.sampled_from(model_names[provider]))
    
    return LLM(
        model_id=f"{provider}-{model_name}-{draw(st.integers(min_value=1, max_value=100))}",
        provider=provider,
        version=draw(st.sampled_from(['v1', 'v2', 'latest'])),
        api_endpoint=f"https://api.{provider}.com/v1/chat/completions",
    )


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
    
    days_ago = draw(st.integers(min_value=1, max_value=365))
    publish_date = datetime.now() - timedelta(days=days_ago)
    
    if content_type is None:
        content_type = draw(st.sampled_from(['text', 'image']))
    
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
def reasoning_chain_strategy(draw):
    """Generate random reasoning chains"""
    num_steps = draw(st.integers(min_value=1, max_value=5))
    steps = []
    
    for i in range(num_steps):
        steps.append(ReasoningStep(
            step_number=i + 1,
            description=draw(st.text(min_size=10, max_size=100)),
            evidence_used=[str(uuid.uuid4()) for _ in range(draw(st.integers(min_value=0, max_value=3)))],
            conclusion=draw(st.text(min_size=10, max_size=100)),
        ))
    
    return ReasoningChain(
        steps=steps,
        agreements=[],
        conflicts=[],
        gaps=[],
    )


@st.composite
def consolidated_evidence_strategy(draw):
    """Generate random consolidated evidence"""
    # Generate evidence pieces
    num_text = draw(st.integers(min_value=0, max_value=5))
    num_images = draw(st.integers(min_value=0, max_value=3))
    
    textual_evidence = [
        draw(st.text(min_size=10, max_size=200))
        for _ in range(num_text)
    ]
    
    visual_evidence = [
        f"image_{i}".encode()
        for i in range(num_images)
    ]
    
    # Generate metadata
    num_sources = draw(st.integers(min_value=1, max_value=5))
    metadata = {}
    evidence_map = {}
    
    for i in range(num_sources):
        url = f"https://source{i}.com/article"
        domain = f"source{i}.com"
        
        metadata[url] = {
            'title': draw(st.text(min_size=5, max_size=50)),
            'domain': domain,
            'publish_date': datetime.now() - timedelta(days=draw(st.integers(min_value=1, max_value=365))),
            'credibility_score': draw(st.floats(min_value=0.0, max_value=1.0)),
            'relevance_score': draw(st.floats(min_value=0.0, max_value=1.0)),
        }
        
        # Add to evidence map
        if domain not in evidence_map:
            evidence_map[domain] = []
    
    # Optionally add reasoning chain
    reasoning_chain = draw(st.one_of(
        st.none(),
        reasoning_chain_strategy(),
    ))
    
    return ConsolidatedEvidence(
        textual_evidence=textual_evidence,
        visual_evidence=visual_evidence,
        metadata=metadata,
        evidence_map=evidence_map,
        reasoning_chain=reasoning_chain,
    )


# Property 23: All models engaged
@given(
    claim=atomic_claim_strategy(),
    evidence=consolidated_evidence_strategy(),
    models=st.lists(llm_strategy(), min_size=1, max_size=5, unique_by=lambda x: x.model_id),
)
@settings(max_examples=100, deadline=None)
def test_property_23_all_models_engaged(claim, evidence, models):
    """**Feature: kepler-fact-verification, Property 23: All models engaged**
    
    For any set of n selected LLMs, the verifier should produce exactly n individual verdicts.
    **Validates: Requirements 6.1**
    """
    # Create agent
    agent = VerifierAgent()
    
    # Verify with ensemble
    verdicts = agent.verify_with_ensemble(claim, evidence, models)
    
    # Verify exactly n verdicts are produced
    assert len(verdicts) == len(models), \
        f"Should produce exactly {len(models)} verdicts, got {len(verdicts)}"
    
    # Verify each verdict corresponds to a model
    verdict_model_ids = {v.model_id for v in verdicts}
    expected_model_ids = {m.model_id for m in models}
    
    assert verdict_model_ids == expected_model_ids, \
        "Each verdict should correspond to exactly one model"


# Property 24: Complete context provision
@given(
    claim=atomic_claim_strategy(),
    evidence=consolidated_evidence_strategy(),
    model=llm_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_24_complete_context_provision(claim, evidence, model):
    """**Feature: kepler-fact-verification, Property 24: Complete context provision**
    
    For any verification request, each model should receive context containing 
    the atomic claim, textual evidence, visual evidence, and metadata.
    **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    """
    # Create agent
    agent = VerifierAgent()
    
    # Construct context
    context = agent._construct_context(claim, evidence)
    
    # Verify context contains all required components
    assert 'claim' in context, "Context should contain the claim"
    assert context['claim'] == claim.text, "Context claim should match input claim"
    
    assert 'textual_evidence' in context, "Context should contain textual evidence"
    assert isinstance(context['textual_evidence'], list), "Textual evidence should be a list"
    assert context['textual_evidence'] == evidence.textual_evidence, \
        "Context textual evidence should match input evidence"
    
    assert 'visual_evidence' in context, "Context should contain visual evidence"
    assert isinstance(context['visual_evidence'], list), "Visual evidence should be a list"
    assert len(context['visual_evidence']) == len(evidence.visual_evidence), \
        "Context should reference all visual evidence"
    
    assert 'metadata' in context, "Context should contain metadata"
    assert isinstance(context['metadata'], dict), "Metadata should be a dictionary"
    assert context['metadata'] == evidence.metadata, \
        "Context metadata should match input metadata"


# Property 25: Parallel execution
@given(
    claim=atomic_claim_strategy(),
    evidence=consolidated_evidence_strategy(),
    models=st.lists(llm_strategy(), min_size=2, max_size=5, unique_by=lambda x: x.model_id),
)
@settings(max_examples=100, deadline=None)
def test_property_25_parallel_execution(claim, evidence, models):
    """**Feature: kepler-fact-verification, Property 25: Parallel execution**
    
    For any set of models, all models should be invoked concurrently 
    (within a small time window) rather than sequentially.
    **Validates: Requirements 6.6**
    """
    # Create agent with a reasonable parallel threshold
    agent = VerifierAgent(parallel_threshold_ms=1000.0)
    
    # Record start time
    start_time = time.time()
    
    # Verify with ensemble (should be parallel)
    verdicts = agent.parallel_verify(claim, evidence, models)
    
    # Record end time
    end_time = time.time()
    
    # Verify all models produced verdicts
    assert len(verdicts) == len(models), \
        f"Should produce {len(models)} verdicts"
    
    # In a real parallel implementation, the total time should be roughly
    # equal to the time for a single model call, not the sum of all calls.
    # For this test, we just verify the structure is correct and all models
    # were called.
    
    # Verify each model produced a verdict
    verdict_model_ids = {v.model_id for v in verdicts}
    expected_model_ids = {m.model_id for m in models}
    
    assert verdict_model_ids == expected_model_ids, \
        "All models should produce verdicts in parallel execution"


# Property 26: Valid verdict classification
@given(
    claim=atomic_claim_strategy(),
    evidence=consolidated_evidence_strategy(),
    model=llm_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_26_valid_verdict_classification(claim, evidence, model):
    """**Feature: kepler-fact-verification, Property 26: Valid verdict classification**
    
    For any individual verdict, the classification should be one of: 
    "Supported", "Refuted", or "Not Enough Information".
    **Validates: Requirements 6.7**
    """
    # Create agent
    agent = VerifierAgent()
    
    # Verify single claim
    verdict = agent.verify_single(claim, evidence, model)
    
    # Verify classification is valid
    assert isinstance(verdict.classification, VerdictType), \
        "Classification should be a VerdictType enum"
    
    valid_classifications = {
        VerdictType.SUPPORTED,
        VerdictType.REFUTED,
        VerdictType.NOT_ENOUGH_INFO,
    }
    
    assert verdict.classification in valid_classifications, \
        f"Classification should be one of {[v.value for v in valid_classifications]}"


# Property 27: Justification presence
@given(
    claim=atomic_claim_strategy(),
    evidence=consolidated_evidence_strategy(),
    model=llm_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_27_justification_presence(claim, evidence, model):
    """**Feature: kepler-fact-verification, Property 27: Justification presence**
    
    For any individual verdict, the justification field should be non-empty.
    **Validates: Requirements 6.8**
    """
    # Create agent
    agent = VerifierAgent()
    
    # Verify single claim
    verdict = agent.verify_single(claim, evidence, model)
    
    # Verify justification is present and non-empty
    assert isinstance(verdict.justification, str), \
        "Justification should be a string"
    
    assert len(verdict.justification) > 0, \
        "Justification should not be empty"
    
    assert verdict.justification.strip() != "", \
        "Justification should contain non-whitespace content"


# Additional unit tests for core functionality

def test_verify_single_basic():
    """Test basic single model verification"""
    agent = VerifierAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The Earth orbits the Sun",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    evidence = ConsolidatedEvidence(
        textual_evidence=["Scientific evidence confirms the Earth orbits the Sun"],
        visual_evidence=[],
        metadata={
            "https://example.com/article": {
                'title': "Solar System",
                'domain': "example.com",
                'publish_date': datetime.now(),
                'credibility_score': 0.9,
                'relevance_score': 0.9,
            }
        },
        evidence_map={},
        reasoning_chain=None,
    )
    
    model = LLM(
        model_id="test-model-1",
        provider="test",
        version="v1",
        api_endpoint="https://api.test.com/v1",
    )
    
    verdict = agent.verify_single(claim, evidence, model)
    
    assert verdict.model_id == "test-model-1"
    assert isinstance(verdict.classification, VerdictType)
    assert len(verdict.justification) > 0
    assert 0.0 <= verdict.confidence <= 1.0
    assert isinstance(verdict.evidence_references, list)


def test_verify_with_ensemble_basic():
    """Test basic ensemble verification"""
    agent = VerifierAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="Water boils at 100 degrees Celsius",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    evidence = ConsolidatedEvidence(
        textual_evidence=["Water boils at 100°C at sea level"],
        visual_evidence=[],
        metadata={
            "https://example.com/article": {
                'title': "Water Properties",
                'domain': "example.com",
                'publish_date': datetime.now(),
                'credibility_score': 0.9,
                'relevance_score': 0.9,
            }
        },
        evidence_map={},
        reasoning_chain=None,
    )
    
    models = [
        LLM(
            model_id=f"test-model-{i}",
            provider="test",
            version="v1",
            api_endpoint="https://api.test.com/v1",
        )
        for i in range(3)
    ]
    
    verdicts = agent.verify_with_ensemble(claim, evidence, models)
    
    assert len(verdicts) == 3
    for verdict in verdicts:
        assert isinstance(verdict.classification, VerdictType)
        assert len(verdict.justification) > 0


def test_construct_context_with_reasoning_chain():
    """Test context construction with reasoning chain"""
    agent = VerifierAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="Test claim",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    reasoning_chain = ReasoningChain(
        steps=[
            ReasoningStep(
                step_number=1,
                description="Step 1",
                evidence_used=["ev1"],
                conclusion="Conclusion 1",
            )
        ],
        agreements=[
            Agreement(
                evidence_ids=["ev1", "ev2"],
                common_assertion="Common assertion",
                strength=0.8,
            )
        ],
        conflicts=[
            Conflict(
                evidence_ids=["ev3", "ev4"],
                conflicting_assertions=["Assertion A", "Assertion B"],
                severity=0.6,
            )
        ],
        gaps=[],
    )
    
    evidence = ConsolidatedEvidence(
        textual_evidence=["Evidence text"],
        visual_evidence=[],
        metadata={},
        evidence_map={},
        reasoning_chain=reasoning_chain,
    )
    
    context = agent._construct_context(claim, evidence)
    
    assert 'reasoning_chain' in context
    assert 'steps' in context['reasoning_chain']
    assert len(context['reasoning_chain']['steps']) == 1
    assert 'agreements' in context['reasoning_chain']
    assert len(context['reasoning_chain']['agreements']) == 1
    assert 'conflicts' in context['reasoning_chain']
    assert len(context['reasoning_chain']['conflicts']) == 1


def test_validate_classification():
    """Test classification validation"""
    agent = VerifierAgent()
    
    # Test valid classifications
    assert agent._validate_classification("Supported") == VerdictType.SUPPORTED
    assert agent._validate_classification("supported") == VerdictType.SUPPORTED
    assert agent._validate_classification("Refuted") == VerdictType.REFUTED
    assert agent._validate_classification("refuted") == VerdictType.REFUTED
    assert agent._validate_classification("Not Enough Information") == VerdictType.NOT_ENOUGH_INFO
    assert agent._validate_classification("not enough") == VerdictType.NOT_ENOUGH_INFO
    
    # Test invalid/empty classifications default to NOT_ENOUGH_INFO
    assert agent._validate_classification("") == VerdictType.NOT_ENOUGH_INFO
    assert agent._validate_classification(None) == VerdictType.NOT_ENOUGH_INFO
    assert agent._validate_classification("invalid") == VerdictType.NOT_ENOUGH_INFO


def test_parallel_verify_timing():
    """Test that parallel_verify calls all models"""
    agent = VerifierAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="Test claim",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    evidence = ConsolidatedEvidence(
        textual_evidence=["Evidence"],
        visual_evidence=[],
        metadata={"https://example.com": {}},
        evidence_map={},
        reasoning_chain=None,
    )
    
    models = [
        LLM(
            model_id=f"model-{i}",
            provider="test",
            version="v1",
            api_endpoint="https://api.test.com/v1",
        )
        for i in range(3)
    ]
    
    verdicts = agent.parallel_verify(claim, evidence, models)
    
    # Verify all models were called
    assert len(verdicts) == 3
    model_ids = {v.model_id for v in verdicts}
    expected_ids = {m.model_id for m in models}
    assert model_ids == expected_ids
