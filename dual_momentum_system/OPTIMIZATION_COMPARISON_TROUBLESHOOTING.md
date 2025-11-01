# Optimization Comparison Troubleshooting Guide

## Quick Diagnosis

When you see "All backtest methods failed", follow these steps:

### Step 1: Check the Error Details

The error message will now show:
```
All X backtest methods failed!
Methods attempted: [list of methods]
Check logs above for specific error details for each method.
```

**Action:** Click "Show error details" in Streamlit to see the full traceback.

### Step 2: Look for Validation Errors

The system now validates inputs **before** running backtests. Look for these messages:

#### "price_data is empty"
- **Cause:** No cached price data available
- **Fix:** Run a backtest from Strategy Builder first
- **Location:** Backend validation

#### "price_data['XXX'] must be a PriceData object"
- **Cause:** Data is in wrong format (likely DataFrame instead of PriceData)
- **Fix:** Ensure data provider returns PriceData objects
- **Location:** Backend type checking

#### "price_data['XXX'] has empty DataFrame"
- **Cause:** Symbol has no data
- **Fix:** Check data source, date range, or remove symbol
- **Location:** Backend data validation

#### "No symbols found in backtest configuration"
- **Cause:** `last_backtest_params` has no universe or symbols
- **Fix:** Run a proper backtest with symbols configured
- **Location:** Frontend validation

#### "Insufficient assets for optimization comparison"
- **Cause:** Less than 2 assets available
- **Fix:** Add more symbols to your universe
- **Location:** Frontend validation

### Step 3: Check Method-Specific Errors

Each method that fails will show:
```
Running backtest with [Method Name]...
  ✗ Failed: [Error message]
  Error details: [Full traceback]
```

**Common errors:**

#### ValueError: Insufficient data for strategy
- **Cause:** Not enough historical data for lookback period
- **Fix:** 
  - Increase data buffer (fetch data starting earlier)
  - Reduce strategy lookback_period
  - Check data availability for symbols

#### AttributeError: 'NoneType' object has no attribute
- **Cause:** Missing data or configuration
- **Fix:** 
  - Verify all symbols have data
  - Check strategy configuration is complete
  - Ensure safe_asset is configured if used

#### TypeError: unsupported operand type(s)
- **Cause:** Data type mismatch
- **Fix:**
  - Verify price data is PriceData objects
  - Check dates are datetime objects
  - Ensure numeric fields are numbers

### Step 4: Verify Your Configuration

Check that your backtest parameters are valid:

```python
# Required parameters:
last_backtest_params = {
    'strategy_type': 'Dual Momentum',
    'strategy_config': {
        'lookback_period': 252,
        'position_count': 3,
        'safe_asset': 'AGG',
        # ... other config
    },
    'universe': ['SPY', 'EFA', 'EEM', 'AGG', 'TLT'],  # At least 2 symbols
    'start_date': datetime(2020, 1, 1),
    'end_date': datetime(2023, 12, 31),
    'initial_capital': 100000,
    'commission': 0.001,
    'slippage': 0.0005,
}
```

### Step 5: Check Verbose Output

With verbose=True (now default), you'll see:
```
✓ Validated X assets
✓ Date range: YYYY-MM-DD to YYYY-MM-DD

Running backtest with Momentum Based...
  ✓ Total Return: XX.XX%, Sharpe: X.XX, Max DD: -XX.XX%

Running backtest with Equal Weight...
  ✗ Failed: [error]
  Error details: [traceback]
```

**This tells you:**
- Which methods worked
- Which methods failed
- Exact error for each failure

## Common Issues and Fixes

### Issue: "Data not in PriceData format"

**Symptom:** Type error about PriceData
**Cause:** Cached data is DataFrame, not PriceData object
**Fix:**
```python
# Clear the cache and re-run backtest
st.session_state.cached_price_data = {}
```

### Issue: "Strategy has no signals"

**Symptom:** Backtest completes but with 0 trades
**Cause:** 
- Momentum filter too strict
- Threshold too high
- Insufficient assets passing filter

**Fix:**
- Lower absolute_threshold
- Increase position_count
- Add more assets to universe
- Check safe_asset configuration

### Issue: "Optimization fails but momentum_based works"

**Symptom:** First method succeeds, others fail
**Cause:** Optimization requires minimum 2 assets
**Fix:** Ensure at least 2 assets pass momentum filter

### Issue: "All methods fail with same error"

**Symptom:** Same error for all methods
**Cause:** Likely data or strategy issue, not optimization issue
**Fix:** 
1. Test with standard backtest first (no comparison)
2. Fix underlying issue
3. Then retry comparison

## Debugging Checklist

Before running optimization comparison:

- [ ] Run a standard backtest first (from Strategy Builder)
- [ ] Verify it completes successfully
- [ ] Check you have at least 2 assets in universe
- [ ] Ensure date range is reasonable (not too short)
- [ ] Verify safe_asset is in universe if configured
- [ ] Check you have sufficient historical data
- [ ] Clear cache if you've made data changes

## Still Having Issues?

If none of the above helps:

1. **Check logs directory:** Look for detailed backtest logs
   - Location: `dual_momentum_system/logs/`
   - File pattern: `backtest_*.log`

2. **Test individual components:**
   ```python
   # Test strategy alone
   from src.strategies.dual_momentum import DualMomentumStrategy
   strategy = DualMomentumStrategy(config)
   signals = strategy.generate_signals(price_data)
   print(signals)  # Should return list of Signal objects
   ```

3. **Test optimization alone:**
   ```python
   from src.portfolio_optimization import compare_portfolio_methods
   # Test with simple returns data
   ```

4. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## What to Report

If you need to report an issue, include:

1. **Full error message** from "Show error details"
2. **Configuration** - your strategy config and universe
3. **Data info** - symbols, date range, data source
4. **Steps to reproduce** - what you clicked/ran
5. **Logs** - relevant log files from logs directory
6. **Validation output** - the "✓ Validated X assets" messages

## Prevention

To avoid these errors:

1. **Always run standard backtest first** before comparison
2. **Use reasonable parameters** - don't be too extreme
3. **Keep cache fresh** - clear if you change data sources
4. **Test with few methods** - start with 2-3, not all 8
5. **Monitor logs** - check for warnings during backtest

## Success Indicators

You know it's working when you see:
```
✓ Validated 6 assets
✓ Date range: 2020-01-01 to 2023-12-31

Running backtest with Momentum Based...
  ✓ Total Return: 45.20%, Sharpe: 1.15, Max DD: -18.30%

Running backtest with Equal Weight...
  ✓ Total Return: 52.80%, Sharpe: 1.28, Max DD: -15.20%

[etc...]

COMPARISON COMPLETE
Best Sharpe Ratio: Maximum Sharpe
Best Total Return: Risk Parity
```

## Quick Fixes Summary

| Error | Quick Fix |
|-------|-----------|
| "price_data is empty" | Run backtest from Strategy Builder first |
| "Not a PriceData object" | Clear cache: `st.session_state.cached_price_data = {}` |
| "Insufficient assets" | Add more symbols to universe |
| "No symbols found" | Configure universe in Strategy Builder |
| "Insufficient data" | Fetch more historical data, reduce lookback |
| "All methods same error" | Fix data/strategy first, not optimization |

---

**Remember:** With the new error handling, you'll get detailed diagnostics. Read the error messages carefully - they now tell you exactly what's wrong!
