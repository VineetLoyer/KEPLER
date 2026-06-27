"""Property-based tests for Pipeline Orchestrator and Traceability

This module tests the pipeline orchestrator's traceability features using
property-based testing to ensure complete logging and inspection capabilities.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from src.pipeline import PipelineOrchestrator
from src.models.data_models import (
    MultimodalInput,
    LLM,
    ImageMetadata,
    VerdictType,
)


# Strategies for generating test data

@st.composite
def llm_strategy(draw):
    """Generate a random LLM configuration"""
    providers = ["openai", "anthropic", "google"]
    provider = draw(st.sampled_from(providers))
    model_num = draw(st.integers(min_value=1, max_value=5))
    
    return LLM(
        model_id=f"{provider}-model-{model_num}",
        provider=provider,
        version=f"v{draw(st.integers(min_value=1, max_value=3))}",
        api_endpoint=f"https://api.{provider}.com/v1",
    )


@st.composite
def multimodal_input_strategy(draw, min_llms=1, max_llms=5):
    """Generate a random MultimodalInput"""
    # Generate text (always present for these tests)
    text = draw(st.text(min_size=10, max_size=200))
    
    # Generate LLMs
    num_llms = draw(st.integers(min_value=min_llms, max_value=max_llms))
    llms = [draw(llm_strategy()) for _ in range(num_llms)]
    
    # Select decomposition model from the list
    decomposition_model = draw(st.sampled_from(llms))
    
    # Generate timestamp (recent past)
    days_ago = draw(st.integers(min_value=0, max_value=365))
    timestamp = datetime.now() - timedelta(days=days_ago)
    
    # Optionally include image
    has_image = draw(st.booleans())
    if has_image:
        image = b"fake_image_data"
        image_metadata = ImageMetadata(
            format="jpeg",
            size_bytes=len(image),
            dimensions=(800, 600),
            hash="abc123",
        )
    else:
        image = None
        image_metadata = None
    
    return MultimodalInput(
        text=text,
        image=image,
        image_metadata=image_metadata,
        timestamp=timestamp,
        selected_llms=llms,
        decomposition_model=decomposition_model,
    )


# Property Tests

class TestPipelineTraceability:
    """Test suite for pipeline traceability properties"""
    
    @given(multimodal_input=multimodal_input_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_34_complete_pipeline_tracing(self, multimodal_input):
        """
        **Feature: kepler-fact-verification, Property 34: Complete pipeline tracing**
        
        Property: For any claim processed through the system, the trace log should 
        contain entries for all pipeline stages: input processing, decomposition, 
        retrieval, reranking, aggregation, verification, and confidence scoring.
        
        **Validates: Requirements 9.1**
        """
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Extract trace log
        trace_log = final_output.trace_log
        
        # Verify trace log is not empty
        assert len(trace_log) > 0, "Trace log should not be empty"
        
        # Define expected stages
        expected_stages = [
            "input_processing",
            "claim_decomposition",
            "evidence_retrieval",
            "evidence_reranking",
            "evidence_aggregation",
            "multi_model_verification",
            "consensus_aggregation",
            "confidence_scoring",
        ]
        
        # Extract stages from trace log
        logged_stages = set()
        for entry in trace_log:
            if "stage" in entry:
                logged_stages.add(entry["stage"])
        
        # Verify all expected stages are present
        for stage in expected_stages:
            assert stage in logged_stages, f"Stage '{stage}' missing from trace log"
        
        # Verify each stage has both start and complete events
        for stage in expected_stages:
            stage_entries = [e for e in trace_log if e.get("stage") == stage]
            events = [e.get("event") for e in stage_entries]
            
            assert "start" in events, f"Stage '{stage}' missing 'start' event"
            assert "complete" in events, f"Stage '{stage}' missing 'complete' event"
    
    @given(multimodal_input=multimodal_input_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_35_evidence_referenced_justifications(self, multimodal_input):
        """
        **Feature: kepler-fact-verification, Property 35: Evidence-referenced justifications**
        
        Property: For any verdict justification where evidence was found, at least 
        one specific evidence source should be referenced.
        
        **Validates: Requirements 9.2**
        """
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Get consensus verdict
        consensus = final_output.consensus_verdict
        
        # Check if evidence was found
        num_evidence = final_output.processing_metadata.get("num_ranked_evidence", 0)
        
        # Only require evidence references if evidence was found
        if num_evidence > 0:
            # Check individual verdicts for evidence references
            for verdict in consensus.individual_verdicts:
                # Each verdict should have evidence references when evidence exists
                assert len(verdict.evidence_references) > 0, \
                    f"Verdict from {verdict.model_id} has no evidence references despite {num_evidence} evidence pieces being available"
                
                # Evidence references should be non-empty strings (URLs)
                for ref in verdict.evidence_references:
                    assert isinstance(ref, str), "Evidence reference should be a string"
                    assert len(ref) > 0, "Evidence reference should not be empty"
        else:
            # When no evidence is found, it's acceptable to have empty references
            # The justification should still explain the lack of evidence
            for verdict in consensus.individual_verdicts:
                assert isinstance(verdict.justification, str), \
                    "Justification should be a string"
                assert len(verdict.justification) > 0, \
                    "Justification should not be empty even when no evidence is found"
    
    @given(multimodal_input=multimodal_input_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_36_source_link_preservation(self, multimodal_input):
        """
        **Feature: kepler-fact-verification, Property 36: Source link preservation**
        
        Property: For any evidence source used in justification, the original 
        source URL should be preserved and accessible in the final output.
        This property only applies when evidence is found.
        
        **Validates: Requirements 9.3**
        """
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Get structured justification
        structured_justification = final_output.confidence_score.structured_justification
        
        # Check if evidence was found
        num_evidence = final_output.processing_metadata.get("num_ranked_evidence", 0)
        
        # Only require source links if evidence was found
        if num_evidence > 0:
            # Verify source links are present
            assert len(structured_justification.source_links) > 0, \
                f"Structured justification should contain source links when {num_evidence} evidence pieces exist"
            
            # Verify all source links are valid URLs (non-empty strings)
            for link in structured_justification.source_links:
                assert isinstance(link, str), "Source link should be a string"
                assert len(link) > 0, "Source link should not be empty"
                # Basic URL validation - should contain protocol or domain
                assert "://" in link or "." in link, \
                    f"Source link '{link}' does not appear to be a valid URL"
            
            # Verify key evidence pieces have source URLs
            for evidence in structured_justification.key_evidence:
                assert evidence.source.url, "Evidence piece should have a source URL"
                assert len(evidence.source.url) > 0, "Source URL should not be empty"
                # Verify the URL is in the source_links list
                assert evidence.source.url in structured_justification.source_links, \
                    f"Evidence URL '{evidence.source.url}' not found in source_links"
        else:
            # When no evidence is found, it's acceptable to have empty source links
            # The structured justification should still exist
            assert structured_justification is not None, \
                "Structured justification should exist even when no evidence is found"
            assert isinstance(structured_justification.summary, str), \
                "Summary should be a string"
            assert len(structured_justification.summary) > 0, \
                "Summary should not be empty even when no evidence is found"
    
    @given(multimodal_input=multimodal_input_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_37_stage_level_inspection_capability(self, multimodal_input):
        """
        **Feature: kepler-fact-verification, Property 37: Stage-level inspection capability**
        
        Property: For any trace log entry, it should contain sufficient information 
        to understand what operations were performed at that pipeline stage.
        
        **Validates: Requirements 9.4**
        """
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Test inspection capability for each stage
        expected_stages = [
            "input_processing",
            "claim_decomposition",
            "evidence_retrieval",
            "evidence_reranking",
            "evidence_aggregation",
            "multi_model_verification",
            "consensus_aggregation",
            "confidence_scoring",
        ]
        
        for stage_name in expected_stages:
            # Use the inspect_stage method
            stage_entries = orchestrator.inspect_stage(stage_name)
            
            # Verify we can inspect the stage
            assert len(stage_entries) > 0, f"Cannot inspect stage '{stage_name}'"
            
            # Verify each entry has required fields
            for entry in stage_entries:
                # Must have stage name
                assert "stage" in entry, "Entry missing 'stage' field"
                assert entry["stage"] == stage_name, "Stage name mismatch"
                
                # Must have event type
                assert "event" in entry, "Entry missing 'event' field"
                assert entry["event"] in ["start", "complete", "error"], \
                    f"Invalid event type: {entry['event']}"
                
                # Must have timestamp
                assert "timestamp" in entry, "Entry missing 'timestamp' field"
                # Verify timestamp is valid ISO format
                try:
                    datetime.fromisoformat(entry["timestamp"])
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {entry['timestamp']}")
                
                # Start events should have details
                if entry["event"] == "start":
                    assert "details" in entry, "Start event missing 'details' field"
                    assert isinstance(entry["details"], dict), \
                        "Details should be a dictionary"
                
                # Complete events should have results
                if entry["event"] == "complete":
                    assert "results" in entry, "Complete event missing 'results' field"
                    assert isinstance(entry["results"], dict), \
                        "Results should be a dictionary"
                    # Should have status
                    assert "status" in entry["results"], \
                        "Results missing 'status' field"


class TestPipelineInspection:
    """Test suite for pipeline inspection methods"""
    
    def test_inspect_stage_returns_correct_entries(self):
        """Test that inspect_stage returns only entries for the specified stage"""
        orchestrator = PipelineOrchestrator()
        
        # Create a simple input
        llm = LLM(
            model_id="test-model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com",
        )
        
        multimodal_input = MultimodalInput(
            text="The Earth is round.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Process the claim
        orchestrator.process_claim(multimodal_input)
        
        # Inspect a specific stage
        decomposition_entries = orchestrator.inspect_stage("claim_decomposition")
        
        # Verify all entries are for the correct stage
        for entry in decomposition_entries:
            assert entry["stage"] == "claim_decomposition"
    
    def test_get_trace_summary_provides_overview(self):
        """Test that get_trace_summary provides a useful overview"""
        orchestrator = PipelineOrchestrator()
        
        # Create a simple input
        llm = LLM(
            model_id="test-model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com",
        )
        
        multimodal_input = MultimodalInput(
            text="The Earth is round.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Process the claim
        orchestrator.process_claim(multimodal_input)
        
        # Get trace summary
        summary = orchestrator.get_trace_summary()
        
        # Verify summary structure
        assert "total_entries" in summary
        assert "stages_executed" in summary
        assert "num_stages" in summary
        assert "errors" in summary
        
        # Verify summary content
        assert summary["total_entries"] > 0
        assert summary["num_stages"] > 0
        assert len(summary["stages_executed"]) == summary["num_stages"]
        assert isinstance(summary["errors"], list)


class TestPipelineMetadata:
    """Test suite for pipeline metadata and processing information"""
    
    @given(multimodal_input=multimodal_input_strategy())
    @settings(max_examples=50, deadline=None)
    def test_processing_metadata_completeness(self, multimodal_input):
        """Test that processing metadata contains all expected fields"""
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify processing metadata
        metadata = final_output.processing_metadata
        
        # Check required fields
        assert "pipeline_version" in metadata
        assert "total_stages" in metadata
        assert "processing_time_ms" in metadata
        assert "num_atomic_claims" in metadata
        assert "num_evidence_pieces" in metadata
        assert "num_ranked_evidence" in metadata
        
        # Verify field types and values
        assert isinstance(metadata["pipeline_version"], str)
        assert isinstance(metadata["total_stages"], int)
        assert metadata["total_stages"] == 7  # Expected number of stages
        assert isinstance(metadata["processing_time_ms"], float)
        assert metadata["processing_time_ms"] >= 0
        assert isinstance(metadata["num_atomic_claims"], int)
        assert metadata["num_atomic_claims"] >= 0
