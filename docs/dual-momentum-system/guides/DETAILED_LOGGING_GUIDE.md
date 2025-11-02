# Detailed Logging for Data Download Diagnostics

## Overview

Comprehensive logging has been added throughout the data download system to help diagnose and troubleshoot download failures. The logging provides detailed information at every stage of the data fetching process.

## What Was Added

### 1. Yahoo Finance Direct Source (`yahoo_finance_direct.py`)

#### Enhanced Logging Features:
- **Fetch lifecycle tracking**: Start and completion times for each fetch
- **Cache hit/miss logging**: Know when data comes from cache vs API
- **HTTP request details**: URL, parameters, timeout settings
- **HTTP response details**: Status code, response size, headers, timing
- **Error categorization**: Separate logging for timeouts, HTTP errors, connection errors
- **Rate limit detection**: Specific handling and logging for 429 errors
- **Data validation**: Row counts, null value detection, date ranges
- **Batch operation tracking**: Progress through multiple symbols with statistics

#### Example Log Output:
```
[FETCH START] Symbol: SPY, Date Range: 2024-09-20 to 2024-10-20, Timeframe: 1d
[CACHE MISS] SPY: No cached data found, fetching from API
[API REQUEST] Initiating Yahoo Finance request for SPY
[REQUEST DETAILS] URL: https://query1.finance.yahoo.com/v8/finance/chart/SPY
[REQUEST DETAILS] Params: {'period1': 1726790400, 'period2': 1729468800, ...}
[HTTP REQUEST] Attempt 1/3: GET https://query1.finance.yahoo.com/v8/finance/chart/SPY
[HTTP RESPONSE] Status: 200, Time: 0.45s, Size: 51234 bytes
[API SUCCESS] Received response for SPY in 0.45s
[DATA VALIDATION] SPY: Shape=(21, 5), Columns=['open', 'high', 'low', 'close', 'volume']
[DATA VALIDATION] SPY: Date range=2024-09-20 to 2024-10-20
[FETCH SUCCESS] SPY: 21 rows fetched successfully (total: 0.52s, parse: 0.03s)
```

### 2. Multi-Source Provider (`multi_source.py`)

#### Enhanced Logging Features:
- **Failover tracking**: Which source is being tried and why
- **Attempt details**: Duration and outcome of each source attempt
- **Error categorization**: Validation errors, connection errors, unexpected errors
- **Success tracking**: Which source succeeded and on which attempt
- **Failure summary**: Detailed breakdown when all sources fail

#### Example Log Output:
```
[MULTI-SOURCE] Fetching SPY from 2 sources with failover
[MULTI-SOURCE CACHE MISS] SPY: No cached data, trying sources
[FAILOVER ATTEMPT 1/2] Trying YahooFinanceDirectSource for SPY
[FAILOVER SUCCESS] ✓ SPY: Fetched 21 rows from YahooFinanceDirectSource (source: 0.52s, total: 0.52s)
```

Or when failing over:
```
[FAILOVER ATTEMPT 1/2] Trying YahooFinanceDirectSource for AAPL
[FAILOVER CONNECTION ERROR] YahooFinanceDirectSource: HTTP 429: Too Many Requests (attempt took 0.34s)
[FAILOVER ATTEMPT 2/2] Trying AlphaVantageSource for AAPL
[FAILOVER SUCCESS] ✓ AAPL: Fetched 21 rows from AlphaVantageSource (source: 1.23s, total: 1.57s)
[FAILOVER SUMMARY] Succeeded on attempt 2/2 after trying: YahooFinanceDirectSource, AlphaVantageSource
```

### 3. Base Data Source (`base_data_source.py`)

#### Enhanced Logging Features:
- **Cache operations**: Detailed logging of cache hits, misses, and additions
- **Cache statistics**: Memory usage, total cached items
- **Batch operation defaults**: Logging for the default fetch_multiple implementation

#### Example Log Output:
```
[CACHE HIT] SPY: Found in cache (key: SPY_2024-09-20_2024-10-20_1d, rows: 21)
[CACHE ADD] AAPL: Cached 21 rows (~15.3 KB, key: AAPL_2024-09-20_2024-10-20_1d)
[CACHE STATS] Total cached items: 3
[CACHE CLEAR] Cleared 5 cached items from YahooFinanceDirectSource
```

### 4. Frontend (`strategy_builder.py`)

#### Enhanced Logging Features:
- **Batch progress tracking**: Real-time progress through symbol list
- **Timing statistics**: Average, min, max fetch times
- **Error categorization**: Connection errors, validation errors, unexpected errors
- **Success rate reporting**: Percentage of successful fetches

#### Example Log Output:
```
[FRONTEND FETCH] Starting data fetch for 4 symbols
[FRONTEND FETCH] Symbols: SPY, QQQ, IWM, DIA
[FRONTEND FETCH] Processing symbol 1/4: SPY
[FRONTEND SUCCESS] SPY: Complete in 0.52s (fetch: 0.45s, normalize: 0.04s)
[FRONTEND COMPLETE] Fetched 4/4 symbols (100.0%) in 2.34s
[FRONTEND STATS] Average time per symbol: 0.59s, Min: 0.52s, Max: 0.67s
```

### 5. Alpha Vantage Source (`alpha_vantage.py`)

#### Enhanced Logging Features:
- **API key validation**: Clear error when API key is missing
- **Rate limiting details**: When rate limits are enforced and for how long
- **API error messages**: Capture and log Alpha Vantage-specific errors
- **Response parsing details**: What data was received and how it was processed

## How to Use the Logging

### 1. Running the Test Script

Use the provided test script to see all logging in action:

```bash
cd dual_momentum_system
python test_detailed_logging.py
```

This will:
- Test single symbol fetches
- Test batch fetches
- Test error handling with invalid symbols
- Test cache functionality
- Write detailed logs to `download_test.log`

### 2. Enabling Detailed Logging in Your Application

```python
from loguru import logger
import sys

# Remove default handler and add custom one
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",  # Set to DEBUG to see all details
    colorize=True
)

# Optional: Also log to file
logger.add(
    "data_download.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    level="DEBUG",
    rotation="10 MB"
)
```

### 3. Interpreting Common Log Patterns

#### Pattern 1: Rate Limiting
```
[HTTP RESPONSE] Status: 429, Time: 0.15s, Size: 234 bytes
[RATE LIMIT] Detected 429 error, waiting 4.0s before retry
[HTTP REQUEST] Attempt 2/3: GET ...
```
**Solution**: The system automatically handles this with delays. If persistent, reduce request frequency.

#### Pattern 2: Connection Timeout
```
[HTTP TIMEOUT] Attempt 1/3: Request timed out after 10.0s
[HTTP REQUEST] Attempt 2/3: GET ...
```
**Solution**: Check internet connection or increase timeout in configuration.

#### Pattern 3: Invalid Symbol
```
[PARSE WARNING] Empty dataframe after parsing INVALID_SYM
[PARSE WARNING] Response data: {"chart":{"result":null,"error":{"code":"Not Found"...
```
**Solution**: Verify symbol is correct and exists on the data provider.

#### Pattern 4: Empty Data Range
```
[DATA VALIDATION] XYZ: Shape=(0, 5), Columns=['open', 'high', 'low', 'close', 'volume']
[PARSE WARNING] Empty dataframe after parsing XYZ
```
**Solution**: Symbol may not have data in the requested date range, or may be delisted.

#### Pattern 5: All Sources Failed
```
[FAILOVER EXHAUSTED] All 2 sources failed for XYZ after 2.34s
[FAILOVER EXHAUSTED] Attempt details:
[FAILOVER EXHAUSTED]   - YahooFinanceDirectSource: connection_error (0.45s)
[FAILOVER EXHAUSTED]   - AlphaVantageSource: empty (1.89s)
```
**Solution**: Symbol may not exist, or both providers are having issues.

## Log Levels

The logging uses these levels:

- **DEBUG**: Detailed technical information (cache keys, HTTP headers, parsing details)
- **INFO**: General progress and success messages
- **WARNING**: Non-critical issues (empty data, rate limit hints)
- **ERROR**: Failures that prevent data fetching
- **SUCCESS**: Successful operations (custom level for positive outcomes)

## Configuration

### Adjusting Log Verbosity

In your application:

```python
# See everything (verbose)
logger.add(sys.stderr, level="DEBUG")

# See only important information
logger.add(sys.stderr, level="INFO")

# See only warnings and errors
logger.add(sys.stderr, level="WARNING")
```

### Filtering Logs

You can filter logs by component:

```python
# Only show multi-source logs
logger.add(sys.stderr, filter=lambda record: "MULTI-SOURCE" in record["message"])

# Only show failures
logger.add(sys.stderr, filter=lambda record: "FAILED" in record["message"] or record["level"].name == "ERROR")
```

## Troubleshooting Guide

### Issue: Downloads are slow

Look for:
```
[HTTP RESPONSE] Status: 200, Time: 5.43s, Size: 51234 bytes
```
If response times are consistently high (>3s), check:
- Internet connection speed
- Distance from data provider servers
- Provider API performance

### Issue: Intermittent failures

Look for:
```
[FAILOVER SUCCESS] Succeeded on attempt 2/2
```
If you see frequent failovers, it indicates:
- Primary source is unreliable
- Consider switching source order
- May need to add delays between requests

### Issue: Cache not working

Look for:
```
[CACHE DISABLED] Caching is disabled for YahooFinanceDirectSource
```
Or:
```
[CACHE MISS] SPY: Not in cache (key: SPY_2024-09-20_2024-10-20_1d)
[CACHE MISS] SPY: Not in cache (key: SPY_2024-09-20_2024-10-20_1d)
```
If same key shows multiple misses, cache may not be persisting correctly.

### Issue: API key problems

Look for:
```
[ALPHA VANTAGE ERROR] API key not configured for AAPL
```
Or:
```
[ALPHA VANTAGE RATE LIMIT] Your API call frequency is ...
```
Check API key configuration and daily limits.

## Performance Metrics

The logs include detailed timing information:

```
[FETCH SUCCESS] SPY: 21 rows fetched successfully (total: 0.52s, parse: 0.03s)
```

This shows:
- **Total time**: 0.52s (end-to-end)
- **Parse time**: 0.03s (just parsing)
- **Implied network time**: 0.49s (0.52 - 0.03)

Use these metrics to identify bottlenecks.

## Files Modified

1. `src/data_sources/yahoo_finance_direct.py` - Enhanced HTTP and parsing logging
2. `src/data_sources/multi_source.py` - Enhanced failover tracking
3. `src/core/base_data_source.py` - Enhanced cache logging
4. `frontend/pages/strategy_builder.py` - Enhanced frontend logging
5. `src/data_sources/alpha_vantage.py` - Enhanced API interaction logging

## Testing

Run the test script to verify logging is working:

```bash
python test_detailed_logging.py
```

Expected output includes:
- Successful fetches with timing details
- Cache hit/miss information
- Error handling demonstrations
- Batch operation progress

Check `download_test.log` for the complete log output.

## Best Practices

1. **Start with INFO level** - Provides good balance of information
2. **Enable DEBUG when troubleshooting** - Shows all details
3. **Log to file for production** - Easier to analyze later
4. **Use log rotation** - Prevent log files from growing too large
5. **Search for specific patterns** - Use grep or log analysis tools

## Example Analysis Session

```bash
# Find all failures
grep "FAILED" download_test.log

# Find all rate limit issues
grep "RATE LIMIT" download_test.log

# Find slow requests (>2s)
grep "Time: [2-9]\." download_test.log

# See what sources were used
grep "FAILOVER SUCCESS" download_test.log

# Check cache effectiveness
grep "CACHE HIT" download_test.log | wc -l
grep "CACHE MISS" download_test.log | wc -l
```

## Support

If downloads are still failing after checking logs:

1. Review the log patterns above
2. Check the specific error messages
3. Verify network connectivity
4. Confirm API keys are valid
5. Check data provider status pages
6. Review date ranges and symbols

The detailed logging should provide all information needed to diagnose the issue.
