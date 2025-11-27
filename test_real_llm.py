"""Quick test to verify real LLM integration"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.agents.claim_decomposition_agent import ClaimDecompositionAgent
from src.models.data_models import LLM

# Check if API keys are available
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

print("=" * 60)
print("REAL LLM INTEGRATION TEST")
print("=" * 60)
print(f"OpenAI API Key: {'✓ Found' if openai_key else '✗ Not found'}")
print(f"Anthropic API Key: {'✓ Found' if anthropic_key else '✗ Not found'}")
print()

if not openai_key and not anthropic_key:
    print("❌ No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    exit(1)

# Test Claim Decomposition with real LLM
print("Testing Claim Decomposition Agent...")
print("-" * 60)

agent = ClaimDecompositionAgent()
print(f"LLM Client Type: {type(agent.llm_client).__name__}")
print()

# Test with a complex claim
test_claim = "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in 1976, and it is headquartered in Cupertino, California."

print(f"Input: {test_claim}")
print()

# Use GPT-4 if available, otherwise GPT-3.5
if openai_key:
    model = LLM(
        model_id="gpt-3.5-turbo",  # Using 3.5 for faster/cheaper testing
        provider="OpenAI",
        version="gpt-3.5-turbo",
        api_endpoint="https://api.openai.com/v1/chat/completions"
    )
    print(f"Using model: {model.model_id}")
elif anthropic_key:
    model = LLM(
        model_id="claude-3-haiku-20240307",  # Using Haiku for faster/cheaper testing
        provider="Anthropic",
        version="claude-3-haiku-20240307",
        api_endpoint="https://api.anthropic.com/v1/messages"
    )
    print(f"Using model: {model.model_id}")

print()
print("Calling LLM API...")
claims = agent.decompose(test_claim, model)

print()
print(f"✓ Success! Extracted {len(claims)} atomic claims:")
print()
for i, claim in enumerate(claims, 1):
    print(f"{i}. {claim.text}")
    print(f"   is_atomic: {claim.is_atomic}")
print()

print("=" * 60)
print("✅ Real LLM integration is working!")
print("=" * 60)
