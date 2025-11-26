"""Property-based tests for RetrieverAgent

This module contains property-based tests to verify the correctness properties
of the RetrieverAgent as specified in the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from src.agents.retriever_agent import RetrieverAgent, MockSearchClient, MockScraperClient
from src.models.data_models import AtomicClaim, Source
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
def source_strategy(draw):
    """Generate random sources"""
    domain = draw(st.sampled_from(['example.com', 'test.org', 'news.net', 'blog.io']))
    url = f"https://{domain}/article-{draw(st.integers(min_value=1, max_value=1000))}"
    
    # Some sources have publish dates, some don't
    has_date = draw(st.booleans())
    publish_date = None
    if has_date:
        days_ago = draw(st.integers(min_value=1, max_value=365))
        publish_date = datetime.now() - timedelta(days=days_ago)
    
    return Source(
        url=url,
        title=draw(st.text(min_size=5, max_size=100)),
        publish_date=publish_date,
        domain=domain,
        content_type=draw(st.sampled_from(['text', 'image', 'video'])),
    )


@st.composite
def source_list_strategy(draw):
    """Generate list of sources"""
    return draw(st.lists(source_strategy(), min_size=1, max_size=20))


@st.composite
def image_bytes_strategy(draw):
    """Generate random image bytes"""
    # Generate random bytes that could represent an image
    size = draw(st.integers(min_value=100, max_value=1000))
    return draw(st.binary(min_size=size, max_size=size))


# Property 7: Web search invocation
@given(claim=atomic_claim_strategy())
@settings(max_examples=100)
def test_property_7_web_search_invocation(claim):
    """**Feature: kepler-fact-verification, Property 7: Web search invocation**
    
    For any atomic claim, the retriever agent should invoke the web search function at least once.
    **Validates: Requirements 3.1**
    """
    # Create agent with mock client
    agent = RetrieverAgent()
    
    # Track if web_search was called
    original_web_search = agent.web_search
    call_count = [0]
    
    def tracked_web_search(*args, **kwargs):
        call_count[0] += 1
        return original_web_search(*args, **kwargs)
    
    agent.web_search = tracked_web_search
    
    # Retrieve evidence (which should call web_search)
    claim_date = datetime.now()
    evidence = agent.retrieve_evidence(claim, claim_date, has_visual_content=False)
    
    # Verify web_search was called at least once
    assert call_count[0] >= 1, "Web search should be invoked at least once for any atomic claim"


# Property 8: Image search invocation for visual content
@given(
    claim=atomic_claim_strategy(),
    image=image_bytes_strategy(),
)
@settings(max_examples=100)
def test_property_8_image_search_invocation(claim, image):
    """**Feature: kepler-fact-verification, Property 8: Image search invocation for visual content**
    
    For any input containing visual content, the retriever agent should invoke both 
    image search and reverse image search functions.
    **Validates: Requirements 3.2, 3.3**
    """
    # Create agent with mock client
    agent = RetrieverAgent()
    
    # Track if image_search and reverse_image_search were called
    image_search_called = [False]
    reverse_search_called = [False]
    
    original_image_search = agent.image_search
    original_reverse_search = agent.reverse_image_search
    
    def tracked_image_search(*args, **kwargs):
        image_search_called[0] = True
        return original_image_search(*args, **kwargs)
    
    def tracked_reverse_search(*args, **kwargs):
        reverse_search_called[0] = True
        return original_reverse_search(*args, **kwargs)
    
    agent.image_search = tracked_image_search
    agent.reverse_image_search = tracked_reverse_search
    
    # Retrieve evidence with visual content
    claim_date = datetime.now()
    evidence = agent.retrieve_evidence(
        claim, 
        claim_date, 
        has_visual_content=True,
        image=image
    )
    
    # Verify both image search functions were called
    assert image_search_called[0], "Image search should be invoked for visual content"
    assert reverse_search_called[0], "Reverse image search should be invoked for visual content"


# Property 9: Evidence summarization
@given(source=source_strategy())
@settings(max_examples=100)
def test_property_9_evidence_summarization(source):
    """**Feature: kepler-fact-verification, Property 9: Evidence summarization**
    
    For any retrieved source, the evidence passed to subsequent stages should contain 
    a summary field that is non-empty.
    **Validates: Requirements 3.4**
    """
    # Create agent
    agent = RetrieverAgent()
    
    # Scrape and summarize the source
    evidence = agent.scrape_and_summarize(source)
    
    # Verify summary is non-empty
    assert evidence.summary is not None, "Evidence summary should not be None"
    assert len(evidence.summary) > 0, "Evidence summary should be non-empty"
    assert isinstance(evidence.summary, str), "Evidence summary should be a string"


# Property 10: Temporal consistency
@given(
    sources=source_list_strategy(),
    days_in_future=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=100)
def test_property_10_temporal_consistency(sources, days_in_future):
    """**Feature: kepler-fact-verification, Property 10: Temporal consistency**
    
    For any claim with date D and any retrieved evidence, all evidence should have 
    publish_date < D or publish_date = null.
    **Validates: Requirements 3.5**
    """
    # Create agent
    agent = RetrieverAgent()
    
    # Set claim date to be in the future relative to sources
    claim_date = datetime.now() + timedelta(days=days_in_future)
    
    # Filter sources by date
    filtered_sources = agent.filter_by_date(sources, claim_date)
    
    # Verify all filtered sources have publish_date < claim_date or None
    for source in filtered_sources:
        if source.publish_date is not None:
            assert source.publish_date < claim_date, \
                f"Source publish date {source.publish_date} should be before claim date {claim_date}"


# Property 11: Domain exclusion
@given(
    sources=source_list_strategy(),
    blocklist=st.lists(
        st.sampled_from(['snopes.com', 'politifact.com', 'factcheck.org', 'example.com', 'test.org']),
        min_size=1,
        max_size=5,
        unique=True
    ),
)
@settings(max_examples=100)
def test_property_11_domain_exclusion(sources, blocklist):
    """**Feature: kepler-fact-verification, Property 11: Domain exclusion**
    
    For any retrieved evidence and any domain in the exclusion list (fact-checking sites, 
    restricted domains), no evidence should have a source domain matching the exclusion list.
    **Validates: Requirements 3.6, 3.7**
    """
    # Create agent
    agent = RetrieverAgent()
    
    # Exclude domains
    filtered_sources = agent.exclude_domains(sources, blocklist)
    
    # Normalize blocklist for comparison
    blocklist_lower = [domain.lower() for domain in blocklist]
    
    # Verify no filtered source has a domain in the blocklist
    for source in filtered_sources:
        assert source.domain.lower() not in blocklist_lower, \
            f"Source domain {source.domain} should not be in blocklist {blocklist}"


# Additional edge case tests
def test_web_search_returns_sources():
    """Test that web_search returns Source objects"""
    agent = RetrieverAgent()
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The Earth is round",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    sources = agent.web_search(claim)
    
    assert isinstance(sources, list), "web_search should return a list"
    for source in sources:
        assert isinstance(source, Source), "Each item should be a Source object"


def test_filter_by_date_keeps_none_dates():
    """Test that sources with None publish_date are kept"""
    agent = RetrieverAgent()
    
    source_with_none = Source(
        url="https://example.com/article",
        title="Article",
        publish_date=None,
        domain="example.com",
        content_type="text",
    )
    
    claim_date = datetime.now()
    filtered = agent.filter_by_date([source_with_none], claim_date)
    
    assert len(filtered) == 1, "Sources with None publish_date should be kept"


def test_exclude_domains_case_insensitive():
    """Test that domain exclusion is case-insensitive"""
    agent = RetrieverAgent()
    
    source = Source(
        url="https://Snopes.COM/article",
        title="Article",
        publish_date=None,
        domain="Snopes.COM",
        content_type="text",
    )
    
    blocklist = ["snopes.com"]
    filtered = agent.exclude_domains([source], blocklist)
    
    assert len(filtered) == 0, "Domain exclusion should be case-insensitive"


def test_retrieve_evidence_integration():
    """Test the full retrieve_evidence workflow"""
    agent = RetrieverAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The sky is blue",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    claim_date = datetime.now()
    evidence = agent.retrieve_evidence(claim, claim_date, has_visual_content=False)
    
    assert isinstance(evidence, list), "retrieve_evidence should return a list"
    # Evidence list may be empty or contain items depending on mock behavior
    for item in evidence:
        assert hasattr(item, 'summary'), "Each evidence piece should have a summary"
        assert hasattr(item, 'source'), "Each evidence piece should have a source"
