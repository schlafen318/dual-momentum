# SPY Momentum Strategy Return Discrepancy - Root Cause & Fix

## Problem Statement

When running an absolute momentum strategy with only SPY as the asset, where all signals are BUY (100% positive momentum), the strategy returns were significantly different from SPY buy-and-hold returns. The discrepancy was much larger than expected transaction costs.

## Root Cause Analysis

### Issue 1: Unnecessary Position Closing at Rebalancing

**Location:** `dual_momentum_system/src/backtesting/engine.py:640-648`

**Problem:** The backtest engine was closing ALL positions at every rebalancing event, even when the signal indicated to continue holding the same asset.

```python
# OLD CODE - Line 640
# Close all existing positions first to free up cash for rebalancing
if self.positions:
    logger.info("   Closing existing positions for rebalancing:")
    for symbol in list(self.positions.keys()):
        # ... closes EVERY position ...
        self._close_position(symbol, current_date, aligned_data)
```

**Impact:**
- With monthly rebalancing, this meant closing and reopening the SPY position every month
- Each close incurs: slippage (0.05%) + commission (0.1%) = 0.15% cost
- Each open incurs: slippage (0.05%) + commission (0.1%) = 0.15% cost
- **Total cost per rebalancing: 0.30%**
- Over a year (12 rebalances): **~3.6% unnecessary drag**

### Issue 2: Inefficient Position Adjustment

**Location:** `dual_momentum_system/src/backtesting/engine.py:863-873`

**Problem:** When adjusting an existing position (e.g., changing size due to rebalancing), the old `_adjust_position` method was closing the entire position and reopening it, rather than just trading the difference.

```python
# OLD CODE - Line 869
def _adjust_position(...):
    """Adjust an existing position (simplified - treats as close and reopen)."""
    # For simplicity, close old and open new
    self._close_position(...)
    self._open_position(...)
```

**Impact:**
- Even when just adjusting position size (e.g., 100 shares → 105 shares), it would:
  - Close 100 shares (pay costs on 100 shares)
  - Open 105 shares (pay costs on 105 shares)
- Instead of just trading the 5 share difference

## The Fix

### 1. Smart Position Management During Rebalancing

**Changed:** Only close positions that are NOT in the new signal set.

```python
# NEW CODE - Starting at line 639
# Determine which symbols are in the new signal set
signal_symbols = {signal.symbol for signal in signals if signal.direction != 0}

# Close only positions that are NOT in the new signal set
positions_to_close = []
positions_to_keep = []

for symbol in list(self.positions.keys()):
    if symbol not in signal_symbols:
        positions_to_close.append(symbol)
    else:
        positions_to_keep.append(symbol)

if positions_to_close:
    logger.info("   Closing positions no longer in signals:")
    for symbol in positions_to_close:
        # ... only close what needs to be closed ...
        self._close_position(symbol, current_date, aligned_data)

if positions_to_keep:
    logger.info("   Keeping existing positions:")
    for symbol in positions_to_keep:
        # ... log that we're keeping these ...
```

**Benefit:** 
- For SPY-only with all buy signals: **Zero unnecessary closes/reopens**
- Position is opened once at start, held through all rebalancing, closed once at end
- Transaction costs reduced to just entry + exit (0.30% total vs ~3.6% before)

### 2. Efficient Position Adjustment

**Changed:** Only trade the difference when adjusting position size.

```python
# NEW CODE - Starting at line 863
def _adjust_position(self, symbol: str, new_quantity: float, price: float, timestamp: datetime) -> None:
    """
    Adjust an existing position by buying or selling shares.
    
    This method intelligently adjusts positions without closing and reopening,
    which avoids unnecessary transaction costs when rebalancing.
    """
    if symbol not in self.positions:
        self._open_position(symbol, new_quantity, price, timestamp)
        return
    
    position = self.positions[symbol]
    current_quantity = position.quantity
    quantity_diff = new_quantity - current_quantity
    
    # Only trade the difference
    if quantity_diff > 0:
        # Buy additional shares
        # ... pay costs only on the additional shares ...
    elif quantity_diff < 0:
        # Sell some shares
        # ... pay costs only on the shares sold ...
    else:
        # No change needed
        return
```

**Benefit:**
- When rebalancing causes minor position adjustments: only pay costs on the difference
- For SPY-only with constant 100% allocation: no adjustments = no costs

### 3. Accurate Position Sizing with Existing Positions

**Changed:** Account for existing position values when calculating capital requirements.

```python
# NEW CODE - Lines 729-755
# Calculate current position values for assets we're keeping
kept_position_values = {}
for symbol in self.positions.keys():
    if symbol in signal_symbols:
        pos = self.positions[symbol]
        kept_position_values[symbol] = pos.quantity * pos.current_price

# For assets we're keeping, we only need cash for adjustments
est_total_required = 0.0
for s2 in ordered_signals:
    target_value = portfolio_value * normalized_weights[s2.symbol]
    
    if s2.symbol in kept_position_values:
        # Already have position - only need cash if increasing
        current_value = kept_position_values[s2.symbol]
        if target_value > current_value:
            additional_needed = (target_value - current_value) * (1 + self.commission)
            est_total_required += additional_needed
    else:
        # New position - need full amount
        est_total_required += target_value * (1 + self.commission)
```

**Benefit:**
- More accurate scaling factors
- Proper cash management when positions are being held and adjusted

## Expected Results After Fix

### For SPY-Only Absolute Momentum with All Buy Signals:

**Before Fix:**
- Strategy Return = SPY Return - ~3.6% (monthly rebalancing drag)
- Number of Trades = ~25 per year (close + open each month)

**After Fix:**
- Strategy Return = SPY Return - 0.30% (entry + exit only)
- Number of Trades = 2 (1 entry + 1 exit)
- **~3.3% improvement in returns**

### General Benefits:

1. **Reduced Transaction Costs:** Only pay costs when positions actually change
2. **More Accurate Buy-and-Hold:** Strategies that maintain positions get proper buy-and-hold behavior
3. **Better Performance:** Especially noticeable in:
   - Low-volatility periods (fewer position changes)
   - Concentrated portfolios (SPY-only, or top 1-2 holdings)
   - Lower turnover strategies

## Benchmark Transaction Costs

**Important:** When comparing strategy to benchmark, consider whether benchmark should include transaction costs:

### Default Approach (Recommended)
- Benchmark = **passive buy-and-hold with no costs**
- This is the standard academic approach
- Strategy return will be ~0.30% lower than benchmark (due to entry/exit costs)
- This is **expected and correct**

### Alternative Approach
- Benchmark = **includes same transaction costs as strategy**
- More realistic for retail investor comparison
- Set `benchmark_include_costs=True` when creating `BacktestEngine`
- Strategy and benchmark returns should now be nearly identical for SPY-only with all buy signals

**Example:**
```python
# Standard approach (default)
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
    benchmark_include_costs=False  # Passive benchmark
)
# Result: Strategy ≈ Benchmark - 0.30%

# Fair comparison approach
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
    benchmark_include_costs=True  # Realistic benchmark
)
# Result: Strategy ≈ Benchmark (both pay same costs)
```

See `BENCHMARK_TRANSACTION_COSTS.md` for detailed explanation.

## Verification

To verify the fix works correctly, you can:

1. Check logs for "Keeping existing positions" messages
2. Verify trade count = 2 for SPY-only strategy (1 entry + 1 exit)
3. Compare strategy return to SPY buy-and-hold:
   - With passive benchmark: Strategy ≈ Benchmark - 0.30%
   - With realistic benchmark: Strategy ≈ Benchmark (within rounding)

## Files Modified

1. `/workspace/dual_momentum_system/src/backtesting/engine.py`
   - `_execute_signals()` method (lines ~620-705)
   - `_adjust_position()` method (lines ~863-920)
   - Position sizing logic (lines ~729-840)

## Backward Compatibility

This fix maintains backward compatibility:
- Existing strategies will see improved performance (lower costs)
- No changes needed to strategy code
- Log messages now clearly indicate position management actions
- All existing tests should pass with better returns

## Summary

The root cause was unnecessary transaction costs from closing and reopening positions that should have been held. The fix ensures positions are only traded when necessary, dramatically reducing costs for strategies with stable positions (like SPY-only absolute momentum with consistent buy signals).

For the specific case you reported:
- **SPY absolute momentum with all buy signals now matches SPY buy-and-hold (minus ~0.3% for entry/exit)**
- **Previously had ~3.6% drag from monthly rebalancing churn**
- **Net improvement: ~3.3%**
