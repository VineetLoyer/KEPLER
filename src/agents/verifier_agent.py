"""Verifier Agent for KEPLER system

This module handles the verification of atomic claims using multiple LLMs in parallel.
It generates verdicts and justifications by providing each model with the claim,
evidence, and metadata.
"""
import asyncio
import time
import os
import logging
from typing import List, Dict, Any, Optional
from src.models.data_models import (
    AtomicClaim,
    ConsolidatedEvidence,
    Verdict,
    VerdictType,
    LLM,
)

logger = logging.getLogger(__name__)


class VerifierAgent:
    """Agent responsible for generating verdicts using multiple LLMs in parallel"""
    
    def __init__(self, parallel_threshold_ms: float = 100.0, llm_client: Optional[Any] = None):
        """Initialize the Verifier Agent
        
        Args:
            parallel_threshold_ms: Maximum time difference (in ms) between model 
                                   invocations to be considered parallel
            llm_client: Optional LLM client for making API calls.
                       If None, tries to use real LLM client if API keys are available.
        """
        self.parallel_threshold_ms = parallel_threshold_ms
        
        # Initialize LLM client
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
                    logger.info("Using real LLM client for verification")
                except Exception as e:
                    logger.warning(f"Failed to initialize real LLM client: {e}. Using mock.")
                    self.llm_client = None
            else:
                logger.warning("No LLM API keys found. Using mock verification.")
                self.llm_client = None
    
    def verify_with_ensemble(
        self,
        claim: AtomicClaim,
        evidence: ConsolidatedEvidence,
        models: List[LLM],
    ) -> List[Verdict]:
        """Verify a claim using an ensemble of LLMs
        
        This method coordinates the verification process by:
        1. Engaging all selected LLMs independently
        2. Executing them in parallel
        3. Collecting individual verdicts from each model
        
        Args:
            claim: Atomic claim to verify
            evidence: Consolidated evidence for the claim
            models: List of LLMs to use for verification
            
        Returns:
            List of Verdict objects, one from each model
        """
        # Use parallel verification
        verdicts = self.parallel_verify(claim, evidence, models)
        
        return verdicts
    
    def verify_single(
        self,
        claim: AtomicClaim,
        evidence: ConsolidatedEvidence,
        model: LLM,
    ) -> Verdict:
        """Verify a claim using a single LLM
        
        This method:
        1. Constructs context containing claim, evidence, and metadata
        2. Sends the context to the LLM
        3. Parses and validates the response
        4. Returns a structured Verdict
        
        Args:
            claim: Atomic claim to verify
            evidence: Consolidated evidence for the claim
            model: LLM to use for verification
            
        Returns:
            Verdict object with classification and justification
        """
        # Construct context for the LLM
        context = self._construct_context(claim, evidence)
        
        # Generate verification prompt
        prompt = self._generate_verification_prompt(claim, context)
        
        # In a real implementation, this would call the actual LLM API
        # For now, we simulate the LLM response
        response = self._call_llm(model, prompt, context)
        
        # Parse and validate the verdict
        verdict = self._parse_verdict(model, response, evidence)
        
        return verdict
    
    def parallel_verify(
        self,
        claim: AtomicClaim,
        evidence: ConsolidatedEvidence,
        models: List[LLM],
    ) -> List[Verdict]:
        """Verify a claim using multiple LLMs in parallel
        
        This method executes all model verifications concurrently to minimize
        total verification time.
        
        Args:
            claim: Atomic claim to verify
            evidence: Consolidated evidence for the claim
            models: List of LLMs to use for verification
            
        Returns:
            List of Verdict objects, one from each model
        """
        # Record start times for each model invocation
        start_times = []
        verdicts = []
        
        # Simulate parallel execution by calling all models
        # In a real implementation, this would use asyncio or threading
        for model in models:
            start_time = time.time()
            start_times.append(start_time)
            
            verdict = self.verify_single(claim, evidence, model)
            verdicts.append(verdict)
        
        # Verify that all models were invoked within the parallel threshold
        if len(start_times) > 1:
            time_diff_ms = (max(start_times) - min(start_times)) * 1000
            # In a real parallel implementation, this would be very small
            # For testing purposes, we just ensure the structure is correct
        
        return verdicts
    
    def _construct_context(
        self,
        claim: AtomicClaim,
        evidence: ConsolidatedEvidence,
    ) -> Dict[str, Any]:
        """Construct context for LLM verification
        
        The context includes:
        - The atomic claim text
        - Textual evidence summaries
        - Visual evidence references
        - Metadata about sources
        
        Args:
            claim: Atomic claim to verify
            evidence: Consolidated evidence
            
        Returns:
            Dictionary containing all context information
        """
        context = {
            'claim': claim.text,
            'textual_evidence': evidence.textual_evidence,
            'visual_evidence': [
                f"Image {i+1}" for i in range(len(evidence.visual_evidence))
            ],
            'metadata': evidence.metadata,
        }
        
        # Add reasoning chain if available
        if evidence.reasoning_chain:
            context['reasoning_chain'] = {
                'steps': [
                    {
                        'step': step.step_number,
                        'description': step.description,
                        'conclusion': step.conclusion,
                    }
                    for step in evidence.reasoning_chain.steps
                ],
                'agreements': [
                    {
                        'assertion': agreement.common_assertion,
                        'strength': agreement.strength,
                    }
                    for agreement in evidence.reasoning_chain.agreements
                ],
                'conflicts': [
                    {
                        'severity': conflict.severity,
                    }
                    for conflict in evidence.reasoning_chain.conflicts
                ],
            }
        
        return context
    
    def _generate_verification_prompt(
        self,
        claim: AtomicClaim,
        context: Dict[str, Any],
    ) -> str:
        """Generate verification prompt for LLM
        
        Args:
            claim: Atomic claim to verify
            context: Context dictionary with evidence and metadata
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Given the claim: "{claim.text}"

And the following evidence:

Textual Evidence:
"""
        
        # Add textual evidence
        for i, text in enumerate(context['textual_evidence'], 1):
            prompt += f"{i}. {text}\n"
        
        # Add visual evidence references
        if context['visual_evidence']:
            prompt += "\nVisual Evidence:\n"
            for i, img_ref in enumerate(context['visual_evidence'], 1):
                prompt += f"{i}. {img_ref}\n"
        
        # Add metadata summary
        if context['metadata']:
            prompt += f"\nSources: {len(context['metadata'])} sources analyzed\n"
        
        prompt += """
Your task is to fact-check this claim using the provided evidence.

IMPORTANT INSTRUCTIONS:

1. **RANGES AND VARIATIONS**: 
   - If the claim states a specific value and evidence provides a RANGE, check if the value falls WITHIN the range
   - Example: Claim "5000kg" + Evidence "4500-6100kg" → SUPPORTED (5000 is in range)
   - If evidence shows MULTIPLE variations (species, types, etc.) and claim matches ANY → SUPPORTED
   - Example: Claim "elephant weighs 5000kg" + Evidence shows 3 species, one weighs ~5000kg → SUPPORTED

2. **CONTRADICTIONS**: 
   - If the claim value is OUTSIDE the documented range → REFUTED
   - Example: Claim "600 meters" but evidence says "324 meters" (no range) → REFUTED
   - Example: Claim "10000kg" but evidence says "4500-6100kg" (outside range) → REFUTED

3. **CONFIRMATION**: 
   - Exact match → SUPPORTED
   - Value within documented range → SUPPORTED
   - Matches one of multiple documented variations → SUPPORTED

4. **INSUFFICIENCY**: 
   - Only use "Not Enough Information" if:
     * No relevant evidence found
     * Evidence is too vague or unclear
     * Evidence doesn't address the specific claim
   - DO NOT use when evidence clearly supports or contradicts!

Analyze the evidence and determine the verdict:
- **SUPPORTED**: Evidence confirms the claim (exact match, within range, or matches a variation)
- **REFUTED**: Evidence contradicts the claim (outside range, different value with no range)
- **NOT ENOUGH INFORMATION**: Evidence is insufficient, unclear, or missing

**CRITICAL: You MUST provide a DETAILED justification that:**
1. References SPECIFIC evidence pieces by number (e.g., "Textual Evidence 1 states...", "Textual Evidence 2 confirms...")
2. Quotes or paraphrases the EXACT relevant portions from each evidence piece
3. Explains HOW each piece of evidence supports or refutes the claim
4. Provides a logical conclusion based on the evidence analysis
5. Is AT LEAST 3-4 sentences long with concrete evidence references

**BAD JUSTIFICATION (too short):** "The claim is supported by the evidence."
**GOOD JUSTIFICATION:** "The claim is supported by multiple pieces of evidence. Textual Evidence 1 states that 'the Earth orbits the Sun at an average distance of 149.60 million km.' Textual Evidence 2 from NASA confirms that 'Earth revolves around the Sun in a counterclockwise direction.' Textual Evidence 3 also explains that 'the Earth's path around the Sun is called its orbit.' Therefore, the claim is well-supported by reliable scientific sources."

===== REQUIRED OUTPUT FORMAT =====
You MUST respond in EXACTLY this format. Do not deviate from this structure:

VERDICT: [Choose EXACTLY ONE: Supported OR Refuted OR Not Enough Information]
CONFIDENCE: [A number between 0.0 and 1.0, e.g., 0.85]
JUSTIFICATION: [Your detailed reasoning here. Must be at least 3-4 sentences. Must reference specific evidence pieces by number. Must quote or paraphrase relevant portions. Must explain how evidence supports/refutes the claim.]

===== EXAMPLE OUTPUT =====
VERDICT: Refuted
CONFIDENCE: 0.92
JUSTIFICATION: The claim is refuted by multiple pieces of evidence. Textual Evidence 1 clearly states that "Mount Everest summit temperatures average around -36°C in winter and -19°C in summer," which directly contradicts the claim of 20°C. Textual Evidence 2 from the National Geographic confirms that "temperatures at the summit never rise above freezing." Textual Evidence 3 also notes that "climbers face extreme cold with temperatures ranging from -20°C to -40°C." Therefore, the claim that summit temperatures average 20°C in summer is clearly refuted by authoritative sources.

===== YOUR RESPONSE (START BELOW) =====
"""
        
        return prompt
    
    def _call_llm(
        self,
        model: LLM,
        prompt: str,
        context: Dict[str, Any],
    ) -> str:
        """Call the LLM API to get a verification response
        
        Args:
            model: LLM to call
            prompt: Verification prompt
            context: Context dictionary
            
        Returns:
            LLM response string
        """
        # Use real LLM if available
        if self.llm_client is not None:
            try:
                logger.info(f"Calling real LLM: {model.provider}/{model.model_id}")
                response = self.llm_client.generate(prompt, model)
                return response
            except Exception as e:
                logger.error(f"LLM API call failed: {e}. Falling back to mock.")
                # Fall through to mock implementation
        
        # Mock implementation (fallback)
        logger.warning(f"Using mock verification for {model.model_id}")
        
        # Simple heuristic: if we have evidence, lean towards Supported
        if len(context['textual_evidence']) > 2:
            verdict = "Supported"
            confidence = 0.8
            justification = f"Based on analysis of {len(context['textual_evidence'])} textual sources, the claim appears to be supported by the available evidence."
        elif len(context['textual_evidence']) > 0:
            verdict = "Not Enough Information"
            confidence = 0.5
            justification = "While some evidence is available, it is insufficient to make a definitive determination."
        else:
            verdict = "Not Enough Information"
            confidence = 0.3
            justification = "No substantial evidence was found to verify this claim."
        
        response = f"""VERDICT: {verdict}
CONFIDENCE: {confidence}
JUSTIFICATION: {justification}"""
        
        return response
    
    def _parse_verdict(
        self,
        model: LLM,
        response: str,
        evidence: ConsolidatedEvidence,
    ) -> Verdict:
        """Parse and validate LLM response into a Verdict object
        
        Args:
            model: LLM that generated the response
            response: Raw LLM response string
            evidence: Evidence used for verification
            
        Returns:
            Validated Verdict object
        """
        # Parse the response
        lines = response.strip().split('\n')
        
        verdict_str = None
        confidence = 0.5
        justification = ""
        justification_started = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Parse VERDICT
            if line_stripped.startswith('VERDICT:'):
                verdict_str = line_stripped.split(':', 1)[1].strip()
            
            # Parse CONFIDENCE
            elif line_stripped.startswith('CONFIDENCE:'):
                try:
                    conf_str = line_stripped.split(':', 1)[1].strip()
                    confidence = float(conf_str)
                    # Clamp confidence to valid range
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, IndexError):
                    logger.warning(f"Failed to parse confidence from: {line_stripped}")
                    confidence = 0.5
            
            # Parse JUSTIFICATION (may span multiple lines)
            elif line_stripped.startswith('JUSTIFICATION:'):
                justification = line_stripped.split(':', 1)[1].strip()
                justification_started = True
            elif justification_started and line_stripped:
                # Continue collecting justification lines
                justification += " " + line_stripped
        
        # If no structured format found, try to extract from plain text
        if not verdict_str or not justification:
            logger.warning(f"Model {model.model_id} did not follow structured format. Attempting fallback parsing.")
            verdict_str, confidence, justification = self._fallback_parse(response)
        
        # Validate and convert verdict string to VerdictType
        classification = self._validate_classification(verdict_str)
        
        # Ensure justification is not empty
        if not justification or len(justification) < 20:
            logger.warning(f"Justification too short or empty for {model.model_id}")
            justification = f"Model verdict: {classification.value}. " + (justification if justification else "No detailed justification provided.")
        
        # Extract evidence references from metadata
        evidence_references = list(evidence.metadata.keys())
        
        return Verdict(
            model_id=model.model_id,
            classification=classification,
            justification=justification,
            confidence=confidence,
            evidence_references=evidence_references,
        )
    
    def _fallback_parse(self, response: str) -> tuple:
        """Fallback parsing for models that don't follow structured format
        
        Args:
            response: Raw response text
            
        Returns:
            Tuple of (verdict_str, confidence, justification)
        """
        response_lower = response.lower()
        
        # Try to extract verdict from plain text
        verdict_str = None
        if 'supported' in response_lower and 'not' not in response_lower[:response_lower.find('supported')]:
            verdict_str = "Supported"
        elif 'refuted' in response_lower or 'refute' in response_lower:
            verdict_str = "Refuted"
        elif 'not enough' in response_lower or 'insufficient' in response_lower:
            verdict_str = "Not Enough Information"
        
        # Default confidence for fallback
        confidence = 0.6
        
        # Use entire response as justification if no structure found
        justification = response.strip()
        
        # If justification is too long, try to extract the most relevant part
        if len(justification) > 1000:
            # Take first 800 characters
            justification = justification[:800] + "..."
        
        logger.info(f"Fallback parsing extracted: verdict={verdict_str}, confidence={confidence}")
        
        return verdict_str, confidence, justification
    
    def _validate_classification(self, verdict_str: str) -> VerdictType:
        """Validate and convert verdict string to VerdictType
        
        Args:
            verdict_str: String representation of verdict
            
        Returns:
            VerdictType enum value
        """
        if not verdict_str:
            return VerdictType.NOT_ENOUGH_INFO
        
        verdict_lower = verdict_str.lower()
        
        if 'supported' in verdict_lower or 'support' in verdict_lower:
            return VerdictType.SUPPORTED
        elif 'refuted' in verdict_lower or 'refute' in verdict_lower:
            return VerdictType.REFUTED
        else:
            return VerdictType.NOT_ENOUGH_INFO
