# Data Availability Query Feature

## Overview

This feature addresses the question: **"Why do we limit backtesting to start from 2012?"**

**Answer:** We don't! But data availability varies by asset. This feature helps you:
1. Query the actual data availability for your universe
2. Default to the longest possible backtest period
3. Make informed decisions about backtest start dates

## Problem Statement

Previously, the system used arbitrary defaults:
- **Strategy Builder**: 3 years of history
- **Hyperparameter Tuning**: 5 years of history

These defaults were conservative but not optimal:
- Some assets have data going back to the 1990s (SPY: 1993, QQQ: 1999)
- Other assets started later (EEM: 2003, AGG: 2003)
- Users had no visibility into actual data availability
- Backtests used less history than available, reducing statistical significance

## Solution

### 1. Data Availability Query Utility

New function in `src/backtesting/utils.py`:

```python
def get_universe_data_availability(
    symbols: List[str],
    data_source: BaseDataSource,
    max_retries: int = 2
) -> Tuple[Optional[datetime], Optional[datetime], Dict]:
    """
    Query the earliest and latest available dates across all symbols.
    
    Returns:
        - earliest_common_date: Latest inception date (conservative backtest start)
        - latest_common_date: Earliest end date
        - per_symbol_ranges: Individual date ranges per symbol
    """
```

**Key Insight:** The "earliest common date" is the **latest** of all inception dates.
- If SPY started in 1993, EFA in 2001, and EEM in 2003
- Then the earliest date where **ALL** symbols have data is **2003-04-11** (EEM's inception)

### 2. Enhanced Strategy Builder

#### New "Check Data Availability" Button

Located in the Date Range section, this button:
1. Queries actual data availability for selected symbols
2. Shows common date range across all symbols
3. Shows per-symbol date ranges
4. Identifies which symbol limits the backtest start date
5. Automatically updates the default start date to use maximum available history

#### Intelligent Defaults

**Before:**
- Default: 3 years back from today
- User had no idea how much history was actually available

**After:**
- Default: 10 years back (if data not checked)
- Default: Earliest available date (if data checked) ✅
- Clear indication of data limitations
- Warning if start date is before available data

#### Example Output

```
📊 Data Availability Details

Common Date Range: 2003-04-11 to 2025-10-24
Duration: 8227 days (22.5 years)

Per-Symbol Availability:
  • SPY    : 1993-01-29 to 2025-10-24 (32.7 years)
  • EFA    : 2001-08-17 to 2025-10-24 (24.2 years)
  • EEM    : 2003-04-11 to 2025-10-24 (22.5 years)  ← Limiting
  • AGG    : 2003-09-29 to 2025-10-24 (22.1 years)
  • TLT    : 2002-07-30 to 2025-10-24 (23.2 years)

💡 Earliest date limited by: EEM
```

### 3. Enhanced Hyperparameter Tuning

- Default increased from 5 years to 10 years
- Added tip encouraging users to use maximum available history
- Shows tuning period duration in years
- Explains importance of long periods for parameter estimation

### 4. Multi-Source Failover

Added `get_data_range()` method to `MultiSourceDataProvider`:
- Tries each data source in order (Yahoo Finance, Alpha Vantage, etc.)
- Returns date range from first successful source
- Provides robustness against individual source failures

## Usage Examples

### Strategy Builder (Interactive)

1. Navigate to "🛠️ Strategy Builder"
2. Select your asset universe (e.g., SPY, EFA, EEM, AGG, TLT)
3. Click "🔍 Check Data Availability"
4. System queries and displays:
   - Common date range for all symbols
   - Per-symbol availability
   - Which symbol limits the start date
5. Start date automatically defaults to earliest available
6. User can override if they want a shorter period

### Programmatic Usage

```python
from datetime import datetime
from src.backtesting.utils import get_universe_data_availability
from src.data_sources import get_default_data_source

# Initialize data source
data_source = get_default_data_source()

# Define your universe
symbols = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD']

# Query data availability
earliest, latest, ranges = get_universe_data_availability(symbols, data_source)

print(f"Can backtest from {earliest.date()} to {latest.date()}")
print(f"Total period: {(latest - earliest).days / 365.25:.1f} years")

# Show per-symbol details
for symbol, (start, end) in ranges.items():
    years = (end - start).days / 365.25
    print(f"{symbol}: {start.date()} to {end.date()} ({years:.1f} years)")
    
# Use for backtesting
backtest_start = earliest  # Use all available history
backtest_end = latest

# Account for warm-up period
from src.backtesting.utils import calculate_data_fetch_dates
lookback_period = 252  # Your strategy's lookback

data_fetch_start, data_fetch_end = calculate_data_fetch_dates(
    backtest_start_date=backtest_start,
    backtest_end_date=backtest_end,
    lookback_period=lookback_period
)

# Fetch data with warm-up period included
price_data = {}
for symbol in symbols:
    raw_data = data_source.fetch_data(symbol, data_fetch_start, data_fetch_end)
    price_data[symbol] = asset_class.normalize_data(raw_data, symbol)

# Run backtest with maximum available history
results = engine.run(
    strategy=strategy,
    price_data=price_data,
    start_date=backtest_start,  # Earliest common date
    end_date=backtest_end
)
```

## Common Asset Inception Dates

Reference for popular ETFs:

### US Equities
- **SPY** (S&P 500): January 29, 1993
- **QQQ** (Nasdaq-100): March 10, 1999
- **IWM** (Russell 2000): May 26, 2000
- **DIA** (Dow 30): January 14, 1998

### International Equities
- **EFA** (Developed Markets): August 17, 2001
- **EEM** (Emerging Markets): April 11, 2003
- **VEU** (Ex-US): March 4, 2007

### Fixed Income
- **AGG** (Aggregate Bonds): September 29, 2003
- **TLT** (Long-Term Treasuries): July 30, 2002
- **SHY** (Short-Term Treasuries): July 27, 2002
- **BND** (Total Bond): April 10, 2007

### Commodities & Alternatives
- **GLD** (Gold): November 18, 2004
- **USO** (Oil): April 10, 2006

### Common Portfolio Limitations

**Classic 60/40 Portfolio** (SPY, AGG):
- Limited by AGG: September 2003
- Available history: ~22 years

**Global Equity Momentum** (SPY, EFA, EEM):
- Limited by EEM: April 2003
- Available history: ~22 years

**Tactical Asset Allocation** (SPY, EFA, EEM, AGG, TLT):
- Limited by AGG: September 2003
- Available history: ~22 years

**Gold-Included Portfolio** (SPY, AGG, GLD):
- Limited by GLD: November 2004
- Available history: ~21 years

## Benefits

### For Users
1. **Maximum Statistical Significance**: Use all available history for robust backtests
2. **Informed Decisions**: Know exactly when data starts for each asset
3. **No Surprises**: Clear warnings about data limitations
4. **Flexibility**: Can still choose shorter periods if desired

### For Strategy Development
1. **Longer Walk-Forward Tests**: More data = better out-of-sample validation
2. **Better Parameter Estimates**: Hyperparameter tuning with more history
3. **Regime Diversity**: Capture multiple market cycles
4. **Reduced Overfitting**: More data reduces risk of curve-fitting

### For Research
1. **Transparency**: Document exact data periods used
2. **Reproducibility**: Others can verify data availability
3. **Comparability**: Standardized approach to data selection

## Best Practices

### 1. Always Check Data Availability
Before running important backtests:
```python
# Don't assume dates - query them!
earliest, latest, ranges = get_universe_data_availability(symbols, data_source)
```

### 2. Use Maximum Available History
For robust backtests, use all available data:
```python
# Instead of arbitrary 3-5 years
start_date = datetime.now() - timedelta(days=365*3)  # ❌ Arbitrary

# Use maximum available
earliest, latest, _ = get_universe_data_availability(symbols, data_source)
start_date = earliest  # ✅ Data-driven
```

### 3. Document Data Limitations
In research notes:
```
Backtest Period: 2003-04-11 to 2025-10-24 (22.5 years)
Limiting Asset: EEM (inception: 2003-04-11)

Note: SPY and TLT have longer histories, but EEM limits the 
common period for this multi-asset strategy.
```

### 4. Consider Survivor Bias
Newer assets may have survivor bias. Balance between:
- **Longer history** (older assets, more cycles)
- **Recent assets** (potential survivor bias)

### 5. Account for Warm-Up Periods
Always fetch extra data for momentum calculations:
```python
# Query availability
earliest, latest, _ = get_universe_data_availability(symbols, data_source)

# Account for warm-up
data_start, data_end = calculate_data_fetch_dates(
    backtest_start_date=earliest,
    backtest_end_date=latest,
    lookback_period=252  # Your strategy's lookback
)

# Fetch with warm-up included
price_data = fetch_data(symbols, data_start, data_end)

# Backtest uses only the intended period
results = engine.run(strategy, price_data, 
                    start_date=earliest,  # Actual backtest start
                    end_date=latest)
```

## Technical Implementation

### Files Modified

1. **`src/backtesting/utils.py`**
   - Added `get_universe_data_availability()` function
   - Returns earliest common date, latest date, and per-symbol ranges

2. **`src/data_sources/multi_source.py`**
   - Added `get_data_range()` method with failover support
   - Tries each source until one succeeds

3. **`frontend/page_modules/strategy_builder.py`**
   - Added "Check Data Availability" button
   - Shows expandable data availability details
   - Intelligent default dates based on actual availability
   - Warning if start date precedes available data
   - Changed default from 3 years to 10 years (when not checked)

4. **`frontend/page_modules/hyperparameter_tuning.py`**
   - Changed default from 5 years to 10 years
   - Added tip about using maximum history for tuning
   - Shows tuning period duration

### Data Sources Supported

The `get_data_range()` method is implemented in:
- ✅ YahooFinanceDirectSource
- ✅ YahooFinanceSource  
- ✅ MultiSourceDataProvider (with failover)

Future data sources should implement this method for compatibility.

## Future Enhancements

### Potential Improvements
1. **Cache date ranges** - Avoid repeated queries for same symbols
2. **Batch queries** - Query multiple symbols in parallel
3. **Data quality metrics** - Show data gaps, missing days, etc.
4. **Visual timeline** - Graph showing per-symbol availability
5. **Universe suggestions** - Recommend universes based on desired date range
6. **Automatic universe adjustment** - Suggest removing limiting assets

### Advanced Features
1. **Walk-forward with expanding window** - Start with shorter period, expand over time
2. **Per-asset backtests** - Compare results with/without limiting assets
3. **Survivorship analysis** - Quantify impact of asset selection timing

## Conclusion

This feature transforms the backtesting workflow from using arbitrary date defaults to **data-driven date selection**. Users can now:

✅ Query actual data availability  
✅ Use maximum available history  
✅ Make informed decisions about backtest periods  
✅ Understand which assets limit their analysis  
✅ Get clear warnings about data constraints  

The result is **more robust backtests** with **better statistical significance** and **full transparency** about data limitations.

---

**Related Documentation:**
- `MOMENTUM_FILTER_FIX_SUMMARY.md` - Explains warm-up period calculations
- `SAFE_ASSET_AUTO_FETCH_FEATURE.md` - Auto-fetching missing safe assets
- `IMPLEMENTATION_COMPLETE_REAL_DATA.md` - Real data integration guide
