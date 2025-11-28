"""Real LLM Client for OpenAI and Anthropic APIs"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class RealLLMClient:
    """Real LLM client that calls OpenAI and Anthropic APIs"""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        """Initialize the LLM client with API keys
        
        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            anthropic_api_key: Anthropic API key (defaults to env var)
        """
        # Get API keys and strip any whitespace/newlines
        self.openai_api_key = (openai_api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        self.anthropic_api_key = (anthropic_api_key or os.getenv("ANTHROPIC_API_KEY") or "").strip()
        
        # Set to None if empty after stripping
        if not self.openai_api_key:
            self.openai_api_key = None
        if not self.anthropic_api_key:
            self.anthropic_api_key = None
        
        # Initialize clients
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found")
            self.openai_client = None
        
        if self.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
            logger.info("Anthropic client initialized")
        else:
            logger.warning("Anthropic API key not found")
            self.anthropic_client = None
    
    def generate(self, prompt: str, model, image: Optional[bytes] = None) -> str:
        """Generate text using the specified model
        
        Args:
            prompt: Input prompt
            model: LLM model object with provider and model_id
            image: Optional image bytes for vision models
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If API key is missing or model is unsupported
        """
        provider = model.provider.lower()
        model_id = model.model_id
        
        logger.info(f"Generating with {provider}/{model_id}" + (" (with image)" if image else ""))
        
        if provider == "openai":
            return self._generate_openai(prompt, model_id, image)
        elif provider == "anthropic":
            return self._generate_anthropic(prompt, model_id, image)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _generate_openai(self, prompt: str, model_id: str, image: Optional[bytes] = None) -> str:
        """Generate using OpenAI API
        
        Args:
            prompt: Input prompt
            model_id: OpenAI model ID (e.g., "gpt-4", "gpt-3.5-turbo", "gpt-4-vision-preview")
            image: Optional image bytes for vision models
            
        Returns:
            Generated text
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Build messages based on whether image is provided
            if image:
                # Vision model - include image
                import base64
                base64_image = base64.b64encode(image).decode('utf-8')
                
                messages = [
                    {"role": "system", "content": "You are a helpful assistant for fact-checking."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
            else:
                # Text-only model
                messages = [
                    {"role": "system", "content": "You are a helpful assistant for fact-checking."},
                    {"role": "user", "content": prompt}
                ]
            
            # Build API call parameters based on model capabilities
            params = {
                "model": model_id,
                "messages": messages,
            }
            
            # GPT-5.1-chat-latest requires default temperature (1.0) and no max_tokens
            if model_id == "gpt-5.1-chat-latest":
                # Use default temperature (1.0) - don't set it
                pass
            # GPT-5.1 and GPT-4.1 don't support max_tokens but support custom temperature
            elif model_id in ["gpt-5.1", "gpt-4.1"]:
                params["temperature"] = 0.3
            # All other models support both parameters
            else:
                params["temperature"] = 0.3
                params["max_tokens"] = 1000
            
            response = self.openai_client.chat.completions.create(**params)
            
            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _generate_anthropic(self, prompt: str, model_id: str, image: Optional[bytes] = None) -> str:
        """Generate using Anthropic API
        
        Args:
            prompt: Input prompt
            model_id: Anthropic model ID (e.g., "claude-3-opus-20240229")
            image: Optional image bytes for vision models
            
        Returns:
            Generated text
        """
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env file")
        
        logger.info(f"Calling Anthropic API with model: {model_id}")
        
        try:
            # Build content based on whether image is provided
            if image:
                # Vision model - include image
                import base64
                base64_image = base64.b64encode(image).decode('utf-8')
                
                # Detect image type (default to jpeg)
                image_type = "image/jpeg"
                if image[:4] == b'\x89PNG':
                    image_type = "image/png"
                elif image[:3] == b'GIF':
                    image_type = "image/gif"
                elif image[:4] == b'RIFF' and image[8:12] == b'WEBP':
                    image_type = "image/webp"
                
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_type,
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            else:
                # Text-only
                content = prompt
            
            response = self.anthropic_client.messages.create(
                model=model_id,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            
            result = response.content[0].text.strip()
            logger.info(f"Anthropic response received: {len(result)} chars")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Anthropic API error: {error_msg}")
            
            # Provide more helpful error messages
            if "connection" in error_msg.lower():
                raise ConnectionError(f"Failed to connect to Anthropic API. Please check your internet connection. Error: {error_msg}")
            elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(f"Anthropic API authentication failed. Please check your API key. Error: {error_msg}")
            elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
                raise ValueError(f"Anthropic API rate limit exceeded. Please wait and try again. Error: {error_msg}")
            else:
                raise RuntimeError(f"Anthropic API error: {error_msg}")
