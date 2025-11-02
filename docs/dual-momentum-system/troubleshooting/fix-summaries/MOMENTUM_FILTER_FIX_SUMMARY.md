# Momentum Filter Fix Summary

**Date:** 2025-10-17  
**Branch:** cursor/investigate-momentum-filter-failure-fc9b  
**Status:** ✅ FIXED

## Executive Summary

Fixed a critical bug that caused the momentum filter to reject all assets during backtesting, resulting in zero trades. The issue was a combination of two problems:

1. **Off-by-one error in data slicing** - The `_get_current_data` method wasn't providing enough data bars for `pct_change(N)` calculations
2. **Insufficient data validation** - The backtest engine was attempting to rebalance before enough warm-up data was available

## Root Cause Analysis

### Problem 1: Off-by-One Error in Data Slicing

**Location:** `src/backtesting/engine.py`, line 312  
**Issue:** The momentum calculation requires N+1 bars to calculate `pct_change(N)`, but only N bars were being provided.

**Example:**
- To calculate momentum over 252 days using `pct_change(252)`
- Need: 253 bars (bar 0 through bar 252)
- Was providing: 252 bars (bar 1 through bar 252)
- Result: All momentum scores = NaN

**Original Code:**
```python
start_loc = max(0, date_loc - lookback + 1)  # Wrong: gives exactly N bars
slice_df = df.iloc[start_loc:date_loc + 1]
```

**Fixed Code:**
```python
start_loc = max(0, date_loc - lookback)  # Correct: gives N+1 bars
slice_df = df.iloc[start_loc:date_loc + 1]
```

**Why this happened:**
- `pct_change(N)` calculates: `(price[i] - price[i-N]) / price[i-N]`
- For position `i=252`, it needs to look back to position `i-252 = 0`
- So you need positions 0 through 252 (253 total bars)

### Problem 2: Insufficient Data Validation

**Location:** `src/backtesting/engine.py`, line 148  
**Issue:** The condition `i >= strategy.get_required_history()` checked the index position but didn't verify that each symbol actually had enough bars of historical data before that position.

**Added validation:**
```python
# Verify we have enough actual data (not just index position)
sufficient_data = True
required_history = strategy.get_required_history()

for symbol, df in aligned_data.items():
    date_loc = df.index.get_loc(current_date)
    if date_loc < required_history:
        sufficient_data = False
        logger.debug(
            f"Insufficient data for {symbol}: only {date_loc} bars available, "
            f"need {required_history}"
        )
        break

if not sufficient_data:
    continue  # Skip rebalancing
```

## Changes Made

### 1. Fixed Data Slicing (`src/backtesting/engine.py`)

**Lines 310-315:**
- Changed `start_loc` calculation to include one extra bar
- Added explanatory comment about `pct_change(N)` requiring N+1 bars

### 2. Enhanced Data Validation (`src/backtesting/engine.py`)

**Lines 148-167:**
- Added per-symbol data availability check
- Skip rebalancing if any symbol lacks sufficient history
- Added debug logging to explain why rebalancing is skipped

### 3. Improved Error Messages (`src/backtesting/engine.py`)

**Lines 109-119:**
- Enhanced error message when `backtest_ready()` fails
- Added guidance on how to fetch sufficient warm-up data
- Calculate and display the recommended data fetch period

### 4. Added First Rebalance Logging (`src/backtesting/engine.py`)

**Lines 126-141:**
- Log when the first rebalancing is expected to occur
- Warn if insufficient data for any rebalancing
- Helps users understand warm-up period requirements

### 5. Enhanced Momentum Debugging (`src/strategies/dual_momentum.py`)

**Lines 152-168:**
- Added debug logging showing momentum calculation details
- Log latest momentum scores for each asset
- Show pass/fail status for each asset against the threshold

### 6. Fixed Optional Imports (`src/backtesting/__init__.py`)

**Lines 11-33:**
- Made `vectorbt` and `scipy` imports optional
- Allows core backtesting to work without optional dependencies
- Prevents import errors when running basic backtests

### 7. Created Utility Functions (`src/backtesting/utils.py`)

**New file with helper functions:**
- `calculate_data_fetch_dates()` - Calculates correct date range for fetching data
- `estimate_required_data_bars()` - Estimates warm-up data requirements
- `validate_data_sufficiency()` - Validates data before backtesting
- `print_backtest_summary()` - Displays configuration summary

## Test Results

### Before Fix:
```
✗ No assets pass absolute momentum filter
✗ Final Capital: $100,000.00
✗ Total Return: 0.00%
✗ Number of Trades: 0
```

### After Fix:
```
✓ Generated 3 long signals for: ['QQQ', 'SPY', 'DIA']
✓ Final Capital: $134,948.41
✓ Total Return: 34.95%
✓ Number of Trades: 75
```

## User Guidance

### How to Avoid This Issue

When running backtests, always fetch MORE data than your backtest period to allow for warm-up:

```python
from datetime import datetime, timedelta
from src.backtesting.utils import calculate_data_fetch_dates

# Your desired backtest period
backtest_start = datetime(2022, 10, 18)
backtest_end = datetime(2025, 10, 17)
lookback_period = 252  # Your strategy's lookback

# Calculate correct data fetch dates (includes warm-up period)
data_start, data_end = calculate_data_fetch_dates(
    backtest_start,
    backtest_end,
    lookback_period,
    safety_factor=1.5  # Fetch 50% extra for safety
)

# Fetch data with warm-up period
for symbol in symbols:
    raw_data = data_source.fetch_data(symbol, data_start, data_end, '1d')
    price_data[symbol] = asset.normalize_data(raw_data, symbol)

# Run backtest (will use start_date/end_date to filter backtest period)
results = engine.run(
    strategy=strategy,
    price_data=price_data,
    start_date=backtest_start,  # Backtest starts here
    end_date=backtest_end
)
```

### Rule of Thumb

For a lookback period of **N days**, fetch data starting at least **N × 1.5** days before your desired backtest start date.

**Examples:**
- 252-day lookback → Fetch ~380 extra days (~1.5 years extra)
- 126-day lookback → Fetch ~190 extra days (~9 months extra)
- 63-day lookback → Fetch ~95 extra days (~4.5 months extra)

### Quick Check

Use the validation utility before running backtests:

```python
from src.backtesting.utils import validate_data_sufficiency

is_valid, message = validate_data_sufficiency(
    price_data,
    lookback_period=252
)

if not is_valid:
    print(f"❌ {message}")
else:
    print(f"✓ {message}")
    # Proceed with backtest
```

## Technical Details

### Why `pct_change(N)` Needs N+1 Bars

The pandas `pct_change(N)` function calculates percentage change from N periods ago:

```
pct_change(N)[i] = (value[i] - value[i-N]) / value[i-N]
```

For this to work at position `i`, you need data at both position `i` and position `i-N`:
- If N=252 and i=252, you need positions 0 through 252
- That's 253 total data points (0, 1, 2, ..., 252)

### Data Slicing Math

With the fix:
```python
date_loc = 252  # Current position
lookback = 252
start_loc = max(0, date_loc - lookback)  # = max(0, 0) = 0
slice_df = df.iloc[start_loc:date_loc + 1]  # iloc[0:253] = 253 bars ✓
```

Without the fix:
```python
start_loc = max(0, date_loc - lookback + 1)  # = max(0, 1) = 1
slice_df = df.iloc[start_loc:date_loc + 1]  # iloc[1:253] = 252 bars ✗
```

## Files Modified

1. `src/backtesting/engine.py` - Core backtest engine fixes
2. `src/strategies/dual_momentum.py` - Enhanced debugging
3. `src/backtesting/__init__.py` - Optional imports
4. `src/backtesting/utils.py` - New utility functions (NEW FILE)

## Files Created

1. `diagnose_momentum.py` - Diagnostic script for momentum issues
2. `diagnose_backtest_dates.py` - Diagnostic for date alignment
3. `test_momentum_fix.py` - Test suite for verifying the fix
4. `MOMENTUM_FILTER_FIX_SUMMARY.md` - This document

## Backward Compatibility

✅ **The fix is backward compatible.**

Existing backtests will continue to work, but will now:
- Calculate momentum correctly (no more NaN values)
- Skip early rebalancing when data is insufficient
- Generate helpful warnings and guidance

The only behavioral change: backtests with insufficient warm-up data will now skip early rebalancing periods instead of proceeding with NaN momentum values.

## Recommendations for Future Development

1. **Add automated data fetching** - Create a wrapper that automatically calculates and fetches correct date ranges
2. **Add pre-flight checks** - Validate data sufficiency before starting backtest
3. **Improve error messages** - Provide specific guidance on missing data
4. **Add configuration validation** - Check strategy parameters against available data
5. **Create example notebooks** - Show proper data fetching patterns

## Conclusion

The momentum filter issue has been fully resolved. The fix ensures that:

✅ Momentum calculations receive sufficient data (N+1 bars)  
✅ Rebalancing is skipped when data is insufficient  
✅ Clear error messages guide users to correct data fetching  
✅ Utility functions help users avoid the issue  
✅ Debug logging helps diagnose similar issues  

Users should now experience reliable momentum calculations and successful backtesting when following the data fetching guidance.
