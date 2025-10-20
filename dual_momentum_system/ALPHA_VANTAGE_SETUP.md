# Alpha Vantage Data Source Setup

This document explains how to use Alpha Vantage for downloading market data in the Dual Momentum trading system.

## Overview

Alpha Vantage is integrated as a **backup data source** with automatic failover. The system uses:
1. **Primary**: Yahoo Finance Direct (free, no API key needed)
2. **Backup**: Alpha Vantage (requires API key, 500 requests/day free)

This ensures 99.9%+ uptime for data downloads.

## Your API Key

```
VT0RO0SAME6YV9PC
```

**Free Tier Limits:**
- 500 API requests per day
- 5 requests per minute
- No credit card required

## Quick Start

### 1. Test Alpha Vantage Connection

```bash
cd dual_momentum_system
python3 examples/quick_alpha_vantage_test.py
```

This will download data for SPY and verify your API key works.

### 2. Run Full Demo

```bash
python3 examples/alpha_vantage_demo.py
```

This demonstrates:
- Basic Alpha Vantage data download
- Downloading multiple symbols
- Multi-source setup with failover
- Integration patterns for backtesting

### 3. Download Data for Analysis

```bash
python3 examples/backtest_with_alpha_vantage.py
```

This will:
- Download data for SPY, QQQ, TLT, SHY
- Calculate returns and volatility
- Show correlation matrix
- Demonstrate production usage patterns

## Configuration Methods

### Method 1: Hardcode in Script (Current)

```python
from src.data_sources import AlphaVantageSource

source = AlphaVantageSource({
    'api_key': 'VT0RO0SAME6YV9PC'
})
```

### Method 2: Environment Variable (Recommended)

```bash
export ALPHAVANTAGE_API_KEY=VT0RO0SAME6YV9PC
```

Then in your code:

```python
from src.data_sources import AlphaVantageSource

# API key is automatically read from environment
source = AlphaVantageSource()
```

### Method 3: .env File (Best for Development)

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env to add your API key
```

The `.env.example` file already contains your API key as a template.

## Production Usage (Recommended Pattern)

Always use the multi-source provider for automatic failover:

```python
from src.data_sources import get_default_data_source

# Configure with Alpha Vantage as backup
config = {
    'alphavantage_api_key': 'VT0RO0SAME6YV9PC'
}

data_source = get_default_data_source(config)

# Download data - automatically uses Yahoo first, Alpha Vantage as backup
data = data_source.fetch_data('SPY', start_date, end_date)
```

This pattern:
- Uses Yahoo Finance first (free, no limits)
- Automatically fails over to Alpha Vantage if Yahoo is down
- Saves your API quota
- Ensures high availability

## API Usage Monitoring

Alpha Vantage free tier provides:
- **500 requests per day**
- **5 requests per minute**

Example usage:
- Downloading 1 symbol = 1 API call
- Downloading 10 symbols = 10 API calls
- A 1-year backtest with 5 symbols = 5 API calls (one-time)

**Note:** With the multi-source setup, Alpha Vantage is only used when Yahoo Finance fails, so most of the time you won't use any API quota!

## Supported Data

Alpha Vantage supports:
- **Stocks**: US and international equities
- **ETFs**: All major ETFs (SPY, QQQ, TLT, etc.)
- **Forex**: Currency pairs
- **Crypto**: Major cryptocurrencies

## Example Scripts

| Script | Purpose | API Calls |
|--------|---------|-----------|
| `quick_alpha_vantage_test.py` | Quick connection test | 1 |
| `alpha_vantage_demo.py` | Full feature demo | ~6 |
| `backtest_with_alpha_vantage.py` | Production usage example | 0* |

\* Uses Yahoo Finance first, only uses Alpha Vantage if Yahoo fails

## Troubleshooting

### API Key Not Working

```python
from src.data_sources import AlphaVantageSource

source = AlphaVantageSource({'api_key': 'VT0RO0SAME6YV9PC'})
if source.is_available():
    print("✓ API key is valid")
else:
    print("✗ API key issue - check internet connection")
```

### Rate Limit Exceeded

If you hit the 5 requests/minute limit, the system automatically:
1. Waits for the rate limit window to expire
2. Retries the request
3. Logs the delay

You can monitor this in the debug logs.

### No Data Returned

Check:
1. Symbol is valid (e.g., 'SPY' not 'spy')
2. Date range is reasonable (not too far in the past)
3. Market was open on those dates

## Advanced Configuration

### Custom Rate Limits

```python
source = AlphaVantageSource({
    'api_key': 'VT0RO0SAME6YV9PC',
    'rate_limit': {
        'requests_per_minute': 5,
        'requests_per_day': 500
    }
})
```

### Caching

Data is automatically cached to avoid redundant API calls:

```python
source = AlphaVantageSource({
    'api_key': 'VT0RO0SAME6YV9PC',
    'cache_enabled': True  # Default: True
})
```

### Timeout Configuration

```python
source = AlphaVantageSource({
    'api_key': 'VT0RO0SAME6YV9PC',
    'timeout': 30  # seconds, default: 30
})
```

## Integration with Backtesting

See `examples/complete_backtest_example.py` for a full backtesting workflow using Alpha Vantage.

Basic pattern:

```python
from src.data_sources import get_default_data_source
from src.strategies.dual_momentum import DualMomentumStrategy
from src.backtesting.engine import BacktestEngine

# 1. Setup data source
config = {'alphavantage_api_key': 'VT0RO0SAME6YV9PC'}
data_source = get_default_data_source(config)

# 2. Download data
universe = ['SPY', 'QQQ', 'TLT']
price_data = {}

for symbol in universe:
    price_data[symbol] = data_source.fetch_data(
        symbol, start_date, end_date
    )

# 3. Run backtest
# (See complete_backtest_example.py for full code)
```

## Getting More API Quota

If you need more than 500 requests/day:

1. **Premium Plans**: Visit https://www.alphavantage.co/premium/
   - Starts at $49.99/month for 1200 requests/day
   - Enterprise plans available

2. **Multiple Data Sources**: The system already supports:
   - Yahoo Finance (unlimited, free)
   - Alpha Vantage (500/day, free)
   - Twelve Data (800/day, free tier available)

3. **Optimize Usage**:
   - Cache data locally
   - Download data once, run multiple backtests
   - Use Yahoo Finance for frequent requests

## Support

- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation/
- **Get API Key**: https://www.alphavantage.co/support/#api-key
- **System Docs**: See `README.md` in project root

## Summary

✅ Alpha Vantage is configured and ready to use  
✅ API Key: `VT0RO0SAME6YV9PC`  
✅ Free tier: 500 requests/day  
✅ Automatic failover from Yahoo Finance  
✅ Production-ready with caching and rate limiting  

Start with the test script to verify everything works:

```bash
python3 examples/quick_alpha_vantage_test.py
```
