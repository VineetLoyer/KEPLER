"""Main entry point for KEPLER fact-verification system

This module provides a command-line interface for the KEPLER system,
allowing users to verify claims through text input or multimodal inputs.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import base64

from src.config import config
from src.models.data_models import MultimodalInput, LLM, ImageMetadata, VerdictType
from src.services.input_processor import InputProcessor
from src.pipeline import PipelineOrchestrator


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers,
    )


def load_image(image_path: str) -> tuple[bytes, ImageMetadata]:
    """Load an image file and extract metadata
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (image_bytes, image_metadata)
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    with open(path, "rb") as f:
        image_bytes = f.read()
    
    # Extract basic metadata
    import hashlib
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    
    metadata = ImageMetadata(
        format=path.suffix.lstrip(".").upper(),
        size_bytes=len(image_bytes),
        dimensions=(0, 0),  # Would need PIL/Pillow to extract actual dimensions
        hash=image_hash,
    )
    
    return image_bytes, metadata


def create_llm_from_string(llm_string: str) -> LLM:
    """Create an LLM object from a string specification
    
    Args:
        llm_string: String in format "provider:model:version" or "provider:model"
        
    Returns:
        LLM object
    """
    parts = llm_string.split(":")
    if len(parts) < 2:
        raise ValueError(
            f"Invalid LLM specification: {llm_string}. "
            "Expected format: provider:model[:version]"
        )
    
    provider = parts[0]
    model = parts[1]
    version = parts[2] if len(parts) > 2 else "latest"
    
    return LLM(
        model_id=f"{provider}/{model}",
        provider=provider,
        version=version,
        api_endpoint=f"https://api.{provider}.com/v1",
    )


def format_output(final_output, format_type: str = "text") -> str:
    """Format the final output for display
    
    Args:
        final_output: FinalOutput object from pipeline
        format_type: Output format ("text" or "json")
        
    Returns:
        Formatted string
    """
    if format_type == "json":
        # Convert to JSON-serializable dict
        output_dict = {
            "verdict": final_output.consensus_verdict.final_classification.value,
            "confidence": final_output.confidence_score.overall_score,
            "justification": final_output.consensus_verdict.consensus_justification,
            "atomic_claims": [
                {
                    "id": claim.id,
                    "text": claim.text,
                    "is_atomic": claim.is_atomic,
                }
                for claim in final_output.atomic_claims
            ],
            "confidence_breakdown": {
                "source_reliability": final_output.confidence_score.source_reliability,
                "model_agreement": final_output.confidence_score.model_agreement,
                "evidence_recency": final_output.confidence_score.evidence_recency,
            },
            "model_agreement": final_output.consensus_verdict.agreement_level,
            "source_links": final_output.confidence_score.structured_justification.source_links,
            "processing_metadata": final_output.processing_metadata,
        }
        return json.dumps(output_dict, indent=2)
    
    else:  # text format
        lines = []
        lines.append("=" * 80)
        lines.append("KEPLER FACT-VERIFICATION RESULT")
        lines.append("=" * 80)
        lines.append("")
        
        # Verdict
        verdict = final_output.consensus_verdict.final_classification.value
        lines.append(f"VERDICT: {verdict}")
        lines.append(f"CONFIDENCE: {final_output.confidence_score.overall_score:.2%}")
        lines.append(f"MODEL AGREEMENT: {final_output.consensus_verdict.agreement_level:.2%}")
        lines.append("")
        
        # Atomic Claims
        lines.append("ATOMIC CLAIMS:")
        for i, claim in enumerate(final_output.atomic_claims, 1):
            lines.append(f"  {i}. {claim.text}")
        lines.append("")
        
        # Justification
        lines.append("JUSTIFICATION:")
        lines.append(final_output.consensus_verdict.consensus_justification)
        lines.append("")
        
        # Confidence Breakdown
        lines.append("CONFIDENCE BREAKDOWN:")
        lines.append(f"  Source Reliability: {final_output.confidence_score.source_reliability:.2%}")
        lines.append(f"  Model Agreement: {final_output.confidence_score.model_agreement:.2%}")
        lines.append(f"  Evidence Recency: {final_output.confidence_score.evidence_recency:.2%}")
        lines.append("")
        
        # Source Links
        if final_output.confidence_score.structured_justification.source_links:
            lines.append("SOURCES:")
            for i, link in enumerate(final_output.confidence_score.structured_justification.source_links[:10], 1):
                lines.append(f"  {i}. {link}")
            if len(final_output.confidence_score.structured_justification.source_links) > 10:
                remaining = len(final_output.confidence_score.structured_justification.source_links) - 10
                lines.append(f"  ... and {remaining} more sources")
            lines.append("")
        
        # Processing Stats
        lines.append("PROCESSING STATISTICS:")
        lines.append(f"  Processing Time: {final_output.processing_metadata['processing_time_ms']:.0f}ms")
        lines.append(f"  Evidence Pieces Retrieved: {final_output.processing_metadata['num_evidence_pieces']}")
        lines.append(f"  Evidence Pieces Ranked: {final_output.processing_metadata['num_ranked_evidence']}")
        lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="KEPLER - Knowledge Extraction Pipeline for Logical Evidence and Reasoning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a text claim
  python -m src.main --text "The Earth is flat" --models openai:gpt-4 anthropic:claude-3
  
  # Verify with image
  python -m src.main --text "This is a real photo" --image photo.jpg --models openai:gpt-4
  
  # Output as JSON
  python -m src.main --text "Water boils at 100°C" --models openai:gpt-4 --format json
  
  # Save trace log
  python -m src.main --text "The moon landing was faked" --models openai:gpt-4 --trace trace.json
        """,
    )
    
    # Input arguments
    parser.add_argument(
        "--text",
        type=str,
        help="Text claim to verify",
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Path to image file (optional)",
    )
    
    # Model selection
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        required=True,
        help="LLM models to use (format: provider:model[:version])",
    )
    parser.add_argument(
        "--decomposition-model",
        type=str,
        help="Model to use for claim decomposition (defaults to first model)",
    )
    
    # Output options
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--trace",
        type=str,
        help="Save trace log to file (JSON format)",
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (default: stdout only)",
    )
    
    # Configuration options
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON format)",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate inputs
        if not args.text and not args.image:
            parser.error("At least one of --text or --image must be provided")
        
        # Load configuration if provided
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config.load_from_file(args.config)
        
        # Validate configuration
        validation_messages = config.validate()
        for msg in validation_messages:
            if msg.startswith("ERROR"):
                logger.error(msg)
                sys.exit(1)
            else:
                logger.warning(msg)
        
        # Create LLM objects
        logger.info(f"Initializing {len(args.models)} LLM models")
        selected_llms = [create_llm_from_string(m) for m in args.models]
        
        # Determine decomposition model
        if args.decomposition_model:
            decomposition_model = create_llm_from_string(args.decomposition_model)
            if decomposition_model not in selected_llms:
                logger.warning(
                    "Decomposition model not in selected models. Adding it to the list."
                )
                selected_llms.append(decomposition_model)
        else:
            decomposition_model = selected_llms[0]
        
        logger.info(f"Using {decomposition_model.model_id} for claim decomposition")
        
        # Load image if provided
        image_bytes = None
        image_metadata = None
        if args.image:
            logger.info(f"Loading image from {args.image}")
            image_bytes, image_metadata = load_image(args.image)
            logger.info(f"Image loaded: {image_metadata.size_bytes} bytes, format: {image_metadata.format}")
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            text=args.text,
            image=image_bytes,
            image_metadata=image_metadata,
            timestamp=datetime.now(),
            selected_llms=selected_llms,
            decomposition_model=decomposition_model,
        )
        
        # Initialize pipeline
        logger.info("Initializing pipeline orchestrator")
        pipeline = PipelineOrchestrator()
        
        # Process claim
        logger.info("Starting fact-verification pipeline")
        final_output = pipeline.process_claim(multimodal_input)
        logger.info("Pipeline completed successfully")
        
        # Format output
        formatted_output = format_output(final_output, args.format)
        
        # Write output
        if args.output:
            logger.info(f"Writing output to {args.output}")
            with open(args.output, "w") as f:
                f.write(formatted_output)
        else:
            print(formatted_output)
        
        # Save trace log if requested
        if args.trace:
            logger.info(f"Saving trace log to {args.trace}")
            trace_data = {
                "trace_log": final_output.trace_log,
                "summary": pipeline.get_trace_summary(),
            }
            with open(args.trace, "w") as f:
                json.dump(trace_data, f, indent=2)
        
        # Exit with appropriate code based on verdict
        if final_output.consensus_verdict.final_classification == VerdictType.SUPPORTED:
            sys.exit(0)
        elif final_output.consensus_verdict.final_classification == VerdictType.REFUTED:
            sys.exit(1)
        else:  # NOT_ENOUGH_INFO
            sys.exit(2)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.exception(f"Error during execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
