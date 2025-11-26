"""Property-based tests for RerankerAgent

This module contains property-based tests to verify the correctness properties
of the RerankerAgent as specified in the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from src.agents.reranker_agent import RerankerAgent
from src.models.data_models import EvidencePiece, AtomicClaim, Source, DomainCredibility
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
def source_strategy(draw, with_date=True):
    """Generate random sources"""
    domain = draw(st.sampled_from([
        'example.com', 'test.org', 'news.net', 'blog.io',
        'arxiv.org', 'reuters.com', 'medium.com'
    ]))
    url = f"https://{domain}/article-{draw(st.integers(min_value=1, max_value=1000))}"
    
    # Generate publish date if requested
    publish_date = None
    if with_date:
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
def evidence_piece_strategy(draw, with_scores=False):
    """Generate random evidence pieces"""
    source = draw(source_strategy())
    
    relevance_score = None
    credibility_score = None
    recency_score = None
    final_rank_score = None
    
    if with_scores:
        relevance_score = draw(st.floats(min_value=0.0, max_value=1.0))
        credibility_score = draw(st.floats(min_value=0.0, max_value=1.0))
        recency_score = draw(st.floats(min_value=0.0, max_value=1.0))
        final_rank_score = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return EvidencePiece(
        id=str(uuid.uuid4()),
        source=source,
        summary=draw(st.text(min_size=10, max_size=200)),
        raw_content=draw(st.text(min_size=50, max_size=500)),
        relevance_score=relevance_score,
        credibility_score=credibility_score,
        recency_score=recency_score,
        final_rank_score=final_rank_score,
    )


@st.composite
def evidence_list_strategy(draw, with_scores=False):
    """Generate list of evidence pieces"""
    return draw(st.lists(
        evidence_piece_strategy(with_scores=with_scores),
        min_size=1,
        max_size=20
    ))


@st.composite
def domain_credibility_strategy(draw):
    """Generate random domain credibility factors"""
    return DomainCredibility(
        agreement_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        citation_density=draw(st.floats(min_value=0.0, max_value=1.0)),
        authorship_quality=draw(st.floats(min_value=0.0, max_value=1.0)),
        stability=draw(st.floats(min_value=0.0, max_value=1.0)),
        link_authority=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


# Property 12: Relevance-based filtering
@given(
    evidence=evidence_list_strategy(with_scores=False),
    claim=atomic_claim_strategy(),
    threshold=st.floats(min_value=0.1, max_value=0.9),
)
@settings(max_examples=100)
def test_property_12_relevance_based_filtering(evidence, claim, threshold):
    """**Feature: kepler-fact-verification, Property 12: Relevance-based filtering**
    
    For any set of evidence with relevance scores, the reranker output should exclude 
    evidence below a relevance threshold.
    **Validates: Requirements 4.1**
    """
    # Create agent with custom threshold
    agent = RerankerAgent(min_rank_threshold=threshold)
    
    # Rank evidence
    ranked_evidence = agent.rank_evidence(evidence, claim)
    
    # Verify all ranked evidence has final_rank_score >= threshold
    for piece in ranked_evidence:
        assert piece.final_rank_score is not None, "Ranked evidence should have final_rank_score"
        assert piece.final_rank_score >= threshold, \
            f"Evidence with score {piece.final_rank_score} should not pass threshold {threshold}"


# Property 13: Credibility-based ordering
@given(
    evidence=evidence_list_strategy(with_scores=False),
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_13_credibility_based_ordering(evidence, claim):
    """**Feature: kepler-fact-verification, Property 13: Credibility-based ordering**
    
    For any set of evidence with different credibility scores, the reranker output should 
    be ordered such that higher credibility evidence appears before lower credibility evidence.
    **Validates: Requirements 4.2**
    """
    # Skip if we have less than 2 evidence pieces
    assume(len(evidence) >= 2)
    
    # Create agent
    agent = RerankerAgent()
    
    # Rank evidence
    ranked_evidence = agent.rank_evidence(evidence, claim)
    
    # Skip if filtering removed all evidence
    assume(len(ranked_evidence) >= 2)
    
    # Verify ordering: each piece should have final_rank_score >= next piece
    for i in range(len(ranked_evidence) - 1):
        current_score = ranked_evidence[i].final_rank_score
        next_score = ranked_evidence[i + 1].final_rank_score
        
        assert current_score is not None and next_score is not None
        assert current_score >= next_score, \
            f"Evidence should be ordered by rank score: {current_score} >= {next_score}"


# Property 14: Recency influence on ranking
@given(
    claim=atomic_claim_strategy(),
)
@settings(max_examples=100)
def test_property_14_recency_influence_on_ranking(claim):
    """**Feature: kepler-fact-verification, Property 14: Recency influence on ranking**
    
    For any two pieces of evidence with identical relevance and credibility but different 
    publish dates, the more recent evidence should rank higher.
    **Validates: Requirements 4.3**
    """
    # Create two evidence pieces with identical content but different dates
    base_date = datetime.now() - timedelta(days=100)
    recent_date = datetime.now() - timedelta(days=10)
    
    # Create identical sources except for publish date
    old_source = Source(
        url="https://example.com/old",
        title="Old Article",
        publish_date=base_date,
        domain="example.com",
        content_type="text",
    )
    
    recent_source = Source(
        url="https://example.com/recent",
        title="Recent Article",
        publish_date=recent_date,
        domain="example.com",
        content_type="text",
    )
    
    # Create evidence pieces with identical content
    old_evidence = EvidencePiece(
        id=str(uuid.uuid4()),
        source=old_source,
        summary="This is a test summary",
        raw_content="This is test content",
        relevance_score=None,
        credibility_score=None,
        recency_score=None,
        final_rank_score=None,
    )
    
    recent_evidence = EvidencePiece(
        id=str(uuid.uuid4()),
        source=recent_source,
        summary="This is a test summary",
        raw_content="This is test content",
        relevance_score=None,
        credibility_score=None,
        recency_score=None,
        final_rank_score=None,
    )
    
    # Create agent
    agent = RerankerAgent()
    
    # Rank evidence
    ranked_evidence = agent.rank_evidence([old_evidence, recent_evidence], claim)
    
    # Skip if filtering removed evidence
    assume(len(ranked_evidence) == 2)
    
    # Find the evidence pieces in ranked list
    old_rank_score = None
    recent_rank_score = None
    
    for piece in ranked_evidence:
        if piece.source.url == old_source.url:
            old_rank_score = piece.final_rank_score
        elif piece.source.url == recent_source.url:
            recent_rank_score = piece.final_rank_score
    
    # Verify recent evidence has higher rank score
    assert old_rank_score is not None and recent_rank_score is not None
    assert recent_rank_score > old_rank_score, \
        f"More recent evidence should rank higher: {recent_rank_score} > {old_rank_score}"


# Property 15: Domain credibility calculation completeness
@given(
    domain=st.text(min_size=5, max_size=50),
    factors=domain_credibility_strategy(),
)
@settings(max_examples=100)
def test_property_15_domain_credibility_calculation_completeness(domain, factors):
    """**Feature: kepler-fact-verification, Property 15: Domain credibility calculation completeness**
    
    For any domain credibility calculation, all five factors (agreement, citation density, 
    authorship, stability, link authority) should be incorporated into the final score.
    **Validates: Requirements 4.7**
    """
    # Add domain factors to agent's database
    RerankerAgent.add_domain_factors(domain, factors)
    
    # Create agent
    agent = RerankerAgent()
    
    # Get domain credibility
    credibility = agent.get_domain_credibility(domain)
    
    # Calculate expected score using the formula from DomainCredibility
    expected_score = factors.calculate_overall()
    
    # Verify the credibility matches the expected calculation
    assert abs(credibility - expected_score) < 0.001, \
        f"Domain credibility {credibility} should match calculated score {expected_score}"
    
    # Verify the calculation uses all five factors
    # This is implicitly tested by the calculate_overall method
    manual_calculation = (
        factors.agreement_score * 0.3 +
        factors.citation_density * 0.2 +
        factors.authorship_quality * 0.2 +
        factors.stability * 0.15 +
        factors.link_authority * 0.15
    )
    
    assert abs(credibility - manual_calculation) < 0.001, \
        "All five factors should be incorporated in credibility calculation"
    
    # Clean up
    if domain.lower() in RerankerAgent.DOMAIN_FACTORS_DB:
        del RerankerAgent.DOMAIN_FACTORS_DB[domain.lower()]


# Property 16: Unknown domain neutral scoring
@given(
    unknown_domain=st.text(min_size=10, max_size=50).filter(
        lambda d: d.lower() not in RerankerAgent.DOMAIN_CREDIBILITY_DB
        and d.lower() not in RerankerAgent.DOMAIN_FACTORS_DB
    ),
)
@settings(max_examples=100)
def test_property_16_unknown_domain_neutral_scoring(unknown_domain):
    """**Feature: kepler-fact-verification, Property 16: Unknown domain neutral scoring**
    
    For any domain not in the known domain database, the credibility score should be 
    set to a neutral default value (0.5).
    **Validates: Requirements 4.8**
    """
    # Create agent
    agent = RerankerAgent()
    
    # Get credibility for unknown domain
    credibility = agent.get_domain_credibility(unknown_domain)
    
    # Verify neutral score
    assert credibility == 0.5, \
        f"Unknown domain should have neutral credibility score 0.5, got {credibility}"


# Property 17: Evidence filtering by rank
@given(
    evidence=evidence_list_strategy(with_scores=False),
    claim=atomic_claim_strategy(),
    threshold=st.floats(min_value=0.1, max_value=0.9),
)
@settings(max_examples=100)
def test_property_17_evidence_filtering_by_rank(evidence, claim, threshold):
    """**Feature: kepler-fact-verification, Property 17: Evidence filtering by rank**
    
    For any ranked evidence list, only evidence with final_rank_score above a threshold 
    should be passed to subsequent stages.
    **Validates: Requirements 4.9**
    """
    # Create agent with custom threshold
    agent = RerankerAgent(min_rank_threshold=threshold)
    
    # Rank evidence
    ranked_evidence = agent.rank_evidence(evidence, claim)
    
    # Verify all evidence passes the threshold
    for piece in ranked_evidence:
        assert piece.final_rank_score is not None
        assert piece.final_rank_score >= threshold, \
            f"Filtered evidence should have rank score >= {threshold}, got {piece.final_rank_score}"
    
    # Verify that evidence below threshold was filtered out
    # We can check this by manually calculating scores for original evidence
    agent_check = RerankerAgent(min_rank_threshold=threshold)
    for piece in evidence:
        # Calculate scores
        relevance = agent_check.calculate_relevance(piece, claim)
        credibility = agent_check.calculate_credibility(piece.source)
        recency = agent_check.calculate_recency_score(piece.source.publish_date, datetime.now())
        
        final_score = (
            agent_check.relevance_weight * relevance +
            agent_check.credibility_weight * credibility +
            agent_check.recency_weight * recency
        )
        
        # If score is below threshold, it should not be in ranked_evidence
        if final_score < threshold:
            assert piece.id not in [e.id for e in ranked_evidence], \
                f"Evidence with score {final_score} below threshold {threshold} should be filtered out"


# Additional edge case tests
def test_calculate_relevance_basic():
    """Test basic relevance calculation"""
    agent = RerankerAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="The Earth is round",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    evidence = EvidencePiece(
        id=str(uuid.uuid4()),
        source=Source(
            url="https://example.com/earth",
            title="Earth Facts",
            publish_date=datetime.now(),
            domain="example.com",
            content_type="text",
        ),
        summary="The Earth is a round planet",
        raw_content="Scientific evidence shows that the Earth is round",
        relevance_score=None,
        credibility_score=None,
        recency_score=None,
        final_rank_score=None,
    )
    
    relevance = agent.calculate_relevance(evidence, claim)
    
    assert 0.0 <= relevance <= 1.0, "Relevance should be between 0 and 1"
    assert relevance > 0.0, "Evidence mentioning claim keywords should have positive relevance"


def test_calculate_credibility_known_domain():
    """Test credibility calculation for known domains"""
    agent = RerankerAgent()
    
    # Test Tier 1 domain
    source_tier1 = Source(
        url="https://arxiv.org/paper",
        title="Research Paper",
        publish_date=datetime.now(),
        domain="arxiv.org",
        content_type="text",
    )
    
    credibility_tier1 = agent.calculate_credibility(source_tier1)
    assert credibility_tier1 >= RerankerAgent.TIER_1_MIN, "Academic source should have Tier 1 credibility"
    
    # Test Tier 2 domain
    source_tier2 = Source(
        url="https://reuters.com/article",
        title="News Article",
        publish_date=datetime.now(),
        domain="reuters.com",
        content_type="text",
    )
    
    credibility_tier2 = agent.calculate_credibility(source_tier2)
    assert credibility_tier2 >= RerankerAgent.TIER_2_MIN, "News source should have Tier 2 credibility"
    assert credibility_tier2 < RerankerAgent.TIER_1_MIN, "News source should be below Tier 1"


def test_calculate_recency_score_edge_cases():
    """Test recency score calculation edge cases"""
    agent = RerankerAgent()
    
    claim_date = datetime.now()
    
    # Test same day
    same_day = agent.calculate_recency_score(claim_date, claim_date)
    assert same_day == 1.0, "Same day should have maximum recency"
    
    # Test None publish date
    none_date = agent.calculate_recency_score(None, claim_date)
    assert none_date == 0.5, "None publish date should have neutral recency"
    
    # Test old date
    old_date = claim_date - timedelta(days=365)
    old_recency = agent.calculate_recency_score(old_date, claim_date)
    assert 0.0 <= old_recency < 0.5, "Old date should have low recency"
    
    # Test recent date
    recent_date = claim_date - timedelta(days=7)
    recent_recency = agent.calculate_recency_score(recent_date, claim_date)
    assert recent_recency > old_recency, "Recent date should have higher recency than old date"


def test_rank_evidence_integration():
    """Test full ranking workflow"""
    agent = RerankerAgent()
    
    claim = AtomicClaim(
        id=str(uuid.uuid4()),
        text="Climate change is real",
        is_atomic=True,
        parent_claim=None,
        verification_status=None,
    )
    
    # Create evidence with varying quality
    evidence = [
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://nature.com/climate",
                title="Climate Research",
                publish_date=datetime.now() - timedelta(days=10),
                domain="nature.com",
                content_type="text",
            ),
            summary="Climate change is supported by scientific evidence",
            raw_content="Extensive research shows climate change is real",
            relevance_score=None,
            credibility_score=None,
            recency_score=None,
            final_rank_score=None,
        ),
        EvidencePiece(
            id=str(uuid.uuid4()),
            source=Source(
                url="https://medium.com/blog",
                title="Blog Post",
                publish_date=datetime.now() - timedelta(days=365),
                domain="medium.com",
                content_type="text",
            ),
            summary="Some thoughts on climate",
            raw_content="I think climate might be changing",
            relevance_score=None,
            credibility_score=None,
            recency_score=None,
            final_rank_score=None,
        ),
    ]
    
    ranked = agent.rank_evidence(evidence, claim)
    
    # Verify ranking
    assert len(ranked) > 0, "Should have ranked evidence"
    
    # High credibility, recent source should rank higher
    if len(ranked) == 2:
        assert ranked[0].source.domain == "nature.com", \
            "High credibility recent source should rank first"


# Unit tests for credibility tier examples (Requirements 4.4, 4.5, 4.6)

def test_tier1_published_papers_highest_credibility():
    """Test that published papers receive highest credibility scores
    
    Requirements 4.4: Published papers should be ranked as most credible
    """
    agent = RerankerAgent()
    
    # Test various academic/peer-reviewed sources
    academic_sources = [
        Source(
            url="https://arxiv.org/abs/1234.5678",
            title="Research Paper on arXiv",
            publish_date=datetime.now(),
            domain="arxiv.org",
            content_type="text",
        ),
        Source(
            url="https://www.nature.com/articles/nature12345",
            title="Nature Article",
            publish_date=datetime.now(),
            domain="nature.com",
            content_type="text",
        ),
        Source(
            url="https://science.org/doi/10.1126/science.abc1234",
            title="Science Journal Article",
            publish_date=datetime.now(),
            domain="science.org",
            content_type="text",
        ),
        Source(
            url="https://ieeexplore.ieee.org/document/1234567",
            title="IEEE Paper",
            publish_date=datetime.now(),
            domain="ieee.org",
            content_type="text",
        ),
    ]
    
    for source in academic_sources:
        credibility = agent.calculate_credibility(source)
        assert credibility >= RerankerAgent.TIER_1_MIN, \
            f"Academic source {source.domain} should have Tier 1 credibility (>= {RerankerAgent.TIER_1_MIN}), got {credibility}"
        assert credibility <= 1.0, \
            f"Credibility should not exceed 1.0, got {credibility}"


def test_tier2_verified_news_intermediate_credibility():
    """Test that verified news sources receive intermediate credibility scores
    
    Requirements 4.5: Verified news sources like Reuters should be ranked as intermediate credible
    """
    agent = RerankerAgent()
    
    # Test verified news sources
    news_sources = [
        Source(
            url="https://www.reuters.com/article/idUSKBN1234567",
            title="Reuters Article",
            publish_date=datetime.now(),
            domain="reuters.com",
            content_type="text",
        ),
        Source(
            url="https://apnews.com/article/1234567890abcdef",
            title="AP News Article",
            publish_date=datetime.now(),
            domain="apnews.com",
            content_type="text",
        ),
        Source(
            url="https://www.bbc.com/news/world-12345678",
            title="BBC News Article",
            publish_date=datetime.now(),
            domain="bbc.com",
            content_type="text",
        ),
        Source(
            url="https://www.npr.org/2023/01/01/1234567890/article",
            title="NPR Article",
            publish_date=datetime.now(),
            domain="npr.org",
            content_type="text",
        ),
    ]
    
    for source in news_sources:
        credibility = agent.calculate_credibility(source)
        assert credibility >= RerankerAgent.TIER_2_MIN, \
            f"Verified news source {source.domain} should have Tier 2 credibility (>= {RerankerAgent.TIER_2_MIN}), got {credibility}"
        assert credibility < RerankerAgent.TIER_1_MIN, \
            f"Verified news source {source.domain} should be below Tier 1 (< {RerankerAgent.TIER_1_MIN}), got {credibility}"


def test_tier4_blogs_lowest_credibility():
    """Test that blogs and social media receive lowest credibility scores
    
    Requirements 4.6: Other internet sources like blogs should be ranked as least credible
    """
    agent = RerankerAgent()
    
    # Test blog and social media sources
    blog_sources = [
        Source(
            url="https://medium.com/@user/article-title-123",
            title="Medium Blog Post",
            publish_date=datetime.now(),
            domain="medium.com",
            content_type="text",
        ),
        Source(
            url="https://myblog.wordpress.com/2023/01/01/post",
            title="WordPress Blog",
            publish_date=datetime.now(),
            domain="wordpress.com",
            content_type="text",
        ),
        Source(
            url="https://twitter.com/user/status/1234567890",
            title="Twitter Post",
            publish_date=datetime.now(),
            domain="twitter.com",
            content_type="text",
        ),
        Source(
            url="https://www.facebook.com/user/posts/1234567890",
            title="Facebook Post",
            publish_date=datetime.now(),
            domain="facebook.com",
            content_type="text",
        ),
    ]
    
    for source in blog_sources:
        credibility = agent.calculate_credibility(source)
        assert credibility < RerankerAgent.TIER_3_MIN, \
            f"Blog/social media source {source.domain} should have Tier 4 credibility (< {RerankerAgent.TIER_3_MIN}), got {credibility}"
        assert credibility >= RerankerAgent.TIER_4_MIN, \
            f"Credibility should not be below {RerankerAgent.TIER_4_MIN}, got {credibility}"


def test_credibility_tier_ordering():
    """Test that credibility tiers are properly ordered: Tier 1 > Tier 2 > Tier 3 > Tier 4"""
    agent = RerankerAgent()
    
    # Create sources from each tier
    tier1_source = Source(
        url="https://nature.com/article",
        title="Nature Article",
        publish_date=datetime.now(),
        domain="nature.com",
        content_type="text",
    )
    
    tier2_source = Source(
        url="https://reuters.com/article",
        title="Reuters Article",
        publish_date=datetime.now(),
        domain="reuters.com",
        content_type="text",
    )
    
    tier3_source = Source(
        url="https://nytimes.com/article",
        title="NYT Article",
        publish_date=datetime.now(),
        domain="nytimes.com",
        content_type="text",
    )
    
    tier4_source = Source(
        url="https://medium.com/article",
        title="Medium Post",
        publish_date=datetime.now(),
        domain="medium.com",
        content_type="text",
    )
    
    # Calculate credibility for each
    tier1_cred = agent.calculate_credibility(tier1_source)
    tier2_cred = agent.calculate_credibility(tier2_source)
    tier3_cred = agent.calculate_credibility(tier3_source)
    tier4_cred = agent.calculate_credibility(tier4_source)
    
    # Verify ordering
    assert tier1_cred > tier2_cred, "Tier 1 should have higher credibility than Tier 2"
    assert tier2_cred > tier3_cred, "Tier 2 should have higher credibility than Tier 3"
    assert tier3_cred > tier4_cred, "Tier 3 should have higher credibility than Tier 4"
