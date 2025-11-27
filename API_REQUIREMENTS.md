# KEPLER API Requirements Guide

This guide explains what APIs you need to run KEPLER and how to get them.

## 🔑 Required APIs (Minimum to Run)

### 1. **OpenAI API** ⭐ REQUIRED
**What it's for**: LLM models for claim decomposition and verification

**How to get it**:
1. Go to https://platform.openai.com/signup
2. Sign up for an account
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-...`)

**Cost**: Pay-as-you-go
- GPT-4: ~$0.03 per 1K tokens
- GPT-3.5-Turbo: ~$0.002 per 1K tokens
- Typical claim verification: $0.05-0.20

**Models used**:
- `gpt-4` - Best quality
- `gpt-4-turbo` - Faster, cheaper
- `gpt-3.5-turbo` - Budget option

---

### 2. **Anthropic API** ⭐ REQUIRED
**What it's for**: Claude models for verification (alternative/ensemble with OpenAI)

**How to get it**:
1. Go to https://console.anthropic.com/
2. Sign up for an account
3. Go to API Keys section
4. Generate a new API key
5. Copy the key

**Cost**: Pay-as-you-go
- Claude 3 Opus: ~$0.015 per 1K tokens
- Claude 3 Sonnet: ~$0.003 per 1K tokens
- Claude 3 Haiku: ~$0.00025 per 1K tokens

**Models used**:
- `claude-3-opus` - Highest quality
- `claude-3-sonnet` - Balanced
- `claude-3-haiku` - Fast and cheap

---

### 3. **Google Search API** ⭐ REQUIRED
**What it's for**: Finding evidence from the web

**How to get it**:
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable "Custom Search API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key

**Then create a Custom Search Engine**:
1. Go to https://programmablesearchengine.google.com/
2. Click "Add" to create new search engine
3. Set "Search the entire web"
4. Get your Search Engine ID (looks like: `abc123def456...`)

**Cost**: 
- Free tier: 100 queries/day
- Paid: $5 per 1,000 queries after free tier
- Typical usage: 5-10 queries per claim

---

## 🔧 Optional APIs (Enhanced Features)

### 4. **Bing Search API** (Optional)
**What it's for**: Alternative/backup search provider

**How to get it**:
1. Go to https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
2. Sign up for Azure account
3. Create Bing Search resource
4. Copy the API key

**Cost**:
- Free tier: 1,000 queries/month
- Paid: $7 per 1,000 queries

**When to use**: Backup if Google Search quota exceeded

---

### 5. **Google Vision API** (Optional)
**What it's for**: Analyzing images for multimodal claims

**How to get it**:
1. Same Google Cloud project as Search API
2. Enable "Cloud Vision API"
3. Use same API key or create new one

**Cost**:
- Free tier: 1,000 requests/month
- Paid: $1.50 per 1,000 images

**When to use**: Only if you want image analysis features

---

## 📋 Quick Setup Checklist

### Minimum Setup (Required)
- [ ] OpenAI API key
- [ ] Anthropic API key  
- [ ] Google Search API key
- [ ] Google Search Engine ID

### Full Setup (All Features)
- [ ] All minimum APIs above
- [ ] Bing Search API key (optional)
- [ ] Google Vision API key (optional)

---

## 💰 Cost Estimates

### Light Usage (10 claims/day)
- OpenAI: ~$2-5/month
- Anthropic: ~$1-3/month
- Google Search: Free (within 100/day limit)
- **Total: ~$3-8/month**

### Medium Usage (100 claims/day)
- OpenAI: ~$20-50/month
- Anthropic: ~$10-30/month
- Google Search: ~$15-30/month
- **Total: ~$45-110/month**

### Heavy Usage (1000 claims/day)
- OpenAI: ~$200-500/month
- Anthropic: ~$100-300/month
- Google Search: ~$150-300/month
- **Total: ~$450-1100/month**

---

## 🔐 Setting Up API Keys

### Option 1: Environment Variables (Recommended for Production)

**On Railway/Vercel/Netlify**:
Add these in your platform's environment variables section:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_SEARCH_API_KEY=AIza...
GOOGLE_SEARCH_ENGINE_ID=abc123...
BING_SEARCH_API_KEY=... (optional)
GOOGLE_VISION_API_KEY=... (optional)
```

**On Local Machine (Windows)**:
```cmd
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-ant-...
set GOOGLE_SEARCH_API_KEY=AIza...
set GOOGLE_SEARCH_ENGINE_ID=abc123...
```

**On Local Machine (Mac/Linux)**:
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_SEARCH_API_KEY=AIza...
export GOOGLE_SEARCH_ENGINE_ID=abc123...
```

### Option 2: Configuration File (Local Development)

Create a `config.json` file (don't commit to git!):

```json
{
  "api": {
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-...",
    "google_search_api_key": "AIza...",
    "google_search_engine_id": "abc123...",
    "bing_search_api_key": "optional",
    "google_vision_api_key": "optional"
  }
}
```

Then load it in your code:
```python
from src.config import config
config.load_from_file("config.json")
```

---

## 🎯 Which Models Are Used Where?

### Claim Decomposition Agent
- Uses: OpenAI GPT-4 or GPT-3.5-Turbo
- Purpose: Break down complex claims into atomic claims
- Frequency: Once per claim

### Retriever Agent
- Uses: Google Search API (or Bing as backup)
- Purpose: Find evidence from the web
- Frequency: 5-10 searches per claim

### Verifier Agent
- Uses: Multiple LLMs (OpenAI + Anthropic)
- Purpose: Verify claims against evidence
- Frequency: 2-5 model calls per claim

### Aggregator Agent
- Uses: OpenAI GPT-4
- Purpose: Combine evidence and reasoning
- Frequency: Once per claim

### Confidence Scorer
- Uses: No external APIs (internal logic)
- Purpose: Calculate confidence scores
- Frequency: Once per claim

---

## 🚨 Common Issues

### "OpenAI API key not found"
**Solution**: Make sure `OPENAI_API_KEY` environment variable is set

### "Google Search quota exceeded"
**Solution**: 
- Wait until next day (free tier resets daily)
- Upgrade to paid tier
- Add Bing Search API as backup

### "Rate limit exceeded"
**Solution**:
- Add delays between requests
- Upgrade to higher tier
- Use multiple API keys (not recommended)

### "Invalid API key"
**Solution**:
- Check for extra spaces or quotes
- Regenerate the key
- Make sure key has correct permissions

---

## 🔒 Security Best Practices

1. **Never commit API keys to git**
   - Add `config.json` to `.gitignore`
   - Use environment variables in production

2. **Rotate keys regularly**
   - Change keys every 3-6 months
   - Immediately rotate if exposed

3. **Set usage limits**
   - Set billing alerts in provider dashboards
   - Set rate limits in your code

4. **Use separate keys for dev/prod**
   - Different keys for testing vs production
   - Easier to track usage and costs

---

## 📊 Monitoring Usage

### OpenAI
- Dashboard: https://platform.openai.com/usage
- Set billing limits in account settings

### Anthropic
- Dashboard: https://console.anthropic.com/
- Monitor usage in dashboard

### Google Cloud
- Dashboard: https://console.cloud.google.com/
- Set up billing alerts
- Monitor API usage per service

---

## 🎓 Free Tier Limits Summary

| Service | Free Tier | Limit |
|---------|-----------|-------|
| OpenAI | $5 credit (new users) | Expires after 3 months |
| Anthropic | $5 credit (new users) | Expires after 1 month |
| Google Search | 100 queries/day | Resets daily |
| Bing Search | 1,000 queries/month | Resets monthly |
| Google Vision | 1,000 requests/month | Resets monthly |

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] All required API keys are set
- [ ] Keys are valid (test with a simple request)
- [ ] Billing is set up (if using paid tiers)
- [ ] Usage alerts are configured
- [ ] Keys are not in git repository
- [ ] Environment variables are set in deployment platform

---

## 🆘 Need Help?

**Getting API Keys**:
- OpenAI: https://platform.openai.com/docs/quickstart
- Anthropic: https://docs.anthropic.com/claude/docs/getting-started
- Google Cloud: https://cloud.google.com/docs/get-started

**Pricing Questions**:
- OpenAI Pricing: https://openai.com/pricing
- Anthropic Pricing: https://www.anthropic.com/pricing
- Google Cloud Pricing: https://cloud.google.com/pricing

**Technical Issues**:
- Check your `config.py` file
- Run `config.validate()` to check configuration
- Review error logs for specific API errors

---

## 🚀 Quick Start

1. **Get minimum required APIs** (OpenAI, Anthropic, Google Search)
2. **Set environment variables** on your deployment platform
3. **Test locally** with a simple claim
4. **Monitor usage** in first few days
5. **Adjust as needed** based on usage patterns

**Estimated time to set up all APIs: 30-45 minutes**

---

## 💡 Pro Tips

1. **Start with free tiers** - Test everything before committing to paid plans
2. **Use GPT-3.5-Turbo for testing** - Much cheaper than GPT-4
3. **Cache search results** - Avoid duplicate searches
4. **Set up billing alerts** - Get notified before costs get high
5. **Monitor token usage** - Optimize prompts to reduce costs

---

**Ready to deploy? Make sure you have at least OpenAI, Anthropic, and Google Search APIs configured!** 🎉
