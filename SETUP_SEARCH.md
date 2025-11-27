# Setting Up Real Search for KEPLER

## Quick Setup

1. **Install new dependencies:**
   ```bash
   pip install requests beautifulsoup4
   ```

2. **Create `.env` file in the project root** with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
   ```

3. **Restart the backend server:**
   ```bash
   # Stop the current server (Ctrl+C)
   # Then restart:
   uvicorn src.api.app:app --reload --port 8000
   ```

## What Changed

- Created `src/utils/google_search_client.py` - Real Google Search API client
- Created `src/utils/web_scraper.py` - Web scraper for extracting content
- Updated `src/pipeline.py` - Now uses real search when API keys are available
- Created `.env` file template

## How It Works

The system now automatically detects if Google Search API keys are configured:

- **With API keys**: Uses real Google Custom Search API to find evidence
- **Without API keys**: Falls back to mock search client (for testing)

## Getting Google Search API Keys

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Custom Search API"
4. Create credentials (API Key)
5. Create a Custom Search Engine at [programmablesearchengine.google.com](https://programmablesearchengine.google.com/)
6. Copy the Search Engine ID

## Testing

After setup, try verifying a claim like:
- "The Earth orbits the Sun"
- "Water boils at 100 degrees Celsius"

You should now see real evidence sources and proper verdicts!
