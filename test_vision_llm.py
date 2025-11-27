"""Test Vision LLM integration for image claim extraction"""
import os
from dotenv import load_dotenv
from src.agents.claim_decomposition_agent import ClaimDecompositionAgent
from src.models.data_models import LLM

# Load environment variables
load_dotenv()

# Check if API keys are available
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

print("=" * 60)
print("VISION LLM INTEGRATION TEST")
print("=" * 60)
print(f"OpenAI API Key: {'✓ Found' if openai_key else '✗ Not found'}")
print(f"Anthropic API Key: {'✓ Found' if anthropic_key else '✗ Not found'}")
print()

if not openai_key and not anthropic_key:
    print("❌ No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    exit(1)

# Create a simple test image (red square with text)
from PIL import Image, ImageDraw, ImageFont
import io

# Create test image
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)

# Add text to image
text = "The Eiffel Tower is 324 meters tall"
draw.text((20, 80), text, fill='black')

# Convert to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

print("Created test image with text:")
print(f"  '{text}'")
print()

# Test Claim Decomposition with Vision
print("Testing Vision Claim Decomposition...")
print("-" * 60)

agent = ClaimDecompositionAgent()
print(f"LLM Client Type: {type(agent.llm_client).__name__}")
print()

# Use GPT-4o (current vision model) if available
if openai_key:
    model = LLM(
        model_id="gpt-4o",
        provider="OpenAI",
        version="gpt-4o",
        api_endpoint="https://api.openai.com/v1/chat/completions"
    )
    print(f"Using model: {model.model_id}")
elif anthropic_key:
    model = LLM(
        model_id="claude-3-opus-20240229",
        provider="Anthropic",
        version="claude-3-opus-20240229",
        api_endpoint="https://api.anthropic.com/v1/messages"
    )
    print(f"Using model: {model.model_id}")

print()
print("Calling Vision LLM API...")
try:
    claims = agent.decompose(text=None, model=model, image=img_bytes)
    
    print()
    print(f"✓ Success! Extracted {len(claims)} atomic claims from image:")
    print()
    for i, claim in enumerate(claims, 1):
        print(f"{i}. {claim.text}")
        print(f"   is_atomic: {claim.is_atomic}")
    print()
    
    print("=" * 60)
    print("✅ Vision LLM integration is working!")
    print("=" * 60)
    
except Exception as e:
    print()
    print(f"❌ Error: {str(e)}")
    print()
    print("Note: Vision models may not be available in your plan.")
    print("Try using gpt-4o or claude-3-opus-20240229 instead.")
