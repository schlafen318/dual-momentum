# Real Data Implementation for Strategy Builder

## Overview

Updated the Streamlit Strategy Builder to **always use real market data** from Yahoo Finance instead of generating hypothetical/sample data.

## Changes Implemented

### File Modified: `dual_momentum_system/frontend/pages/strategy_builder.py`

#### 1. Replaced `generate_sample_data()` with `fetch_real_data()`

**Old Behavior:**
- Generated random walk sample data
- Not based on real market prices
- No actual market data fetched

**New Behavior:**
- Fetches real historical data from Yahoo Finance
- Uses actual OHLCV market data
- Respects user-selected date ranges

#### 2. Safe Asset Handling with Cash Fallback

**New Logic:**
```python
# Try to fetch safe asset data
if safe_asset:
    if safe_asset not in price_data_dict:
        # Attempt to fetch real data
        safe_asset_dict = fetch_real_data([safe_asset], ...)
        
        if safe_asset_dict:
            # Successfully fetched
            price_data_dict[safe_asset] = safe_asset_dict[safe_asset]
        else:
            # Could not fetch - use CASH instead
            warnings.append(
                f"⚠️ WARNING: Could not fetch real data for safe asset '{safe_asset}'.\n"
                f"   The strategy will use CASH during defensive periods instead."
            )
            safe_asset = None  # Use cash
```

#### 3. Pre-Backtest Warnings

The system now shows clear warnings **before starting** the backtest:

- ✅ Safe asset fetched successfully
- ⚠️ Safe asset unavailable - using cash
- ⚠️ Benchmark data unavailable
- ⚠️ Some symbols failed to fetch

**Example Warning Display:**
```
⚠️ WARNING: Could not fetch real data for safe asset 'XYZ'.
   The strategy will use CASH during defensive periods instead of XYZ.

⚠️ Could not fetch data for: INVALID1, INVALID2
These symbols will be excluded from the backtest.
```

## Function Details

### `fetch_real_data()`

```python
def fetch_real_data(
    symbols: List[str],
    start_date,
    end_date,
    data_source,
    asset_instance,
    status_text=None
) -> Dict[str, PriceData]:
    """
    Fetch REAL market data from Yahoo Finance.
    
    Returns:
        Dictionary of symbol -> PriceData with real market data
    """
```

**Features:**
- Fetches from Yahoo Finance API
- Handles missing/invalid symbols gracefully
- Normalizes data using appropriate asset class
- Shows progress updates
- Returns only successfully fetched symbols

### Updated `run_backtest()`

**Key Changes:**

1. **Initializes real data source:**
   ```python
   from src.data_sources.yahoo_finance import YahooFinanceSource
   data_source = YahooFinanceSource(config={'cache_enabled': True})
   ```

2. **Fetches real data for universe:**
   ```python
   price_data_dict = fetch_real_data(
       symbols,
       start_date,
       end_date,
       data_source,
       asset_instance,
       status_text
   )
   ```

3. **Validates safe asset availability:**
   - Attempts to fetch safe asset data
   - If unavailable, sets `safe_asset = None` (cash)
   - Warns user before starting backtest

4. **Collects and displays warnings:**
   ```python
   warnings = []
   # ... collect warnings during data fetching ...
   if warnings:
       st.warning("\n\n".join(warnings))
   ```

## User Experience

### Before (Old Behavior):
1. User configures strategy with safe asset "SHY"
2. System generates random sample data
3. Backtest runs with hypothetical data
4. Results not based on real market behavior

### After (New Behavior):
1. User configures strategy with safe asset "SHY"
2. System fetches real Yahoo Finance data for universe
3. System attempts to fetch "SHY" data
4. If "SHY" data unavailable:
   - Shows warning: "⚠️ Could not fetch data for SHY, using CASH"
   - User sees warning before backtest starts
   - User can cancel or proceed
5. Backtest runs with real market data

## Error Handling

### Invalid Symbols
```
⚠️ Could not fetch data for: INVALID, BADTICKER
These symbols will be excluded from the backtest.
```

### Safe Asset Unavailable
```
⚠️ WARNING: Could not fetch real data for safe asset 'XYZ'.
   The strategy will use CASH during defensive periods instead of XYZ.
```

### No Data Available
```
❌ Failed to fetch data for any symbols. Please check symbols and try again.
```

### Benchmark Unavailable
```
⚠️ Could not fetch benchmark data for BENCHMARK
```

## Data Flow

```
User Configuration
    ↓
Initialize Yahoo Finance Data Source
    ↓
Fetch Real Data for Universe Symbols
    ↓
Check Safe Asset
    ├─ In Universe? → Use existing data
    └─ Not in Universe? → Try to fetch
        ├─ Success? → Add to price_data
        └─ Failed? → Set safe_asset=None (CASH) + Warn User
    ↓
Show Pre-Backtest Warnings
    ↓
User Reviews and Confirms
    ↓
Run Backtest with Real Data
```

## Benefits

1. **Real Market Data**: Backtests use actual historical prices
2. **Transparent Fallbacks**: User knows when cash is used instead of safe asset
3. **Pre-Validation**: Warnings shown before backtest starts
4. **Graceful Degradation**: System continues with available data
5. **Clear Communication**: Users understand exactly what's happening

## Testing

### Test Case 1: Valid Universe + Valid Safe Asset
- **Input**: SPY, AGG, GLD + Safe Asset: SHY
- **Expected**: Fetches all 4 symbols successfully
- **Result**: Backtest runs with real data for all assets

### Test Case 2: Valid Universe + Invalid Safe Asset
- **Input**: SPY, AGG + Safe Asset: INVALIDXYZ
- **Expected**: Fetches SPY, AGG; warns about INVALIDXYZ; uses cash
- **Result**: Warning displayed, backtest proceeds with cash

### Test Case 3: Some Invalid Universe Symbols
- **Input**: SPY, INVALID1, AGG, INVALID2
- **Expected**: Fetches SPY, AGG; warns about INVALID1, INVALID2
- **Result**: Warning displayed, backtest runs with 2 valid symbols

### Test Case 4: All Invalid Symbols
- **Input**: INVALID1, INVALID2
- **Expected**: Error message, backtest cancelled
- **Result**: "Failed to fetch data for any symbols" error

## Configuration

The data source uses caching to improve performance:

```python
data_source = YahooFinanceSource(config={'cache_enabled': True})
```

This reduces redundant API calls when fetching the same symbol multiple times.

## Code Changes Summary

**Lines Modified:**
- `run_backtest()` function: ~120 lines rewritten
- `generate_sample_data()` → `fetch_real_data()`: Complete replacement

**New Features Added:**
1. Real Yahoo Finance data fetching
2. Safe asset validation with cash fallback
3. Pre-backtest warning system
4. Graceful error handling for missing data
5. Progress updates during data fetching

**Removed:**
- Random walk data generation
- Mock price data creation
- Hypothetical volatility/trend simulation

## Migration Notes

**For Users:**
- No action required - works automatically
- You'll now see real market data in backtests
- Warnings appear if data unavailable
- Cash used automatically when safe asset missing

**For Developers:**
- `generate_sample_data()` function removed
- Use `fetch_real_data()` for real data
- Yahoo Finance is the default data source
- Caching enabled by default

## Future Enhancements

Potential improvements:
1. Support for multiple data sources (Alpha Vantage, Polygon, etc.)
2. Data quality checks (missing dates, gaps, etc.)
3. Alternative safe assets suggestion (if primary unavailable)
4. Offline mode with previously cached data
5. Data source selection in UI

## Status

✅ **COMPLETE** - Real data implementation deployed

- ✅ Real Yahoo Finance data fetching
- ✅ Safe asset validation with cash fallback
- ✅ Pre-backtest warnings
- ✅ Error handling for invalid symbols
- ✅ Progress indicators
- ✅ User-friendly warning messages
