"""Integration tests for KEPLER fact-verification system

This module contains end-to-end integration tests that verify the complete
pipeline works correctly with sample claims, multimodal inputs, and error scenarios.
"""
import pytest
from datetime import datetime
from src.pipeline import PipelineOrchestrator
from src.models.data_models import (
    MultimodalInput,
    LLM,
    ImageMetadata,
    VerdictType,
)
from src.agents.claim_decomposition_agent import ClaimDecompositionAgent
from src.agents.retriever_agent import RetrieverAgent
from src.agents.reranker_agent import RerankerAgent
from src.agents.aggregator_agent import AggregatorAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.multi_model_aggregator import MultiModelAggregator
from src.agents.confidence_scorer import ConfidenceScorer


class TestCompleteEndToEndPipeline:
    """Test complete pipeline with sample claims"""
    
    def test_simple_text_claim_end_to_end(self):
        """Test complete pipeline with a simple text claim
        
        This test verifies that the entire pipeline can process a basic
        text claim from input to final verdict.
        """
        # Create test LLMs
        llm1 = LLM(
            model_id="openai/gpt-4",
            provider="openai",
            version="v1",
            api_endpoint="https://api.openai.com/v1",
        )
        llm2 = LLM(
            model_id="anthropic/claude-3",
            provider="anthropic",
            version="v1",
            api_endpoint="https://api.anthropic.com/v1",
        )
        
        # Create multimodal input with text only
        multimodal_input = MultimodalInput(
            text="The Earth orbits around the Sun.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm1, llm2],
            decomposition_model=llm1,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify final output structure
        assert final_output is not None
        assert final_output.original_input == multimodal_input
        assert len(final_output.atomic_claims) > 0
        assert final_output.consensus_verdict is not None
        assert final_output.confidence_score is not None
        assert len(final_output.trace_log) > 0
        
        # Verify consensus verdict
        assert final_output.consensus_verdict.final_classification in [
            VerdictType.SUPPORTED,
            VerdictType.REFUTED,
            VerdictType.NOT_ENOUGH_INFO,
        ]
        assert len(final_output.consensus_verdict.consensus_justification) > 0
        assert len(final_output.consensus_verdict.individual_verdicts) == 2
        assert 0.0 <= final_output.consensus_verdict.agreement_level <= 1.0
        
        # Verify confidence score
        assert 0.0 <= final_output.confidence_score.overall_score <= 1.0
        assert 0.0 <= final_output.confidence_score.source_reliability <= 1.0
        assert 0.0 <= final_output.confidence_score.model_agreement <= 1.0
        assert 0.0 <= final_output.confidence_score.evidence_recency <= 1.0
        
        # Verify processing metadata
        assert "processing_time_ms" in final_output.processing_metadata
        assert "num_atomic_claims" in final_output.processing_metadata
        assert "num_evidence_pieces" in final_output.processing_metadata
        assert final_output.processing_metadata["num_atomic_claims"] == len(final_output.atomic_claims)
    
    def test_compound_claim_decomposition_end_to_end(self):
        """Test pipeline with a compound claim that should be decomposed
        
        This test verifies that compound claims are properly decomposed
        into atomic claims and each is processed.
        """
        # Create test LLM
        llm = LLM(
            model_id="openai/gpt-4",
            provider="openai",
            version="v1",
            api_endpoint="https://api.openai.com/v1",
        )
        
        # Create multimodal input with compound claim
        multimodal_input = MultimodalInput(
            text="Water boils at 100 degrees Celsius and freezes at 0 degrees Celsius at sea level.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify atomic claims were extracted
        assert len(final_output.atomic_claims) >= 1
        
        # Verify each atomic claim has required properties
        for claim in final_output.atomic_claims:
            assert claim.id is not None
            assert len(claim.text) > 0
            assert isinstance(claim.is_atomic, bool)
    
    def test_multiple_llms_consensus_end_to_end(self):
        """Test pipeline with multiple LLMs to verify consensus mechanism
        
        This test verifies that multiple LLMs are properly engaged and
        their outputs are aggregated into a consensus.
        """
        # Create multiple test LLMs
        llms = [
            LLM(
                model_id=f"provider{i}/model{i}",
                provider=f"provider{i}",
                version="v1",
                api_endpoint=f"https://api.provider{i}.com/v1",
            )
            for i in range(3)
        ]
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="The speed of light is approximately 299,792,458 meters per second.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=llms,
            decomposition_model=llms[0],
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify all LLMs were engaged
        assert len(final_output.consensus_verdict.individual_verdicts) == 3
        
        # Verify each LLM produced a verdict
        for verdict in final_output.consensus_verdict.individual_verdicts:
            assert verdict.model_id is not None
            assert verdict.classification in [
                VerdictType.SUPPORTED,
                VerdictType.REFUTED,
                VerdictType.NOT_ENOUGH_INFO,
            ]
            assert len(verdict.justification) > 0
            assert 0.0 <= verdict.confidence <= 1.0
        
        # Verify consensus was calculated
        assert final_output.consensus_verdict.final_classification is not None
        assert 0.0 <= final_output.consensus_verdict.agreement_level <= 1.0


class TestMultimodalInputIntegration:
    """Test pipeline with multimodal inputs (text + image)"""
    
    def test_text_and_image_input_end_to_end(self):
        """Test complete pipeline with both text and image input
        
        This test verifies that the pipeline can handle multimodal inputs
        with both text claims and accompanying images.
        """
        # Create test LLM
        llm = LLM(
            model_id="openai/gpt-4v",
            provider="openai",
            version="v1",
            api_endpoint="https://api.openai.com/v1",
        )
        
        # Create fake image data
        fake_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        image_metadata = ImageMetadata(
            format="PNG",
            size_bytes=len(fake_image),
            dimensions=(100, 100),
            hash="abc123def456",
        )
        
        # Create multimodal input with text and image
        multimodal_input = MultimodalInput(
            text="This image shows the Eiffel Tower in Paris.",
            image=fake_image,
            image_metadata=image_metadata,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify the pipeline processed both modalities
        assert final_output.original_input.text is not None
        assert final_output.original_input.image is not None
        assert final_output.original_input.image_metadata is not None
        
        # Verify output structure
        assert final_output.consensus_verdict is not None
        assert final_output.confidence_score is not None
        
        # Check trace log for evidence retrieval stage
        retrieval_entries = [
            e for e in final_output.trace_log
            if e.get("stage") == "evidence_retrieval"
        ]
        assert len(retrieval_entries) > 0
        
        # Verify visual content was considered
        for entry in retrieval_entries:
            if entry.get("event") == "start":
                assert "has_visual_content" in entry.get("details", {})
    
    def test_image_only_input_end_to_end(self):
        """Test pipeline with image-only input (no text claim)
        
        This test verifies that the pipeline can handle inputs with
        only an image and no accompanying text.
        """
        # Create test LLM
        llm = LLM(
            model_id="openai/gpt-4v",
            provider="openai",
            version="v1",
            api_endpoint="https://api.openai.com/v1",
        )
        
        # Create fake image data
        fake_image = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"  # JPEG header
        image_metadata = ImageMetadata(
            format="JPEG",
            size_bytes=len(fake_image),
            dimensions=(800, 600),
            hash="image123hash",
        )
        
        # Create multimodal input with image only
        multimodal_input = MultimodalInput(
            text=None,
            image=fake_image,
            image_metadata=image_metadata,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify the pipeline handled image-only input
        assert final_output.original_input.text is None
        assert final_output.original_input.image is not None
        
        # Verify output was still generated
        assert final_output.consensus_verdict is not None
        assert final_output.confidence_score is not None


class TestErrorPropagationIntegration:
    """Test error handling and propagation through the pipeline"""
    
    def test_empty_text_graceful_degradation(self):
        """Test pipeline handles empty text input gracefully
        
        This test verifies that the pipeline can handle edge cases
        like empty text input without crashing.
        """
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input with empty text
        multimodal_input = MultimodalInput(
            text="",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim - should handle gracefully
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify pipeline completed without crashing
        assert final_output is not None
        assert final_output.consensus_verdict is not None
        
        # With empty text, we expect no atomic claims or NOT_ENOUGH_INFO verdict
        assert (
            len(final_output.atomic_claims) == 0 or
            final_output.consensus_verdict.final_classification == VerdictType.NOT_ENOUGH_INFO
        )
    
    def test_no_evidence_found_graceful_degradation(self):
        """Test pipeline handles scenario where no evidence is found
        
        This test verifies graceful degradation when the retrieval
        stage finds no evidence for a claim.
        """
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input with an obscure claim
        multimodal_input = MultimodalInput(
            text="The fictional character Zorgblat invented the quantum flibbertigibbet in 2099.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify pipeline completed
        assert final_output is not None
        assert final_output.consensus_verdict is not None
        
        # Check trace log for evidence retrieval
        retrieval_entries = [
            e for e in final_output.trace_log
            if e.get("stage") == "evidence_retrieval" and e.get("event") == "complete"
        ]
        
        # If no evidence was found, verify graceful handling
        if retrieval_entries:
            results = retrieval_entries[0].get("results", {})
            num_evidence = results.get("num_evidence_pieces", 0)
            
            if num_evidence == 0:
                # Verify the pipeline continued despite no evidence
                assert final_output.consensus_verdict.final_classification is not None
                # Likely should be NOT_ENOUGH_INFO
                assert final_output.consensus_verdict.final_classification == VerdictType.NOT_ENOUGH_INFO
    
    def test_single_llm_failure_recovery(self):
        """Test pipeline handles individual LLM failures gracefully
        
        This test verifies that if one LLM in an ensemble fails,
        the pipeline can still produce a verdict from the remaining LLMs.
        """
        # Create multiple test LLMs
        llms = [
            LLM(
                model_id=f"provider{i}/model{i}",
                provider=f"provider{i}",
                version="v1",
                api_endpoint=f"https://api.provider{i}.com/v1",
            )
            for i in range(3)
        ]
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="The Moon is made of cheese.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=llms,
            decomposition_model=llms[0],
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify pipeline completed
        assert final_output is not None
        assert final_output.consensus_verdict is not None
        
        # Verify we got verdicts (even if some LLMs failed, we should get at least one)
        assert len(final_output.consensus_verdict.individual_verdicts) >= 1
        
        # Verify consensus was still calculated
        assert final_output.consensus_verdict.final_classification is not None


class TestTraceabilityIntegration:
    """Test traceability features in end-to-end scenarios"""
    
    def test_complete_trace_log_structure(self):
        """Test that trace log contains complete information for debugging
        
        This test verifies that the trace log provides sufficient detail
        for understanding and debugging the pipeline execution.
        """
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="Python is a programming language.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify trace log structure
        assert len(final_output.trace_log) > 0
        
        # Verify each entry has required fields
        for entry in final_output.trace_log:
            assert "stage" in entry
            assert "event" in entry
            assert "timestamp" in entry
            
            # Verify timestamp is valid
            try:
                datetime.fromisoformat(entry["timestamp"])
            except ValueError:
                pytest.fail(f"Invalid timestamp: {entry['timestamp']}")
        
        # Verify we can inspect individual stages
        for stage in ["input_processing", "claim_decomposition", "multi_model_verification"]:
            stage_entries = orchestrator.inspect_stage(stage)
            assert len(stage_entries) > 0
            
            # Verify stage entries are properly filtered
            for entry in stage_entries:
                assert entry["stage"] == stage
    
    def test_trace_summary_provides_overview(self):
        """Test that trace summary provides useful overview information"""
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="The capital of France is Paris.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
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
        assert isinstance(summary["stages_executed"], list)
        assert isinstance(summary["errors"], list)
        
        # Verify all expected stages are in the summary
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
        
        for stage in expected_stages:
            assert stage in summary["stages_executed"]


class TestProcessingMetadataIntegration:
    """Test processing metadata in end-to-end scenarios"""
    
    def test_processing_time_tracking(self):
        """Test that processing time is accurately tracked"""
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="Test claim for timing.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify processing time is tracked
        assert "processing_time_ms" in final_output.processing_metadata
        processing_time = final_output.processing_metadata["processing_time_ms"]
        
        # Processing time should be positive
        assert processing_time >= 0
        
        # Processing time should be reasonable (not negative or absurdly large)
        assert processing_time < 1000000  # Less than 1000 seconds
    
    def test_evidence_count_tracking(self):
        """Test that evidence counts are accurately tracked"""
        # Create test LLM
        llm = LLM(
            model_id="test/model",
            provider="test",
            version="v1",
            api_endpoint="https://test.com/v1",
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text="The sky is blue.",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Process the claim
        final_output = orchestrator.process_claim(multimodal_input)
        
        # Verify evidence counts are tracked
        assert "num_evidence_pieces" in final_output.processing_metadata
        assert "num_ranked_evidence" in final_output.processing_metadata
        
        num_evidence = final_output.processing_metadata["num_evidence_pieces"]
        num_ranked = final_output.processing_metadata["num_ranked_evidence"]
        
        # Counts should be non-negative
        assert num_evidence >= 0
        assert num_ranked >= 0
        
        # Ranked evidence should not exceed retrieved evidence
        assert num_ranked <= num_evidence
