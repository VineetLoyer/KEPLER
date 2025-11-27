"""
Quick script to test if your API keys are working
"""
import os
from src.config import config

def test_api_keys():
    """Test if API keys are properly configured"""
    
    print("🔍 Checking API Keys Configuration...\n")
    
    # Check OpenAI
    if config.api.openai_api_key:
        print(f"✅ OpenAI API Key: Found (starts with {config.api.openai_api_key[:7]}...)")
    else:
        print("❌ OpenAI API Key: NOT FOUND")
    
    # Check Anthropic
    if config.api.anthropic_api_key:
        print(f"✅ Anthropic API Key: Found (starts with {config.api.anthropic_api_key[:10]}...)")
    else:
        print("❌ Anthropic API Key: NOT FOUND")
    
    # Check Google Search
    if config.api.google_search_api_key:
        print(f"✅ Google Search API Key: Found (starts with {config.api.google_search_api_key[:6]}...)")
    else:
        print("❌ Google Search API Key: NOT FOUND")
    
    # Check Google Search Engine ID
    if config.api.google_search_engine_id:
        print(f"✅ Google Search Engine ID: Found ({config.api.google_search_engine_id[:10]}...)")
    else:
        print("❌ Google Search Engine ID: NOT FOUND")
    
    print("\n" + "="*50)
    
    # Validate configuration
    validation_messages = config.validate()
    
    if validation_messages:
        print("\n⚠️  Configuration Issues:")
        for msg in validation_messages:
            print(f"  {msg}")
    else:
        print("\n✅ All configuration checks passed!")
    
    print("\n" + "="*50)
    
    # Test OpenAI connection
    print("\n🧪 Testing OpenAI Connection...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.api.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI Error: {str(e)[:100]}")
    
    # Test Anthropic connection
    print("\n🧪 Testing Anthropic Connection...")
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=config.api.anthropic_api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'API test successful'"}]
        )
        print(f"✅ Anthropic: {response.content[0].text}")
    except Exception as e:
        print(f"❌ Anthropic Error: {str(e)[:100]}")
    
    # Test Google Search
    print("\n🧪 Testing Google Search...")
    try:
        from googleapiclient.discovery import build
        service = build("customsearch", "v1", developerKey=config.api.google_search_api_key)
        result = service.cse().list(q="test", cx=config.api.google_search_engine_id, num=1).execute()
        if 'items' in result:
            print(f"✅ Google Search: Found {len(result['items'])} result(s)")
        else:
            print("⚠️  Google Search: No results (but API is working)")
    except Exception as e:
        print(f"❌ Google Search Error: {str(e)[:100]}")
    
    print("\n" + "="*50)
    print("\n✨ API Key Testing Complete!\n")

if __name__ == "__main__":
    test_api_keys()
