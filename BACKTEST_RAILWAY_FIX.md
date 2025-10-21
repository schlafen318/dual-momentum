# Backtest Railway Fix - Complete Solution

## Problem Resolved ✅

**Original Error:**
```
Backtest failed: No secrets found. Valid paths for a secrets.toml file or secret directories are:
/root/.streamlit/secrets.toml, /app/.streamlit/secrets.toml, /app/dual_momentum_system/frontend/.streamlit/secrets.toml
```

## Root Cause

The application was trying to access Streamlit secrets (`st.secrets`), which:
1. Caused errors on Railway where secrets.toml doesn't exist
2. Is not the correct method for Railway deployments
3. Railway uses **environment variables**, not secrets files

## Solution Implemented

### 1. Removed Streamlit Secrets Access
**File:** `dual_momentum_system/frontend/pages/strategy_builder.py`

**Before:**
```python
# Get API keys from environment or Streamlit secrets if available
api_config = {}

# Try to get from Streamlit secrets (safe handling)
try:
    if hasattr(st, 'secrets') and st.secrets:
        if 'ALPHAVANTAGE_API_KEY' in st.secrets:
            api_config['alphavantage_api_key'] = st.secrets['ALPHAVANTAGE_API_KEY']
        # ... more st.secrets access
except (FileNotFoundError, RuntimeError):
    pass

# Also check environment variables
if 'ALPHAVANTAGE_API_KEY' in os.environ:
    api_config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
```

**After:**
```python
# Get API keys from Railway environment variables
# Railway automatically injects variables set in the dashboard as environment variables
api_config = {}

# Check Railway environment variables (primary method for cloud deployment)
if 'ALPHAVANTAGE_API_KEY' in os.environ:
    api_config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
if 'TWELVEDATA_API_KEY' in os.environ:
    api_config['twelvedata_api_key'] = os.environ['TWELVEDATA_API_KEY']
```

### 2. Updated secrets.toml Documentation
**File:** `dual_momentum_system/.streamlit/secrets.toml`

Updated to clearly state:
- This file is NOT used on Railway
- Railway uses environment variables
- Instructions for Railway Dashboard setup

### 3. Comprehensive Testing

✅ **Tested scenarios:**
- Without any API keys → Works (Yahoo Finance)
- With Railway environment variables → Works (All sources)
- Railway deployment pattern → Verified
- Backtest execution → Successful

## Railway Setup Instructions

### Step 1: Access Railway Variables
1. Go to Railway Dashboard
2. Select your project
3. Click on your service
4. Navigate to **"Variables"** tab

### Step 2: Add API Keys (Optional)
Click "New Variable" and add:

```
Variable Name: ALPHAVANTAGE_API_KEY
Value: your_alphavantage_key_here

Variable Name: TWELVEDATA_API_KEY  
Value: your_twelvedata_key_here
```

### Step 3: That's It!
Railway automatically injects these as environment variables.
The app detects and uses them automatically.

## Important Notes

### ✅ API Keys Are Optional
- App works perfectly without any API keys (uses Yahoo Finance)
- API keys provide backup data sources for reliability
- **Start without keys, add only if needed**

### ✅ Railway Auto-Injection
- Variables set in Railway Dashboard → Become `os.environ` variables
- No manual configuration in code needed
- App automatically detects and uses them

### ✅ No Secrets File Needed
- Don't modify `.streamlit/secrets.toml` on Railway
- Railway uses environment variables
- Secrets file only exists to prevent local errors

## Getting Free API Keys (Optional)

### Alpha Vantage
- URL: https://www.alphavantage.co/support/#api-key
- Free: 500 requests/day, 5 requests/minute
- No credit card required

### Twelve Data
- URL: https://twelvedata.com/pricing
- Free: 800 requests/day, 8 requests/minute
- No credit card required

## Verification

### Check Railway Logs
With API keys:
```
[DATA SOURCE] Initialized with 3 sources:
  ['YahooFinanceDirectSource', 'AlphaVantageSource', 'TwelveDataSource']
```

Without API keys (default):
```
[DATA SOURCE] Initialized with 2 sources:
  ['YahooFinanceDirectSource', 'YahooFinanceSource']
```

Both work perfectly!

## Files Modified

1. ✅ `dual_momentum_system/frontend/pages/strategy_builder.py`
   - Removed `st.secrets` access
   - Uses only `os.environ` (Railway variables)

2. ✅ `dual_momentum_system/.streamlit/secrets.toml`
   - Updated documentation
   - Railway setup instructions

3. ✅ Created comprehensive documentation:
   - `RAILWAY_API_KEY_SETUP.md` - Setup guide
   - `BACKTEST_RAILWAY_FIX.md` - This file

## Data Source Behavior

### With API Keys Set in Railway:
1. Yahoo Finance Direct (primary)
2. Alpha Vantage (backup, if key provided)
3. Twelve Data (backup, if key provided)
4. Yahoo Finance (backup, alternative)

### Without API Keys (Default):
1. Yahoo Finance Direct (primary)
2. Yahoo Finance (backup)

**Both configurations work reliably!**

## Status

✅ **RESOLVED** - Backtest now works on Railway

### What Changed:
- ❌ No more `st.secrets` access (caused errors)
- ✅ Uses Railway environment variables
- ✅ Works with or without API keys
- ✅ Clear documentation for setup

### What To Do:
1. Deploy to Railway (works immediately)
2. Optionally add API keys in Variables tab
3. Run backtests successfully!

## Summary

**The Fix:**
- Removed Streamlit secrets access that caused errors
- App now reads API keys from Railway environment variables
- Works perfectly with or without API keys

**Railway Setup:**
1. Go to Railway Dashboard → Variables
2. Add API keys (optional): `ALPHAVANTAGE_API_KEY`, `TWELVEDATA_API_KEY`
3. Deploy and run backtests!

**Result:**
🚀 Backtesting works on Railway with zero configuration!

---

For detailed setup instructions, see: `RAILWAY_API_KEY_SETUP.md`
