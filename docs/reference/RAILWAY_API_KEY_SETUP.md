# Railway API Key Setup Guide

## Overview

This application reads API keys from **Railway Environment Variables** automatically.
No code changes or secrets files needed - just set variables in Railway Dashboard!

## Quick Setup

### Step 1: Go to Railway Dashboard
1. Open your Railway project
2. Click on your service/app
3. Navigate to the **"Variables"** tab

### Step 2: Add API Keys (Optional)
Click **"New Variable"** and add:

| Variable Name | Value | Required? |
|--------------|-------|-----------|
| `ALPHAVANTAGE_API_KEY` | your_alpha_vantage_key | Optional |
| `TWELVEDATA_API_KEY` | your_twelve_data_key | Optional |

### Step 3: Deploy
Railway automatically injects these as environment variables. Your app will detect and use them!

## Important Notes

### ✅ API Keys Are Optional
- The system works perfectly with **Yahoo Finance only** (no API keys needed)
- API keys provide **backup data sources** if Yahoo Finance is unavailable
- **Recommended:** Start without API keys, add them only if needed

### ✅ How It Works
1. You set variables in Railway Dashboard
2. Railway injects them as `os.environ` variables
3. App automatically reads from `os.environ['ALPHAVANTAGE_API_KEY']`
4. Data sources are configured with automatic failover

### ✅ No Secrets File Needed
- Don't edit `.streamlit/secrets.toml` on Railway
- Railway uses environment variables, not secrets files
- The app code reads directly from `os.environ`

## Getting Free API Keys

### Alpha Vantage (Optional)
- **URL:** https://www.alphavantage.co/support/#api-key
- **Free Tier:** 500 requests/day, 5 requests/minute
- **No credit card required**
- **Setup:** Enter email → Get instant API key

### Twelve Data (Optional)
- **URL:** https://twelvedata.com/pricing
- **Free Tier:** 800 requests/day, 8 requests/minute
- **No credit card required**
- **Setup:** Sign up → Dashboard → Copy API key

## Railway Variable Configuration

### Example Setup in Railway Dashboard

```
Variable Name: ALPHAVANTAGE_API_KEY
Value: ABC123XYZ789 (your actual key)

Variable Name: TWELVEDATA_API_KEY
Value: DEF456UVW012 (your actual key)
```

### Variables Tab Screenshot Guide
```
Railway Dashboard
├── Your Project
    ├── Your Service
        ├── Settings
        ├── Deployments
        ├── Variables ← Click here
            ├── New Variable (button)
            ├── Existing Variables:
                ├── ALPHAVANTAGE_API_KEY = ••••••••
                └── TWELVEDATA_API_KEY = ••••••••
```

## Testing Your Setup

### Verify Variables Are Set
In Railway Logs, you should see:
```
[DATA SOURCE] Initialized with 3 sources: 
  ['YahooFinanceDirectSource', 'AlphaVantageSource', 'TwelveDataSource']
```

### Without API Keys (Default)
```
[DATA SOURCE] Initialized with 2 sources:
  ['YahooFinanceDirectSource', 'YahooFinanceSource']
```

Both configurations work perfectly!

## Code Implementation

The app reads variables like this:

```python
import os
from src.data_sources import get_default_data_source

# Get API keys from Railway environment variables
api_config = {}

if 'ALPHAVANTAGE_API_KEY' in os.environ:
    api_config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
if 'TWELVEDATA_API_KEY' in os.environ:
    api_config['twelvedata_api_key'] = os.environ['TWELVEDATA_API_KEY']

# Create data source (works with or without API keys)
data_source = get_default_data_source(api_config)
```

## Troubleshooting

### "No secrets found" Error
✅ **FIXED** - The app no longer uses Streamlit secrets on Railway
- App reads from Railway environment variables
- No secrets.toml file needed
- Error should not occur anymore

### API Keys Not Working
1. Check variable names are exact: `ALPHAVANTAGE_API_KEY` (case-sensitive)
2. Verify keys are valid (test at provider's website)
3. Check Railway logs for initialization messages
4. Redeploy after adding variables

### Backtest Still Using Only Yahoo
This is normal if:
- No API keys are set (expected behavior)
- API keys are invalid (falls back to Yahoo)
- Rate limit exceeded on API sources (automatic failover)

All scenarios work correctly!

## Deployment Checklist

- [ ] Deploy app to Railway
- [ ] Test backtest without API keys (should work with Yahoo)
- [ ] (Optional) Get free API keys from Alpha Vantage / Twelve Data
- [ ] (Optional) Add API keys to Railway Variables tab
- [ ] (Optional) Redeploy and verify backup sources are active
- [ ] Run backtest - should work with or without API keys!

## Data Source Priority

With API keys configured:
1. **Yahoo Finance Direct** (primary, always tried first)
2. **Alpha Vantage** (backup #1, if key provided)
3. **Twelve Data** (backup #2, if key provided)
4. **Yahoo Finance** (backup #3, alternative Yahoo implementation)

Without API keys:
1. **Yahoo Finance Direct** (primary)
2. **Yahoo Finance** (backup, alternative implementation)

Both configurations provide robust data fetching!

## Summary

✅ **Simple Setup:** Just add variables in Railway Dashboard  
✅ **No Code Changes:** App automatically detects environment variables  
✅ **Optional Keys:** Works perfectly without any API keys  
✅ **Automatic Failover:** Backup sources activate when needed  
✅ **No Secrets File:** Railway uses environment variables, not secrets.toml  

**You're ready to deploy!** 🚀
