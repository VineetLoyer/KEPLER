"""Unit tests for error handling scenarios

This module tests error handling across the KEPLER system including:
- Input validation errors
- External service failure recovery
- Empty evidence handling
- Consensus tie-breaking
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.services.input_processor import InputProcessor, InputValidationError
from src.agents.multi_model_aggregator import MultiModelAggregator
from src.agents.retriever_agent import RetrieverAgent
from src.pipeline import PipelineOrchestrator
from src.models.data_models import (
    LLM,
    Verdict,
    VerdictType,
    AtomicClaim,
    MultimodalInput,
    ImageMetadata,
    EvidencePiece,
    Source,
)
from src.utils.retry import (
    retry_with_exponential_backoff,
    RetryExhaustedError,
    ExternalServiceError,
)


class TestInputValidationErrors:
    """Test input validation error handling"""
    
    def test_empty_input_raises_error(self):
        """Test that providing neither text nor image raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text=None,
                image=None,
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            )
        
        assert "at least one" in str(exc_info.value).lower()
    
    def test_invalid_text_type_raises_error(self):
        """Test that non-string text raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text=12345,  # Invalid: not a string
                image=None,
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            )
        
        assert "string" in str(exc_info.value).lower()
    
    def test_empty_text_raises_error(self):
        """Test that empty or whitespace-only text raises InputValidationError"""
        processor = InputProcessor()
        llm = LLM("gpt-4", "openai", "1.0", "https://api.openai.com")
        
        # Test empty string
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text="",
                image=None,
                selected_llms=[llm],
                decomposition_model=llm,
            )
        
        assert "empty" in str(exc_info.value).lower()
        
        # Test whitespace-only string
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text="   \n\t  ",
                image=None,
                selected_llms=[llm],
                decomposition_model=llm,
            )
        
        assert "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
    
    def test_invalid_image_type_raises_error(self):
        """Test that non-bytes image raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text=None,
                image="not bytes",  # Invalid: not bytes
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            )
        
        assert "bytes" in str(exc_info.value).lower()
    
    def test_empty_image_raises_error(self):
        """Test that empty image data raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text=None,
                image=b"",  # Empty bytes
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            )
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_oversized_image_raises_error(self):
        """Test that image exceeding size limit raises InputValidationError"""
        processor = InputProcessor()
        
        # Create image larger than 10MB
        large_image = b"x" * (11 * 1024 * 1024)
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text=None,
                image=large_image,
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            )
        
        assert "size" in str(exc_info.value).lower() or "exceeds" in str(exc_info.value).lower()
    
    def test_no_llms_selected_raises_error(self):
        """Test that not selecting any LLMs raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text="Test claim",
                image=None,
                selected_llms=[],  # Empty list
                decomposition_model=None,
            )
        
        assert "llm" in str(exc_info.value).lower()
    
    def test_no_decomposition_model_raises_error(self):
        """Test that not designating decomposition model raises InputValidationError"""
        processor = InputProcessor()
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text="Test claim",
                image=None,
                selected_llms=[LLM("gpt-4", "openai", "1.0", "https://api.openai.com")],
                decomposition_model=None,  # Not designated
            )
        
        assert "decomposition" in str(exc_info.value).lower()
    
    def test_decomposition_model_not_in_selected_raises_error(self):
        """Test that decomposition model must be in selected LLMs"""
        processor = InputProcessor()
        
        llm1 = LLM("gpt-4", "openai", "1.0", "https://api.openai.com")
        llm2 = LLM("claude-3", "anthropic", "1.0", "https://api.anthropic.com")
        
        with pytest.raises(InputValidationError) as exc_info:
            processor.accept_input(
                text="Test claim",
                image=None,
                selected_llms=[llm1],
                decomposition_model=llm2,  # Not in selected_llms
            )
        
        assert "selected" in str(exc_info.value).lower()
    
    def test_invalid_llm_selection_count(self):
        """Test that selecting invalid number of LLMs raises error"""
        processor = InputProcessor()
        available = [
            LLM("gpt-4", "openai", "1.0", "https://api.openai.com"),
            LLM("claude-3", "anthropic", "1.0", "https://api.anthropic.com"),
        ]
        
        # Test n = 0
        with pytest.raises(InputValidationError):
            processor.select_llms(available, 0)
        
        # Test n < 0
        with pytest.raises(InputValidationError):
            processor.select_llms(available, -1)
        
        # Test n > available
        with pytest.raises(InputValidationError):
            processor.select_llms(available, 5)
    
    def test_valid_input_succeeds(self):
        """Test that valid input is accepted without error"""
        processor = InputProcessor()
        llm = LLM("gpt-4", "openai", "1.0", "https://api.openai.com")
        
        # Valid text input
        result = processor.accept_input(
            text="The Earth is round",
            image=None,
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        assert result.text == "The Earth is round"
        assert result.image is None
        assert len(result.selected_llms) == 1
        
        # Valid image input
        result = processor.accept_input(
            text=None,
            image=b"fake_image_data",
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        assert result.text is None
        assert result.image == b"fake_image_data"
        
        # Valid both
        result = processor.accept_input(
            text="The Earth is round",
            image=b"fake_image_data",
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        assert result.text == "The Earth is round"
        assert result.image == b"fake_image_data"


class TestExternalServiceFailureRecovery:
    """Test external service failure recovery with retry logic"""
    
    def test_retry_decorator_succeeds_on_first_attempt(self):
        """Test that retry decorator doesn't interfere with successful calls"""
        call_count = [0]
        
        @retry_with_exponential_backoff(max_retries=3)
        def successful_function():
            call_count[0] += 1
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        assert call_count[0] == 1  # Called only once
    
    def test_retry_decorator_retries_on_failure(self):
        """Test that retry decorator retries on transient failures"""
        call_count = [0]
        
        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.01)
        def failing_then_succeeding_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ExternalServiceError("Temporary failure")
            return "success"
        
        result = failing_then_succeeding_function()
        
        assert result == "success"
        assert call_count[0] == 3  # Failed twice, succeeded on third
    
    def test_retry_decorator_exhausts_retries(self):
        """Test that retry decorator raises RetryExhaustedError after max retries"""
        call_count = [0]
        
        @retry_with_exponential_backoff(max_retries=2, initial_delay=0.01)
        def always_failing_function():
            call_count[0] += 1
            raise ExternalServiceError("Permanent failure")
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            always_failing_function()
        
        assert call_count[0] == 3  # Initial + 2 retries
        assert "failed after 3 attempts" in str(exc_info.value).lower()
    
    def test_retry_decorator_respects_exception_types(self):
        """Test that retry decorator only retries specified exception types"""
        call_count = [0]
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01,
            exceptions=(ExternalServiceError,)
        )
        def function_with_wrong_exception():
            call_count[0] += 1
            raise ValueError("Not a retryable error")
        
        # Should not retry ValueError
        with pytest.raises(ValueError):
            function_with_wrong_exception()
        
        assert call_count[0] == 1  # No retries
    
    def test_pipeline_handles_retrieval_failure_gracefully(self):
        """Test that pipeline handles evidence retrieval failure gracefully"""
        # Create mock agents
        mock_decomposer = Mock()
        mock_retriever = Mock()
        mock_reranker = Mock()
        mock_aggregator = Mock()
        mock_verifier = Mock()
        mock_multi_model = Mock()
        mock_confidence = Mock()
        
        # Setup mock decomposer to return a claim
        claim = AtomicClaim(
            id="claim1",
            text="Test claim",
            is_atomic=True,
            parent_claim=None,
            verification_status=None,
        )
        mock_decomposer.decompose.return_value = [claim]
        
        # Setup mock retriever to raise exception (simulating failure)
        mock_retriever.retrieve_evidence.side_effect = ExternalServiceError("API failure")
        
        # Setup other mocks to handle empty evidence
        mock_reranker.rank_evidence.return_value = []
        mock_aggregator.consolidate_evidence.return_value = Mock(
            textual_evidence=[],
            visual_evidence=[],
            metadata={},
            evidence_map={},
            reasoning_chain=None,
        )
        mock_aggregator.apply_chain_of_thought.return_value = Mock(
            steps=[],
            agreements=[],
            conflicts=[],
            gaps=[],
        )
        
        # Setup verifier to return NOT_ENOUGH_INFO verdict
        verdict = Verdict(
            model_id="gpt-4",
            classification=VerdictType.NOT_ENOUGH_INFO,
            justification="No evidence available",
            confidence=0.3,
            evidence_references=[],
        )
        mock_verifier.verify_with_ensemble.return_value = [verdict]
        
        # Setup multi-model aggregator
        from src.models.data_models import ConsensusVerdict
        consensus = ConsensusVerdict(
            final_classification=VerdictType.NOT_ENOUGH_INFO,
            consensus_justification="No evidence available",
            individual_verdicts=[verdict],
            agreement_level=1.0,
        )
        mock_multi_model.aggregate_verdicts.return_value = consensus
        
        # Setup confidence scorer
        from src.models.data_models import ConfidenceScore, StructuredJustification
        confidence_score = ConfidenceScore(
            overall_score=0.3,
            source_reliability=0.0,
            model_agreement=1.0,
            evidence_recency=0.0,
            structured_justification=StructuredJustification(
                summary="No evidence",
                key_evidence=[],
                reasoning_chain=Mock(steps=[], agreements=[], conflicts=[], gaps=[]),
                source_links=[],
            ),
        )
        mock_confidence.calculate_confidence.return_value = confidence_score
        
        # Create pipeline with mocks
        pipeline = PipelineOrchestrator(
            claim_decomposer=mock_decomposer,
            retriever=mock_retriever,
            reranker=mock_reranker,
            aggregator=mock_aggregator,
            verifier=mock_verifier,
            multi_model_aggregator=mock_multi_model,
            confidence_scorer=mock_confidence,
        )
        
        # Create input
        llm = LLM("gpt-4", "openai", "1.0", "https://api.openai.com")
        multimodal_input = MultimodalInput(
            text="Test claim",
            image=None,
            image_metadata=None,
            timestamp=datetime.now(),
            selected_llms=[llm],
            decomposition_model=llm,
        )
        
        # Process claim - should not raise exception despite retrieval failure
        result = pipeline.process_claim(multimodal_input)
        
        # Verify graceful degradation
        assert result.consensus_verdict.final_classification == VerdictType.NOT_ENOUGH_INFO
        assert result.processing_metadata["num_evidence_pieces"] == 0
        
        # Check trace log for error handling
        retrieval_logs = [
            log for log in result.trace_log
            if log.get("stage") == "evidence_retrieval"
        ]
        assert len(retrieval_logs) > 0


class TestEmptyEvidenceHandling:
    """Test handling of empty or missing evidence scenarios"""
    
    def test_empty_evidence_list_handled_gracefully(self):
        """Test that empty evidence list is handled without errors"""
        from src.agents.reranker_agent import RerankerAgent
        
        reranker = RerankerAgent()
        claim = AtomicClaim(
            id="claim1",
            text="Test claim",
            is_atomic=True,
            parent_claim=None,
            verification_status=None,
        )
        
        # Should not raise exception
        result = reranker.rank_evidence([], claim)
        
        assert result == []
    
    def test_aggregator_handles_empty_evidence(self):
        """Test that aggregator handles empty evidence gracefully"""
        from src.agents.aggregator_agent import AggregatorAgent
        
        aggregator = AggregatorAgent()
        
        # Should not raise exception
        result = aggregator.consolidate_evidence([])
        
        assert result.textual_evidence == []
        assert result.visual_evidence == []
    
    def test_verifier_handles_empty_evidence(self):
        """Test that verifier can work with empty evidence"""
        from src.agents.verifier_agent import VerifierAgent
        from src.models.data_models import ConsolidatedEvidence
        
        verifier = VerifierAgent()
        claim = AtomicClaim(
            id="claim1",
            text="Test claim",
            is_atomic=True,
            parent_claim=None,
            verification_status=None,
        )
        
        empty_evidence = ConsolidatedEvidence(
            textual_evidence=[],
            visual_evidence=[],
            metadata={},
            evidence_map={},
            reasoning_chain=None,
        )
        
        llm = LLM("gpt-4", "openai", "1.0", "https://api.openai.com")
        
        # Should not raise exception
        verdict = verifier.verify_single(claim, empty_evidence, llm)
        
        # Should return NOT_ENOUGH_INFO for empty evidence
        assert verdict.classification == VerdictType.NOT_ENOUGH_INFO


class TestConsensusTieBreaking:
    """Test consensus tie-breaking logic"""
    
    def test_tie_defaults_to_not_enough_info(self):
        """Test that tie in voting defaults to NOT_ENOUGH_INFO"""
        aggregator = MultiModelAggregator()
        
        # Create tie: 2 Supported, 2 Refuted
        verdicts = [
            Verdict("model1", VerdictType.SUPPORTED, "Just1", 0.8, []),
            Verdict("model2", VerdictType.SUPPORTED, "Just2", 0.8, []),
            Verdict("model3", VerdictType.REFUTED, "Just3", 0.8, []),
            Verdict("model4", VerdictType.REFUTED, "Just4", 0.8, []),
        ]
        
        result = aggregator.majority_poll(verdicts)
        
        assert result == VerdictType.NOT_ENOUGH_INFO
    
    def test_three_way_tie_defaults_to_not_enough_info(self):
        """Test that three-way tie defaults to NOT_ENOUGH_INFO"""
        aggregator = MultiModelAggregator()
        
        # Create three-way tie: 1 of each
        verdicts = [
            Verdict("model1", VerdictType.SUPPORTED, "Just1", 0.8, []),
            Verdict("model2", VerdictType.REFUTED, "Just2", 0.8, []),
            Verdict("model3", VerdictType.NOT_ENOUGH_INFO, "Just3", 0.5, []),
        ]
        
        result = aggregator.majority_poll(verdicts)
        
        assert result == VerdictType.NOT_ENOUGH_INFO
    
    def test_clear_majority_no_tie_breaking(self):
        """Test that clear majority doesn't trigger tie-breaking"""
        aggregator = MultiModelAggregator()
        
        # Clear majority: 3 Supported, 1 Refuted
        verdicts = [
            Verdict("model1", VerdictType.SUPPORTED, "Just1", 0.8, []),
            Verdict("model2", VerdictType.SUPPORTED, "Just2", 0.8, []),
            Verdict("model3", VerdictType.SUPPORTED, "Just3", 0.8, []),
            Verdict("model4", VerdictType.REFUTED, "Just4", 0.8, []),
        ]
        
        result = aggregator.majority_poll(verdicts)
        
        assert result == VerdictType.SUPPORTED
    
    def test_empty_verdicts_defaults_to_not_enough_info(self):
        """Test that empty verdicts list defaults to NOT_ENOUGH_INFO"""
        aggregator = MultiModelAggregator()
        
        result = aggregator.majority_poll([])
        
        assert result == VerdictType.NOT_ENOUGH_INFO
    
    def test_aggregate_verdicts_raises_on_empty_list(self):
        """Test that aggregate_verdicts raises ValueError on empty list"""
        aggregator = MultiModelAggregator()
        
        with pytest.raises(ValueError) as exc_info:
            aggregator.aggregate_verdicts([])
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_tie_justification_mentions_split(self):
        """Test that tie-breaking produces appropriate justification"""
        aggregator = MultiModelAggregator()
        
        # Create tie
        verdicts = [
            Verdict("model1", VerdictType.SUPPORTED, "Evidence supports", 0.8, []),
            Verdict("model2", VerdictType.REFUTED, "Evidence refutes", 0.8, []),
        ]
        
        consensus = aggregator.aggregate_verdicts(verdicts)
        
        assert consensus.final_classification == VerdictType.NOT_ENOUGH_INFO
        assert "split" in consensus.consensus_justification.lower() or "tie" in consensus.consensus_justification.lower()
        assert consensus.agreement_level == 0.0  # No agreement on final classification


class TestErrorResponseCreation:
    """Test error response structure creation"""
    
    def test_create_error_response(self):
        """Test creating structured error response"""
        processor = InputProcessor()
        
        error_response = processor.create_error_response(
            error_code="INPUT_001",
            error_message="Invalid input provided",
            error_stage="input_processing",
            recoverable=True,
            suggested_action="Please provide valid text or image input",
        )
        
        assert error_response.error_code == "INPUT_001"
        assert error_response.error_message == "Invalid input provided"
        assert error_response.error_stage == "input_processing"
        assert error_response.recoverable is True
        assert error_response.suggested_action == "Please provide valid text or image input"
        assert error_response.trace_id is not None
        assert len(error_response.trace_id) > 0
    
    def test_error_response_has_unique_trace_id(self):
        """Test that each error response has a unique trace ID"""
        processor = InputProcessor()
        
        error1 = processor.create_error_response(
            error_code="ERR1",
            error_message="Error 1",
        )
        
        error2 = processor.create_error_response(
            error_code="ERR2",
            error_message="Error 2",
        )
        
        assert error1.trace_id != error2.trace_id
