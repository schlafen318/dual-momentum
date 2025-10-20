# Symbol Data Fetching Error Fix

## Issue Summary

Users were experiencing errors when trying to fetch data for major ETF symbols:
- **SPY** (SPDR S&P 500 ETF)
- **QQQ** (Invesco QQQ Trust - Nasdaq-100)
- **IWM** (iShares Russell 2000 ETF)
- **DIA** (SPDR Dow Jones Industrial Average ETF)

Error message:
```
Could not fetch data for: SPY, QQQ, IWM, DIA
These symbols will be excluded from the backtest.
```

## Root Cause

The issue was **Yahoo Finance rate limiting** caused by:

1. **No delays between symbol fetches** - The code was making rapid-fire requests for multiple symbols
2. **Insufficient retry delays** - Only 1 second delay between retries wasn't enough for rate limit errors
3. **No rate limit detection** - The code didn't specifically handle 429 "Too Many Requests" errors

When fetching multiple symbols quickly, Yahoo Finance's API would return:
```
Edge: Too Many Requests
```

## Symbol Compatibility

### Are SPY, QQQ, IWM, DIA universal across data providers?

**YES!** These symbols are universally supported because they are:

- **Major US-listed ETFs** on NYSE Arca and Nasdaq
- **Standardized US ticker symbols** recognized by all financial data providers
- **High-volume, liquid instruments** available on all major data feeds

### Data Provider Support

| Provider | Support | Notes |
|----------|---------|-------|
| **Yahoo Finance** | ✅ YES | Free, no API key required |
| **Alpha Vantage** | ✅ YES | US equities and ETFs fully supported |
| **Twelve Data** | ✅ YES | Complete US market coverage |
| **IEX Cloud** | ✅ YES | US equities supported |
| **Polygon.io** | ✅ YES | US stocks and ETFs |

## Solution Implemented

### 1. Added Request Delays in `yahoo_finance_direct.py`

**Changed:**
- Default retry delay: `1s` → `2s`
- Added new `request_delay` parameter: `0.5s` between symbols
- Enhanced retry logic to detect rate limit errors

```python
# Before
self.retry_delay = self.config.get('retry_delay', 1)

# After
self.retry_delay = self.config.get('retry_delay', 2)
self.request_delay = self.config.get('request_delay', 0.5)
```

### 2. Enhanced Rate Limit Handling

Added detection for rate limit errors and increased backoff:

```python
if 'Too Many Requests' in str(e) or '429' in str(e):
    delay = self.retry_delay * 2  # Double the delay for rate limits
    logger.info(f"Rate limit detected, waiting {delay}s before retry")
```

### 3. Added Delays in `fetch_multiple()` Method

```python
for i, symbol in enumerate(symbols):
    df = self.fetch_data(symbol, start_date, end_date, timeframe)
    
    # Add delay between requests (except after last symbol)
    if i < len(symbols) - 1:
        time.sleep(self.request_delay)
```

### 4. Added Delays in Frontend `fetch_real_data()`

Updated `dual_momentum_system/frontend/pages/strategy_builder.py`:

```python
for i, symbol in enumerate(symbols):
    raw_data = data_source.fetch_data(...)
    
    # Add delay to avoid rate limiting
    if i < len(symbols) - 1:
        time.sleep(0.5)
```

## Testing Results

Tested with all 4 symbols over 1 year of data:

```
Test Results:
✓ SPY: 250 rows fetched
✓ QQQ: 250 rows fetched  
✓ IWM: 250 rows fetched
✓ DIA: 250 rows fetched

Total time: 1.94s (includes 0.5s delays between symbols)
Success rate: 100%
```

## Benefits

1. **Eliminates rate limiting errors** - Proper delays prevent "Too Many Requests"
2. **Maintains responsiveness** - 0.5s delays are barely noticeable to users
3. **Better error handling** - Increased delays for detected rate limit errors
4. **Universal symbol support** - Works with all major US-listed securities
5. **Failover ready** - MultiSourceDataProvider can use Alpha Vantage if Yahoo fails

## Configuration Options

Users can customize rate limit handling:

```python
# Create data source with custom delays
source = YahooFinanceDirectSource({
    'timeout': 10,           # Request timeout
    'max_retries': 3,        # Retry attempts
    'retry_delay': 2,        # Delay between retries
    'request_delay': 0.5     # Delay between different symbols
})
```

## Recommendations

For users experiencing issues:

1. **Use default configuration** - The updated defaults handle rate limits well
2. **Enable Alpha Vantage fallback** - Set `ALPHAVANTAGE_API_KEY` for automatic failover
3. **Reduce symbol count** - If fetching 20+ symbols, consider batching
4. **Check internet connection** - Slow connections may timeout

## Files Modified

1. `dual_momentum_system/src/data_sources/yahoo_finance_direct.py`
   - Added `request_delay` configuration
   - Enhanced rate limit detection in retry logic
   - Added delays in `fetch_multiple()` method

2. `dual_momentum_system/frontend/pages/strategy_builder.py`
   - Added `import time`
   - Added delays in `fetch_real_data()` function

## Summary

The "Could not fetch data" error was caused by Yahoo Finance rate limiting when fetching multiple symbols rapidly. The fix adds small delays (0.5s) between requests, which eliminates the rate limiting while maintaining good performance. 

**SPY, QQQ, IWM, and DIA are universally supported symbols** that work across all major financial data providers including Yahoo Finance and Alpha Vantage.
