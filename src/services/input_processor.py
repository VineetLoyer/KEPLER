"""Input Processing Module for KEPLER system

This module handles input validation, LLM selection, and designation logic.
"""
from typing import Optional, List
from datetime import datetime
from src.models.data_models import MultimodalInput, ImageMetadata, LLM, ErrorResponse
import hashlib
import logging

# Configure logging
logger = logging.getLogger(__name__)


class InputValidationError(Exception):
    """Exception raised for input validation errors"""
    pass


class InputProcessor:
    """Processes and validates multimodal inputs for the KEPLER system"""
    
    def accept_input(
        self,
        text: Optional[str] = None,
        image: Optional[bytes] = None,
        image_metadata: Optional[ImageMetadata] = None,
        selected_llms: Optional[List[LLM]] = None,
        decomposition_model: Optional[LLM] = None,
    ) -> MultimodalInput:
        """Accept and validate user inputs
        
        Args:
            text: Optional text input
            image: Optional image data as bytes
            image_metadata: Optional metadata for the image
            selected_llms: List of selected LLMs for verification
            decomposition_model: LLM designated for claim decomposition
            
        Returns:
            MultimodalInput object with validated inputs
            
        Raises:
            InputValidationError: If inputs are invalid
        """
        try:
            # Validate that at least one input type is provided
            if text is None and image is None:
                error_msg = "At least one of text or image must be provided"
                logger.error(f"Input validation failed: {error_msg}")
                raise InputValidationError(error_msg)
            
            # Validate text if provided
            if text is not None:
                if not isinstance(text, str):
                    error_msg = "Text input must be a string"
                    logger.error(f"Input validation failed: {error_msg}")
                    raise InputValidationError(error_msg)
                
                # Check for empty or whitespace-only text
                if not text.strip():
                    error_msg = "Text input cannot be empty or whitespace-only"
                    logger.error(f"Input validation failed: {error_msg}")
                    raise InputValidationError(error_msg)
            
            # Validate image if provided
            if image is not None:
                if not isinstance(image, bytes):
                    error_msg = "Image input must be bytes"
                    logger.error(f"Input validation failed: {error_msg}")
                    raise InputValidationError(error_msg)
                
                if len(image) == 0:
                    error_msg = "Image data cannot be empty"
                    logger.error(f"Input validation failed: {error_msg}")
                    raise InputValidationError(error_msg)
                
                # Validate image size (max 10MB)
                max_size = 10 * 1024 * 1024  # 10MB
                if len(image) > max_size:
                    error_msg = f"Image size ({len(image)} bytes) exceeds maximum allowed size ({max_size} bytes)"
                    logger.error(f"Input validation failed: {error_msg}")
                    raise InputValidationError(error_msg)
                
                # Generate metadata if not provided
                if image_metadata is None:
                    try:
                        image_metadata = self._generate_image_metadata(image)
                    except Exception as e:
                        error_msg = f"Failed to generate image metadata: {str(e)}"
                        logger.error(f"Image metadata generation failed: {error_msg}")
                        raise InputValidationError(error_msg)
            
            # Validate LLM selection
            if selected_llms is None or len(selected_llms) == 0:
                error_msg = "At least one LLM must be selected"
                logger.error(f"Input validation failed: {error_msg}")
                raise InputValidationError(error_msg)
            
            # Validate decomposition model
            if decomposition_model is None:
                error_msg = "Decomposition model must be designated"
                logger.error(f"Input validation failed: {error_msg}")
                raise InputValidationError(error_msg)
            
            if decomposition_model not in selected_llms:
                error_msg = "Decomposition model must be one of the selected LLMs"
                logger.error(f"Input validation failed: {error_msg}")
                raise InputValidationError(error_msg)
            
            logger.info(f"Input validation successful: text={text is not None}, image={image is not None}, llms={len(selected_llms)}")
            
            # Create and return MultimodalInput
            return MultimodalInput(
                text=text,
                image=image,
                image_metadata=image_metadata,
                timestamp=datetime.now(),
                selected_llms=selected_llms,
                decomposition_model=decomposition_model,
            )
        except InputValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Catch unexpected errors and wrap them
            error_msg = f"Unexpected error during input validation: {str(e)}"
            logger.exception(error_msg)
            raise InputValidationError(error_msg)
    
    def select_llms(
        self,
        available_models: List[LLM],
        n: int,
    ) -> List[LLM]:
        """Select n LLMs from available models
        
        Args:
            available_models: Pool of available LLM models
            n: Number of models to select
            
        Returns:
            List of n selected LLMs
            
        Raises:
            InputValidationError: If n is invalid or exceeds available models
        """
        if n <= 0:
            raise InputValidationError("Number of models to select must be positive")
        
        if n > len(available_models):
            raise InputValidationError(
                f"Cannot select {n} models from {len(available_models)} available models"
            )
        
        # For now, select the first n models
        # In a real implementation, this could involve user selection or other logic
        return available_models[:n]
    
    def designate_decomposition_model(
        self,
        selected_models: List[LLM],
    ) -> LLM:
        """Designate one model from selected models for claim decomposition
        
        Args:
            selected_models: List of selected LLMs
            
        Returns:
            Designated LLM for claim decomposition
            
        Raises:
            InputValidationError: If selected_models is empty
        """
        if not selected_models or len(selected_models) == 0:
            raise InputValidationError("Cannot designate model from empty list")
        
        # For now, designate the first model
        # In a real implementation, this could involve user selection or model capability analysis
        return selected_models[0]
    
    def _generate_image_metadata(self, image: bytes) -> ImageMetadata:
        """Generate metadata for an image
        
        Args:
            image: Image data as bytes
            
        Returns:
            ImageMetadata object
        """
        # Generate hash
        image_hash = hashlib.sha256(image).hexdigest()
        
        # For now, return basic metadata
        # In a real implementation, this would analyze the image to extract format and dimensions
        return ImageMetadata(
            format="UNKNOWN",
            size_bytes=len(image),
            dimensions=(0, 0),
            hash=image_hash,
        )
    
    def create_error_response(
        self,
        error_code: str,
        error_message: str,
        error_stage: str = "input_processing",
        recoverable: bool = True,
        suggested_action: str = "",
    ) -> ErrorResponse:
        """Create a structured error response
        
        Args:
            error_code: Error code identifier
            error_message: Human-readable error message
            error_stage: Pipeline stage where error occurred
            recoverable: Whether the error is recoverable
            suggested_action: Suggested action to resolve the error
            
        Returns:
            ErrorResponse object
        """
        import uuid
        
        return ErrorResponse(
            error_code=error_code,
            error_message=error_message,
            error_stage=error_stage,
            recoverable=recoverable,
            suggested_action=suggested_action,
            trace_id=str(uuid.uuid4()),
        )
