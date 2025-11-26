# KEPLER Web Interface Deployment Guide

This guide covers deploying the KEPLER Web Interface with:
- **Frontend**: Vercel
- **Backend API**: Railway

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git repository
- Vercel account (https://vercel.com)
- Railway account (https://railway.app)
- API keys for LLM providers (OpenAI, Anthropic, etc.)

## Backend Deployment (Railway)

### 1. Prepare Your Repository

Ensure your repository has:
- `Dockerfile` (already included)
- `railway.json` (already included)
- `requirements.txt` with all dependencies
- `src/` directory with your API code

### 2. Deploy to Railway

1. Go to https://railway.app and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your KEPLER repository
5. Railway will automatically detect the Dockerfile

### 3. Configure Environment Variables

In Railway project settings, add these environment variables:

```
# Required
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
GOOGLE_API_KEY=your_google_key
COHERE_API_KEY=your_cohere_key

# Application Settings
PORT=8000
PYTHONUNBUFFERED=1
```

### 4. Get Your API URL

After deployment, Railway will provide a URL like:
```
https://your-app.railway.app
```

Save this URL for frontend configuration.

## Frontend Deployment (Vercel)

### 1. Prepare Frontend

Navigate to the frontend directory:
```bash
cd frontend
```

### 2. Configure API URL

Create or update `frontend/.env.production`:
```
VITE_API_URL=https://your-app.railway.app
```

Replace with your actual Railway API URL.

### 3. Deploy to Vercel

#### Option A: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

#### Option B: Vercel Dashboard

1. Go to https://vercel.com and sign in
2. Click "Add New Project"
3. Import your Git repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add environment variable:
   - `VITE_API_URL`: Your Railway API URL
6. Click "Deploy"

### 4. Configure Custom Domain (Optional)

In Vercel project settings:
1. Go to "Domains"
2. Add your custom domain
3. Follow DNS configuration instructions

## Post-Deployment

### 1. Test the Application

1. Visit your Vercel URL
2. Try submitting a test claim
3. Verify all features work:
   - Claim input
   - Image upload
   - Model selection
   - Results display
   - History
   - Export

### 2. Monitor Logs

**Railway (Backend)**:
- View logs in Railway dashboard
- Monitor API errors and performance

**Vercel (Frontend)**:
- View deployment logs in Vercel dashboard
- Check for build errors

### 3. Update CORS Settings

If you encounter CORS errors, update `src/api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "https://your-custom-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy the backend after changes.

## Troubleshooting

### Frontend Issues

**Build Fails**:
- Check Node.js version (should be 18+)
- Verify all dependencies are in `package.json`
- Check build logs for specific errors

**API Connection Fails**:
- Verify `VITE_API_URL` is set correctly
- Check CORS configuration on backend
- Ensure Railway app is running

### Backend Issues

**Deployment Fails**:
- Check Dockerfile syntax
- Verify all Python dependencies are in `requirements.txt`
- Check Railway build logs

**Runtime Errors**:
- Verify all environment variables are set
- Check API key validity
- Review Railway logs for errors

**Out of Memory**:
- Upgrade Railway plan for more resources
- Optimize model loading and caching

## Scaling Considerations

### Frontend (Vercel)
- Vercel automatically scales
- CDN caching for static assets
- Edge network for global performance

### Backend (Railway)
- Start with Hobby plan ($5/month)
- Upgrade to Pro for:
  - More memory
  - Better CPU
  - Higher request limits
- Consider horizontal scaling for high traffic

## Cost Estimates

### Vercel (Frontend)
- **Hobby**: Free (personal projects)
- **Pro**: $20/month (commercial use)

### Railway (Backend)
- **Free Trial**: $5 credit
- **Hobby**: ~$5-10/month (light usage)
- **Pro**: $20+/month (production use)

### LLM API Costs
- Varies by provider and usage
- Monitor usage in provider dashboards
- Set up billing alerts

## Security Best Practices

1. **Environment Variables**: Never commit API keys
2. **CORS**: Restrict to your frontend domain
3. **Rate Limiting**: Implement on backend
4. **HTTPS**: Both platforms provide SSL automatically
5. **API Keys**: Rotate regularly
6. **Monitoring**: Set up error tracking (Sentry, etc.)

## Continuous Deployment

Both platforms support automatic deployments:

**Vercel**:
- Automatically deploys on git push to main branch
- Preview deployments for pull requests

**Railway**:
- Automatically deploys on git push
- Configure branch-specific deployments

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Railway Docs**: https://docs.railway.app
- **KEPLER Issues**: [Your GitHub Issues URL]

## Quick Start Commands

```bash
# Frontend local development
cd frontend
npm install
npm run dev

# Backend local development
pip install -r requirements.txt
uvicorn src.api.app:app --reload

# Deploy frontend
cd frontend
vercel --prod

# Check Railway deployment
railway logs
```

## Environment Variables Reference

### Backend (Railway)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `GOOGLE_API_KEY` | No | Google AI API key |
| `COHERE_API_KEY` | No | Cohere API key |
| `PORT` | No | Port (default: 8000) |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL |

