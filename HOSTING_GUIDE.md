# Quick UI Hosting Guide

This is a simplified guide to get your KEPLER UI hosted and running quickly.

## Option 1: Vercel (Recommended - Easiest)

Vercel is the easiest way to host your React/Vite frontend with zero configuration.

### Step-by-Step:

1. **Sign up for Vercel**
   - Go to https://vercel.com
   - Sign up with GitHub (recommended)

2. **Import Your Project**
   - Click "Add New Project"
   - Select your KEPLER repository
   - Vercel will auto-detect it's a Vite project

3. **Configure Build Settings**
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

4. **Add Environment Variable**
   - In project settings, add:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```
   - Replace with your actual backend URL

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your UI will be live at `https://your-project.vercel.app`

### Automatic Updates
- Every time you push to GitHub, Vercel automatically redeploys
- Pull requests get preview deployments

### Custom Domain (Optional)
- Go to Project Settings → Domains
- Add your domain (e.g., kepler.yourdomain.com)
- Follow DNS instructions

---

## Option 2: Netlify (Alternative)

Similar to Vercel, great for static sites.

### Step-by-Step:

1. **Sign up for Netlify**
   - Go to https://netlify.com
   - Sign up with GitHub

2. **Import Project**
   - Click "Add new site" → "Import an existing project"
   - Choose your repository

3. **Configure Build**
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```

4. **Environment Variables**
   - Go to Site settings → Environment variables
   - Add: `VITE_API_URL=https://your-backend-url.railway.app`

5. **Deploy**
   - Click "Deploy site"
   - Your UI will be live at `https://your-site.netlify.app`

---

## Option 3: GitHub Pages (Free, Static Only)

Good for demos, but requires manual deployment.

### Step-by-Step:

1. **Update vite.config.ts**
   ```typescript
   export default defineConfig({
     base: '/your-repo-name/',
     // ... rest of config
   })
   ```

2. **Build for Production**
   ```bash
   cd frontend
   npm run build
   ```

3. **Deploy to GitHub Pages**
   ```bash
   # Install gh-pages
   npm install -D gh-pages

   # Add to package.json scripts:
   "deploy": "gh-pages -d dist"

   # Deploy
   npm run deploy
   ```

4. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: gh-pages branch
   - Your site will be at `https://username.github.io/repo-name/`

---

## Option 4: Self-Hosted (VPS/Cloud)

For full control, host on your own server.

### Requirements:
- A server (DigitalOcean, AWS, Azure, etc.)
- Node.js installed
- Nginx or Apache

### Step-by-Step:

1. **Build the Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Upload to Server**
   ```bash
   # Using SCP
   scp -r dist/* user@your-server:/var/www/kepler/

   # Or use FTP/SFTP client
   ```

3. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /var/www/kepler;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       # Proxy API requests to backend
       location /api {
           proxy_pass https://your-backend-url.railway.app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Restart Nginx**
   ```bash
   sudo systemctl restart nginx
   ```

5. **Setup SSL (Optional but Recommended)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## Quick Comparison

| Platform | Difficulty | Cost | Auto-Deploy | Custom Domain | SSL |
|----------|-----------|------|-------------|---------------|-----|
| **Vercel** | ⭐ Easy | Free/Paid | ✅ Yes | ✅ Yes | ✅ Auto |
| **Netlify** | ⭐ Easy | Free/Paid | ✅ Yes | ✅ Yes | ✅ Auto |
| **GitHub Pages** | ⭐⭐ Medium | Free | ❌ Manual | ✅ Yes | ✅ Auto |
| **Self-Hosted** | ⭐⭐⭐ Hard | Variable | ❌ Manual | ✅ Yes | ⚙️ Manual |

---

## Recommended Setup

For most users, I recommend:

1. **Frontend**: Vercel (easiest, free tier is generous)
2. **Backend**: Railway (already configured in your project)

This gives you:
- ✅ Automatic deployments
- ✅ Free SSL certificates
- ✅ Global CDN
- ✅ Easy scaling
- ✅ Great developer experience

---

## Testing Your Deployment

After deployment, test these features:

1. **Basic Functionality**
   - [ ] Page loads without errors
   - [ ] Can enter a claim
   - [ ] Can upload an image
   - [ ] Can select models

2. **API Connection**
   - [ ] Submit a test claim
   - [ ] Verify results display
   - [ ] Check browser console for errors

3. **Responsive Design**
   - [ ] Test on mobile device
   - [ ] Test on tablet
   - [ ] Test on desktop

4. **Features**
   - [ ] History saves and loads
   - [ ] Export works (JSON/PDF)
   - [ ] All result sections display

---

## Common Issues & Solutions

### Issue: "Failed to fetch" or CORS errors

**Solution**: Update backend CORS settings in `src/api/app.py`:
```python
allow_origins=[
    "https://your-vercel-app.vercel.app",
    "http://localhost:5173",  # for local dev
]
```

### Issue: Environment variables not working

**Solution**: 
- Vercel/Netlify: Redeploy after adding env vars
- Vite requires `VITE_` prefix for env vars
- Check `.env.production` file exists

### Issue: 404 on page refresh

**Solution**: Configure rewrites in `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Issue: Build fails

**Solution**:
- Check Node.js version (needs 18+)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check build logs for specific errors

---

## Next Steps

1. ✅ Deploy frontend to Vercel
2. ✅ Deploy backend to Railway (if not done)
3. ✅ Configure environment variables
4. ✅ Test the application
5. ✅ Set up custom domain (optional)
6. ✅ Monitor logs and errors
7. ✅ Share with users!

---

## Need Help?

- **Vercel Docs**: https://vercel.com/docs
- **Netlify Docs**: https://docs.netlify.com
- **Vite Docs**: https://vitejs.dev/guide/static-deploy.html
- **Your DEPLOYMENT.md**: Full deployment guide with more details

---

## Quick Commands Reference

```bash
# Local development
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Deploy to Vercel (with CLI)
npm install -g vercel
vercel --prod

# Check build output
ls -la dist/
```

---

## Cost Breakdown

### Free Tier (Perfect for Getting Started)
- **Vercel**: 100GB bandwidth/month, unlimited sites
- **Netlify**: 100GB bandwidth/month, 300 build minutes
- **GitHub Pages**: Unlimited for public repos

### Paid Plans (For Production)
- **Vercel Pro**: $20/month (commercial use, better support)
- **Netlify Pro**: $19/month (more build minutes, analytics)

**Recommendation**: Start with free tier, upgrade when needed.

---

## Success Checklist

Before going live:

- [ ] Frontend deployed and accessible
- [ ] Backend API connected and working
- [ ] Environment variables configured
- [ ] SSL certificate active (https://)
- [ ] Tested on multiple devices
- [ ] Error monitoring set up (optional)
- [ ] Custom domain configured (optional)
- [ ] Shared with team/users

---

**You're ready to host! Start with Vercel for the easiest experience.** 🚀
