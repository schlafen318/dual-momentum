# Railway Deployment Fix - "start.sh not found" Error

## Problem
Railway was showing error: **"Script start.sh not found"**

## Root Cause
The git repository root is at `/workspace/`, but the application code was in the `/workspace/dual_momentum_system/` subdirectory. Railway looks for configuration files at the **repository root**, not in subdirectories.

## Solution Applied ✅

Created the following files at the **repository root** (`/workspace/`):

### 1. `start.sh` (Railway startup script)
```bash
#!/bin/bash
cd dual_momentum_system
streamlit run frontend/app.py --server.port=$PORT --server.headless=true --server.address=0.0.0.0
```
- Made executable with `chmod +x`
- Navigates to app subdirectory
- Starts Streamlit with Railway's dynamic port

### 2. `Procfile` (Alternative start method)
```
web: streamlit run dual_momentum_system/frontend/app.py --server.port=$PORT --server.headless=true
```
- Railway will use this if start.sh isn't found
- Uses correct path from repo root

### 3. `runtime.txt` (Python version)
```
python-3.11.0
```
- Tells Railway which Python version to use

### 4. `requirements.txt` (Dependencies)
- Copied from `dual_momentum_system/requirements.txt`
- All dependencies at repo root for Railway to find

### 5. `railway.json` (Railway configuration)
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run dual_momentum_system/frontend/app.py --server.port=$PORT --server.headless=true --server.address=0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```
- Explicit start command configuration
- Restart policy for resilience

---

## Files Now in Repository

### Repository Root (`/workspace/`)
```
/workspace/
├── start.sh ✅ NEW - Railway startup script
├── Procfile ✅ NEW - Process file
├── runtime.txt ✅ NEW - Python version
├── requirements.txt ✅ NEW - Dependencies
├── railway.json ✅ NEW - Railway config
└── dual_momentum_system/
    ├── frontend/
    │   └── app.py
    ├── Procfile (old, kept for reference)
    ├── runtime.txt (old, kept for reference)
    └── requirements.txt (old, kept for reference)
```

---

## What Railway Will Do Now

1. **Detect Python project** - Via `runtime.txt` and `requirements.txt`
2. **Install dependencies** - Using `pip install -r requirements.txt`
3. **Start application** - Using one of:
   - `start.sh` (primary)
   - `railway.json` startCommand (fallback)
   - `Procfile` (secondary fallback)

---

## Deploy Now

```bash
# 1. Commit the new files
git add start.sh Procfile runtime.txt requirements.txt railway.json RAILWAY_FIX.md
git commit -m "Fix Railway deployment - add root config files"

# 2. Push to GitHub
git push origin main

# 3. Railway will auto-deploy
# - Check Railway dashboard for build logs
# - App will be live in ~5-10 minutes
```

---

## Verification

After deployment, verify:
- ✅ Build completes without "start.sh not found" error
- ✅ App starts on Railway's dynamic port
- ✅ Dashboard loads at your Railway URL
- ✅ All pages accessible

---

## Troubleshooting

### If build still fails:

1. **Check Railway Logs**
   - Look for "start.sh not found" (should be gone)
   - Look for dependency installation errors
   - Look for port binding issues

2. **Verify File Permissions**
   ```bash
   chmod +x start.sh
   git add start.sh
   git commit -m "Make start.sh executable"
   git push
   ```

3. **Check Railway Settings**
   - Go to Railway dashboard
   - Settings → Root Directory: Should be `/` (default)
   - Settings → Build Command: Should auto-detect
   - Settings → Start Command: Should use start.sh or railway.json

### If app starts but doesn't load:

1. **Check PORT binding**
   - Verify `$PORT` is used in start command
   - Verify `--server.address=0.0.0.0` is included

2. **Check Environment Variables**
   - Add optional: `ALPHAVANTAGE_API_KEY`, `TWELVEDATA_API_KEY`

3. **Check Memory Usage**
   - Hobby plan: 512MB (may be tight)
   - Upgrade to Developer if needed

---

## Status: ✅ FIXED

The "start.sh not found" error should now be resolved. Railway will find all necessary configuration files at the repository root.

---

**Created**: 2025-10-21
**Issue**: Script start.sh not found
**Resolution**: Added start.sh, Procfile, runtime.txt, requirements.txt, railway.json to repository root
**Status**: Ready to deploy
