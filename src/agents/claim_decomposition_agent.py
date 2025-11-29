"""Claim Decomposition Agent for KEPLER system

This module handles the extraction of atomic claims from complex input text and images.
Each atomic claim is a minimal, self-contained factual statement that can be
independently verified.
"""
from typing import List, Optional, Protocol
from src.models.data_models import AtomicClaim, LLM
import uuid
import logging
import os

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM client implementations"""
    
    def generate(self, prompt: str, model: LLM) -> str:
        """Generate text from a prompt using the specified model"""
        ...


class ClaimDecompositionAgent:
    """Agent responsible for decomposing complex claims into atomic claims"""
    
    # Prompt template for claim decomposition
    DECOMPOSITION_PROMPT = """You are a fact-checking assistant. Extract atomic claims from the given text.

An atomic claim is:
- A minimal, self-contained factual statement
- Independently verifiable without additional context
- Contains only ONE factual assertion
- Preserves the original meaning and context

CRITICAL RULES FOR EXTRACTION:

1. **KEEP TOGETHER (Do NOT split):**
   - Lists of people, places, or things (e.g., "A, B, and C")
   - Related facts about the same subject (e.g., "X is Y and located at Z")
   - Compound sentences with "and" connecting related info about same subject
   - Example: "Mount Everest is 8,849m tall and located on the Nepal-China border" → ONE claim

2. **SPLIT ONLY when:**
   - Facts are about DIFFERENT subjects
   - Facts are INDEPENDENT and can be verified separately
   - Example: "Earth is the third planet. Mars is the fourth planet." → TWO claims

3. **CONSISTENCY:**
   - Extract the SAME number of claims regardless of model
   - Be CONSERVATIVE - when in doubt, keep claims together
   - Aim for 5-8 claims for a typical paragraph

Text: {text}

===== REQUIRED OUTPUT FORMAT =====
Output ONLY a numbered list. NO explanations. NO notes. NO commentary. NO "Let me analyze" or "Here are the claims" or similar phrases.

CORRECT FORMAT:
1. [First atomic claim]
2. [Second atomic claim]
3. [Third atomic claim]

INCORRECT FORMAT (DO NOT DO THIS):
"Let me analyze this text. Here are the atomic claims:
1. [claim]
Note: I kept related facts together."

If no factual claims exist, respond with only: NO_CLAIMS
"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the Claim Decomposition Agent
        
        Args:
            llm_client: Optional LLM client for making API calls.
                       If None, tries to use real LLM client if API keys are available,
                       otherwise falls back to mock client.
        """
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            # Try to use real LLM client if API keys are available
            openai_key = os.getenv("OPENAI_API_KEY")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            
            if openai_key or anthropic_key:
                try:
                    from src.utils.llm_client import RealLLMClient
                    self.llm_client = RealLLMClient(openai_key, anthropic_key)
                    logger.info("Using real LLM client for claim decomposition")
                except Exception as e:
                    logger.warning(f"Failed to initialize real LLM client: {e}. Using mock.")
                    self.llm_client = MockLLMClient()
            else:
                logger.warning("No LLM API keys found. Using mock LLM client.")
                self.llm_client = MockLLMClient()
    
    def decompose(self, text: Optional[str], model: LLM, image: Optional[bytes] = None) -> List[AtomicClaim]:
        """Decompose input text and/or image into atomic claims
        
        Args:
            text: Optional input text containing one or more claims
            model: LLM model to use for decomposition
            image: Optional image bytes for vision models
            
        Returns:
            List of AtomicClaim objects
        """
        # Need at least text or image
        if (not text or not text.strip()) and not image:
            return []
        
        # Generate prompt based on input type
        if image and text:
            # Both text and image
            prompt = self.DECOMPOSITION_PROMPT.format(
                text=f"Text: {text}\n\nPlease also analyze the provided image and extract any claims from it."
            )
            original_input = f"{text} [with image]"
        elif image:
            # Image only
            prompt = """You are a fact-checking assistant. Your task is to extract atomic claims from the provided image.

An atomic claim is:
- A minimal, self-contained factual statement
- Independently verifiable without additional context
- Contains only one factual assertion
- Preserves the original meaning and context

IMPORTANT: Keep lists of people, places, or things together as a single claim.

Analyze the image and extract all factual claims you can identify. This includes:
- Text visible in the image (screenshots, memes, infographics)
- Visual information (objects, people, places, events)
- Any factual statements or assertions made

Format your response as a numbered list, with one claim per line:
1. [First atomic claim]
2. [Second atomic claim]
...

If the image contains no factual claims, respond with "NO_CLAIMS"."""
            original_input = "[image]"
        else:
            # Text only (original behavior)
            prompt = self.DECOMPOSITION_PROMPT.format(text=text)
            original_input = text
        
        # Call LLM (with image if provided)
        response = self.llm_client.generate(prompt, model, image=image)
        
        # Parse response into atomic claims
        claims = self._parse_llm_response(response, original_input)
        
        return claims
    
    def validate_atomicity(self, claim: AtomicClaim) -> bool:
        """Validate that a claim is truly atomic
        
        Args:
            claim: AtomicClaim to validate
            
        Returns:
            True if the claim is atomic, False otherwise
        """
        # Basic validation rules for atomicity
        text = claim.text.strip()
        
        # Empty claims are not atomic
        if not text:
            return False
        
        # Claims with multiple sentences are likely not atomic
        # Count sentences by looking for sentence-ending punctuation followed by space or end of string
        import re
        # Match sentence endings: period, exclamation, or question mark followed by space and capital letter
        # or at the end of the string (but not the final punctuation)
        sentence_pattern = r'[.!?]\s+[A-Z]'
        sentence_breaks = re.findall(sentence_pattern, text)
        
        # If there are sentence breaks (indicating multiple sentences), it's compound
        if len(sentence_breaks) > 0:
            return False
        
        # Check for common compound indicators
        compound_indicators = [
            ' and ',
            ' but ',
            ' however ',
            ' moreover ',
            ' furthermore ',
            ' additionally ',
            '; ',
        ]
        
        # If multiple compound indicators are present, likely not atomic
        indicator_count = sum(1 for indicator in compound_indicators if indicator.lower() in text.lower())
        if indicator_count > 1:
            return False
        
        # If we get here, the claim passes basic atomicity checks
        return True
    
    def _parse_llm_response(self, response: str, original_text: str) -> List[AtomicClaim]:
        """Parse LLM response into AtomicClaim objects
        
        Args:
            response: Raw response from LLM
            original_text: Original input text
            
        Returns:
            List of AtomicClaim objects
        """
        claims = []
        
        # Handle "NO_CLAIMS" response
        if "NO_CLAIMS" in response.upper():
            return claims
        
        # Parse numbered list format
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are clearly not claims (explanatory text from Claude)
            skip_patterns = [
                'let me analyze',
                'note:',
                'here are',
                'i will',
                'i have',
                'the claims are',
                'extracted claims',
                'atomic claims:',
                'factual claims:',
            ]
            if any(pattern in line.lower() for pattern in skip_patterns):
                continue
            
            # Remove numbering (e.g., "1. ", "2) ", etc.)
            # Match patterns like "1.", "1)", "1 -", etc.
            import re
            claim_text = re.sub(r'^\d+[\.\)\-\:]\s*', '', line)
            
            # Skip empty claims after removing numbering
            if not claim_text:
                continue
            
            # Create AtomicClaim
            claim = AtomicClaim(
                id=str(uuid.uuid4()),
                text=claim_text,
                is_atomic=True,  # Assume LLM produces atomic claims
                parent_claim=original_text,
                verification_status=None,
            )
            
            # Validate atomicity
            claim.is_atomic = self.validate_atomicity(claim)
            
            claims.append(claim)
        
        # If no claims were parsed but response wasn't "NO_CLAIMS",
        # treat the entire response as a single claim
        if not claims and response.strip():
            claim = AtomicClaim(
                id=str(uuid.uuid4()),
                text=response.strip(),
                is_atomic=True,
                parent_claim=original_text,
                verification_status=None,
            )
            claim.is_atomic = self.validate_atomicity(claim)
            claims.append(claim)
        
        return claims


class MockLLMClient:
    """Mock LLM client for testing purposes
    
    This client simulates LLM behavior by applying simple heuristics
    to decompose claims. It's used when no real LLM client is provided.
    """
    
    def generate(self, prompt: str, model: LLM) -> str:
        """Generate a mock response for claim decomposition
        
        Args:
            prompt: Input prompt (contains the text to decompose)
            model: LLM model (ignored in mock)
            
        Returns:
            Mock response in the expected format
        """
        # Extract the text from the prompt
        import re
        text_match = re.search(r'Text: (.+?)(?:\n\nInstructions:|$)', prompt, re.DOTALL)
        if not text_match:
            return "NO_CLAIMS"
        
        text = text_match.group(1).strip()
        
        if not text:
            return "NO_CLAIMS"
        
        # Simple heuristic: split on common conjunctions and sentence boundaries
        # This is a very basic decomposition for testing purposes
        claims = []
        
        # Split on sentence boundaries, but avoid common abbreviations
        # Look for period followed by space and capital letter (but not Inc., Dr., etc.)
        # For simplicity, just look for period at end of text or period followed by space and capital
        # that's not part of common abbreviations
        sentences = []
        
        # Simple approach: split on ". " but rejoin if it's a known abbreviation
        temp_sentences = text.split('. ')
        current_sentence = ""
        
        for i, part in enumerate(temp_sentences):
            current_sentence += part
            
            # Check if this part ends with a common abbreviation
            is_abbreviation = any(current_sentence.endswith(abbr) for abbr in 
                                 ['Inc', 'Corp', 'Ltd', 'Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'Sr', 'Jr'])
            
            if is_abbreviation and i < len(temp_sentences) - 1:
                # This is an abbreviation, keep the period and continue
                current_sentence += '. '
            else:
                # This is a real sentence boundary
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Look for ", and" pattern which typically connects independent clauses
            # This avoids splitting lists like "A, B, and C"
            # Strategy: Look specifically for ", and" followed by a pronoun (strongest indicator)
            if ', and ' in sentence.lower():
                # Find all positions of ", and"
                import re
                pattern = r',\s+and\s+(it|he|she|they|we|i)\s+'
                match = re.search(pattern, sentence, flags=re.IGNORECASE)
                
                if match:
                    # Found ", and [pronoun]" - this is very likely an independent clause
                    split_pos = match.start()
                    
                    part1 = sentence[:split_pos].strip()
                    part2 = sentence[split_pos + 1:].strip()  # +1 to skip the comma
                    
                    # Remove "and " from start of part2
                    if part2.lower().startswith('and '):
                        part2 = part2[4:].strip()
                    
                    # Only split if both parts are substantial
                    if len(part1) > 15 and len(part2) > 15:
                        claims.append(part1)
                        claims.append(part2)
                    else:
                        claims.append(sentence)
                else:
                    # No ", and [pronoun]" found, keep together
                    # This handles lists like "A, B, and C"
                    claims.append(sentence)
            else:
                # No ", and" pattern, keep as single claim
                claims.append(sentence)
        
        if not claims:
            return "NO_CLAIMS"
        
        # Format as numbered list
        response = '\n'.join(f"{i+1}. {claim}" for i, claim in enumerate(claims))
        return response
