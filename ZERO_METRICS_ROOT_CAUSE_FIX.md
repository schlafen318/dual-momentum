# Zero Metrics Root Cause Fix

## Problem Summary
Several performance metrics were displaying 0.00% in the dashboard despite having actual backtest data:
- Annualized Return: 0.00%
- CAGR: 0.00%
- Best Month: 0.00%
- Worst Month: 0.00%
- Positive Months: 0%

## Root Cause Identified

The issue was a **type mismatch** in the data flow between VectorBT and the metrics calculator:

### VectorBT Behavior
- `portfolio.returns()` returns a **DataFrame** (even for single-asset portfolios)
- `portfolio.value()` returns a **DataFrame** (even for single-asset portfolios)

### Metrics Calculator Expectation
- `VectorizedMetricsCalculator.calculate_all_metrics()` expects **Series** objects
- When DataFrame is passed instead of Series, pandas operations fail or produce incorrect results

### Why It Failed
When DataFrame was passed to the metrics calculator:
1. Operations like `returns.index[-1] - returns.index[0]` failed for CAGR calculation
2. Resample operations behaved differently with DataFrame vs Series
3. Monthly aggregations didn't work correctly with DataFrame structure

## Solution

### Fixed in `vectorized_engine.py`

Added DataFrame → Series conversion after extracting returns and equity from VectorBT:

```python
# Extract key series
equity_curve = portfolio.value()
returns = portfolio.returns()

# Convert to Series if DataFrame (VectorBT returns DataFrames even for single assets)
if isinstance(returns, pd.DataFrame):
    if returns.shape[1] == 1:
        returns = returns.iloc[:, 0]
    else:
        # Multi-asset: use total portfolio returns
        returns = returns.sum(axis=1)

if isinstance(equity_curve, pd.DataFrame):
    if equity_curve.shape[1] == 1:
        equity_curve = equity_curve.iloc[:, 0]
    else:
        # Multi-asset: use total portfolio value
        equity_curve = equity_curve.sum(axis=1)
```

### Benefits
1. **Single-asset portfolios**: Extracts the single column as a Series
2. **Multi-asset portfolios**: Aggregates to total portfolio returns/value
3. **Preserves DateTimeIndex**: Conversion maintains the datetime index
4. **No fallback needed**: Fixes the root cause instead of masking it

## Verification Results

### Single-Asset Test
- Total Return: -5.80% ✓
- Annualized Return: -2.32% ✓
- CAGR: -3.27% ✓
- Best Month: 8.98% ✓
- Worst Month: -10.44% ✓
- Positive Months: 41% ✓

### Multi-Asset Test
- Total Return: 41.19% ✓
- Annualized Return: 14.07% ✓
- CAGR: 21.14% ✓
- Best Month: 5.80% ✓
- Worst Month: -2.85% ✓
- Positive Months: 68% ✓

## Files Modified

1. **`src/backtesting/vectorized_engine.py`**
   - Added DataFrame to Series conversion in `_extract_results()` method
   - Lines 452-469

2. **`src/backtesting/vectorized_metrics.py`**
   - Removed unnecessary fallback logic
   - Kept original clean implementation

## Impact

- ✓ All metrics now calculate correctly
- ✓ Both single-asset and multi-asset portfolios work
- ✓ DateTimeIndex preserved throughout the flow
- ✓ No breaking changes to existing API
- ✓ No performance impact
- ✓ Clean, maintainable solution

## Conclusion

The fix addresses the actual root cause (type mismatch) rather than adding workarounds. This ensures robust metric calculation for all portfolio types while maintaining clean, maintainable code.
