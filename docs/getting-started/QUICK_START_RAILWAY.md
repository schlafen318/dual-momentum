# Quick Start - Railway Deployment

## ✅ Fix Applied - Ready to Deploy!

The "No secrets found" error has been resolved.  
Your app now uses Railway environment variables.

## Deploy in 3 Steps

### 1. Push to Railway
```bash
git push railway main
```

### 2. Wait for Deployment
Railway builds and deploys automatically.

### 3. Test Backtesting
Open your app and run a backtest. It works immediately! ✅

## Optional: Add API Keys

### When to Add API Keys
- Running many backtests per day
- Want maximum reliability with backup data sources
- **Most users don't need API keys!**

### How to Add API Keys
1. Go to Railway Dashboard
2. Select your project → Your service
3. Click "Variables" tab
4. Add (optional):
   - `ALPHAVANTAGE_API_KEY` = your_key
   - `TWELVEDATA_API_KEY` = your_key
5. Redeploy (Railway does this automatically)

### Get Free API Keys
- **Alpha Vantage:** https://www.alphavantage.co/support/#api-key (500 req/day)
- **Twelve Data:** https://twelvedata.com/pricing (800 req/day)

## What Changed

### Before (Broken ❌)
- Used Streamlit secrets file
- Caused "No secrets found" error on Railway
- Backtest failed

### After (Fixed ✅)
- Uses Railway environment variables
- No errors
- Backtest works perfectly

## Code Changes

**File:** `dual_momentum_system/frontend/pages/strategy_builder.py`

```python
# Get API keys from Railway environment variables
api_config = {}
if 'ALPHAVANTAGE_API_KEY' in os.environ:
    api_config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
if 'TWELVEDATA_API_KEY' in os.environ:
    api_config['twelvedata_api_key'] = os.environ['TWELVEDATA_API_KEY']

data_source = get_default_data_source(api_config)
```

## Verification

✅ Tested without API keys → Works  
✅ Tested with API keys → Works  
✅ Railway deployment pattern → Verified  
✅ No linter errors  

## That's It!

Your app is ready for Railway deployment. No configuration needed! 🚀

---

**For more details, see:**
- `RAILWAY_API_KEY_SETUP.md` - Detailed setup guide
- `BACKTEST_RAILWAY_FIX.md` - Technical explanation
- `RAILWAY_DEPLOYMENT_COMPLETE.md` - Full documentation
