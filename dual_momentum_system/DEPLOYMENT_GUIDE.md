# Deployment Guide

## 🚫 Current Issue: Vercel 404 Error

You're getting a 404 error because:
1. This is a **Streamlit** Python application
2. Vercel is designed for static sites and serverless functions (Next.js, React)
3. No Vercel configuration exists for this app

## ✅ Solution: Choose the Right Platform

### **Option 1: Streamlit Cloud (Recommended for Streamlit)**

**Best for**: Your current Streamlit dashboard

**Steps:**

1. **Push to GitHub**
   ```bash
   cd /workspace/dual_momentum_system
   git init
   git add .
   git commit -m "Add Streamlit dashboard"
   git remote add origin https://github.com/yourusername/dual-momentum.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `frontend/app.py`
   - Click "Deploy"

3. **Requirements**
   - Streamlit Cloud will automatically use `requirements.txt`
   - Your app will be live at: `https://your-app-name.streamlit.app`

**Pros:**
- ✅ Free tier available
- ✅ No configuration needed
- ✅ Automatic deployments on push
- ✅ Native Streamlit support

---

### **Option 2: Railway (Easy Python Deployment)**

**Best for**: Quick deployment with more control

**Steps:**

1. **Create `Procfile`**
   ```
   web: streamlit run frontend/app.py --server.port=$PORT --server.headless=true
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Connect GitHub repository
   - Railway auto-detects Python
   - Deploys automatically

**Pros:**
- ✅ Free tier: $5 credit/month
- ✅ Easy setup
- ✅ Supports any Python app

---

### **Option 3: Heroku (Traditional)**

**Best for**: Traditional PaaS deployment

**Steps:**

1. **Create required files** (see below)
2. **Deploy**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

**Required Files:**
- `Procfile` (created below)
- `requirements.txt` (already exists)
- `runtime.txt` (created below)

---

### **Option 4: Vercel with API Routes (Requires Rewrite)**

**Best for**: If you must use Vercel

⚠️ **Important**: You'd need to rebuild the frontend as:
- Next.js/React frontend
- Python serverless API functions in `/api` directory

This requires significant restructuring. Not recommended unless you specifically need Vercel.

---

## 📦 Required Files for Deployment

### For Railway/Heroku: Create `Procfile`

```
web: streamlit run frontend/app.py --server.port=$PORT --server.headless=true
```

### For Heroku: Create `runtime.txt`

```
python-3.11.0
```

### For All: Update `requirements.txt`

Make sure all dependencies are listed:
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
yfinance>=0.2.28
vectorbt>=0.26.0
scipy>=1.10.0
loguru>=0.7.0
```

---

## 🚀 Quick Start: Deploy to Streamlit Cloud

**Fastest solution for your Streamlit app:**

1. **Push code to GitHub**
2. **Go to share.streamlit.io**
3. **Connect repository**
4. **Set main file**: `frontend/app.py`
5. **Deploy** (takes ~2 minutes)

Your app will be live at: `https://your-app-name.streamlit.app`

---

## 🔧 Alternative: If You Want to Stay with Vercel

If you really want to use Vercel, you have two options:

### A. Create a Next.js Frontend + Python API

**Structure:**
```
project/
├── frontend/           # Next.js/React app
│   ├── pages/
│   ├── components/
│   └── package.json
├── api/               # Python serverless functions
│   └── backtest.py
└── vercel.json
```

### B. Use Vercel for Static Export + External API

1. Build a React/Next.js dashboard
2. Deploy that to Vercel
3. Host Python backend elsewhere (Railway, Heroku)
4. Connect via API calls

---

## 📊 Platform Comparison

| Platform | Best For | Free Tier | Setup Difficulty |
|----------|----------|-----------|------------------|
| **Streamlit Cloud** | Streamlit apps | ✅ Yes | ⭐ Easy |
| **Railway** | Any Python app | ✅ $5/month | ⭐⭐ Easy |
| **Heroku** | Traditional PaaS | ⚠️ Limited | ⭐⭐ Medium |
| **Vercel** | Static/Serverless | ✅ Yes | ⭐⭐⭐⭐ Hard (needs rewrite) |

---

## 🎯 Recommended Solution

**For your Streamlit dashboard: Use Streamlit Cloud**

It's:
- ✅ Free
- ✅ Zero configuration
- ✅ Works out of the box
- ✅ Perfect for Streamlit apps

---

## ❓ Need Help?

**Error you're seeing**: `404: NOT_FOUND`

**Cause**: Vercel can't find an entry point because there's no compatible app structure

**Quick Fix**: Deploy to Streamlit Cloud instead (5 minutes)

---

## 📝 Next Steps

1. ✅ Choose deployment platform (recommend: Streamlit Cloud)
2. ✅ Follow steps above
3. ✅ Push to GitHub if needed
4. ✅ Deploy
5. ✅ Share your live dashboard!

---

**Questions?** Check platform docs:
- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- Railway: https://docs.railway.app
- Heroku: https://devcenter.heroku.com
