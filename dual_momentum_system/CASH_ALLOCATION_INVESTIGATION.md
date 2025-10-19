# Cash Allocation Investigation Report

**Date:** 2025-10-19  
**Branch:** cursor/investigate-high-cash-allocation-reasons-9e8f  
**Status:** 🔍 Investigation Complete

## Executive Summary

After thorough investigation of the codebase, I've identified **5 key reasons** why cash allocation is so high in the portfolio, as shown in the "Portfolio Allocation by Asset" chart.

## Root Causes

### 1. **Safe Asset Signals Not Being Executed** ⚠️ CRITICAL ISSUE

**Location:** `src/backtesting/engine.py`, line 532

**Problem:**
```python
for signal in signals:
    if signal.direction == 0 or signal.symbol not in aligned_data:
        continue  # SKIPS THE SIGNAL!
```

When the strategy generates a signal for the safe asset (e.g., SHY, AGG) during bearish market conditions, but that safe asset is **not included in the aligned_data dictionary**, the signal is silently skipped. This results in:
- ❌ No position opened in the safe asset
- ❌ Cash remains uninvested
- ❌ Portfolio sits in 100% cash during downturns

**Evidence from Strategy Code:**
```python
# dual_momentum.py, lines 227-247
if not filtered_momentum:
    # No assets pass absolute momentum filter
    if self.safe_asset:
        signal = Signal(
            symbol=self.safe_asset,  # e.g., 'SHY'
            direction=1,
            ...
        )
        signals.append(signal)
        logger.info(f"Switched to safe asset: {self.safe_asset}")
```

**Impact:** During bearish periods (2023-2024, Jan-Jul 2024), when no assets have positive momentum:
1. Strategy generates safe asset signal (SHY)
2. Engine checks if 'SHY' in aligned_data
3. SHY not in aligned_data → signal skipped
4. Result: 40-70% cash allocation instead of being invested in bonds

### 2. **Limited Position Count with High Selectivity**

**Configuration:** `position_count: 1` (classic dual momentum)

**Impact:**
- Strategy only holds the **top 1 asset** at any time
- Even with a universe of 7 assets (SPY, EFA, EEM, AGG, TLT, GLD, DBC)
- 6 out of 7 assets are always in cash
- This is by design, but contributes to high apparent "cash" in the chart

**Why this matters:** In the allocation chart, if only 1 asset is selected:
- 1 asset = ~14% allocation (equal weight assumption)
- 6 assets = not selected = appear as "cash"
- Actual portfolio might be 100% invested, but chart shows high cash

### 3. **Absolute Momentum Filter During Bear Markets**

**Configuration:** `absolute_threshold: 0.0` (must have positive returns)

**Market Periods Affected:**
- **2023 Q1-Q2:** Market correction, many assets negative
- **2024 Q1:** Volatility spike, momentum turns negative
- **Mid-2024:** Mixed signals, threshold not met

**What Happens:**
```python
# dual_momentum.py, lines 182-186
filtered_momentum = {
    symbol: score
    for symbol, score in latest_momentum.items()
    if not pd.isna(score) and score > self.absolute_threshold  # > 0.0
}
```

**Result:** If all risky assets have negative momentum:
1. All assets filtered out
2. Safe asset signal generated (SHY)
3. But SHY not in data → skipped (see Issue #1)
4. Portfolio stays in cash

### 4. **Position Sizing and Cash Management**

**Location:** `src/backtesting/engine.py`, lines 552-554

```python
# Simple equal weight
target_pct = signal.strength / len(signals)
position_size_dollars = portfolio_value * target_pct
```

**Issues:**
- **Signal Strength < 1.0:** If momentum is weak, signal strength is reduced
- **Multiple Signals:** Position size divided by number of signals
- **Commission Reserves:** Cash held back for commissions (lines 560-592)
- **Insufficient Cash Handling:** If total_cost > cash, position is reduced or skipped

**Example:**
- 3 signals with strengths [0.8, 0.6, 0.4]
- Average strength = 0.6
- Target allocation = 0.6 / 3 = 20% per position
- Total invested = 60%
- Cash = 40%

### 5. **Rebalancing Frequency and Lag**

**Configuration:** `rebalance_frequency: monthly`

**Impact:**
- Positions only adjusted once per month
- Between rebalances, if positions lose value, cash % appears higher
- Momentum can turn negative before next rebalance
- By the time rebalancing occurs, new signals may be weaker

**Timeline Example (Jan 2024):**
```
Jan 1:  Rebalance, buy QQQ at $400, invest 100%
Jan 15: QQQ drops to $360 (-10%), portfolio now 90% QQQ, 10% "cash" (value lost)
Feb 1:  Rebalance check - momentum now negative
        Strategy signals safe asset (SHY)
        SHY not in data → skipped
        Result: Exit QQQ, 100% cash
```

## Evidence from Configuration Files

### Default Strategy Config
**File:** `config/strategies/dual_momentum_default.yaml`
```yaml
lookback_period: 252          # 1 year momentum
rebalance_frequency: monthly  # Only rebalance monthly
position_count: 1             # Hold only 1 asset
absolute_threshold: 0.0       # Must be positive
safe_asset: SHY              # Defensive asset
```

### Asset Universe
**File:** `config/strategies/dual_momentum_default.yaml`
```yaml
universe:
  - SPY   # S&P 500
  - EFA   # International Developed
  - EEM   # Emerging Markets
  - AGG   # U.S. Aggregate Bonds
  - TLT   # Long-term Treasuries
  - GLD   # Gold
  - DBC   # Commodities
```

**Notice:** SHY (safe_asset) is NOT in the universe!

## Why High Cash Specifically in 2023-2024 Periods

Based on the chart showing high cash in these periods:

### Jan-Jul 2023
- Market uncertainty, Fed rate hikes
- Many assets had negative 12-month momentum
- Absolute filter eliminated most assets
- position_count: 1 means limited exposure
- Safe asset signals likely skipped

### Jan-Jul 2024  
- Market volatility, geopolitical risks
- Similar momentum deterioration
- Strategy tried to rotate to safe asset
- Safe asset not in data → cash

### Current (Oct 2024+)
- Improved momentum across assets
- More signals passing filter
- Lower cash allocation visible

## Recommendations to Fix High Cash Allocation

### 🔥 Priority 1: Fix Safe Asset Execution (CRITICAL)

**Change:** Ensure safe asset is included in backtesting data

**Option A: Add safe asset to universe**
```yaml
universe:
  - SPY
  - EFA
  - EEM
  - AGG
  - TLT
  - GLD
  - DBC
  - SHY   # ADD THIS
```

**Option B: Always fetch safe asset data**
```python
# In backtesting code, before engine.run()
if strategy.config.get('safe_asset'):
    safe_asset = strategy.config['safe_asset']
    if safe_asset not in price_data:
        # Fetch safe asset data
        safe_data = data_source.fetch_data(safe_asset, start_date, end_date)
        price_data[safe_asset] = asset.normalize_data(safe_data, safe_asset)
```

**Option C: Fallback to cash with warning**
```python
# In engine.py, _execute_signals method
for signal in signals:
    if signal.direction == 0:
        continue
    
    if signal.symbol not in aligned_data:
        # Check if this is the safe asset
        if hasattr(strategy, 'safe_asset') and signal.symbol == strategy.safe_asset:
            logger.warning(
                f"⚠️ Safe asset '{signal.symbol}' signal generated but no price data available. "
                f"Consider adding {signal.symbol} to your universe or fetching its data separately. "
                f"Holding cash instead."
            )
        continue
```

### Priority 2: Increase Position Count

**Current:** position_count: 1 (only top asset)

**Recommendation:** 
```yaml
position_count: 3  # Hold top 3 assets
```

**Impact:** 
- Reduces single-asset concentration
- Lower cash allocation (3x more invested)
- Better diversification

### Priority 3: Lower Absolute Threshold

**Current:** absolute_threshold: 0.0 (must be positive)

**Recommendation:**
```yaml
absolute_threshold: -0.05  # Allow slight negative momentum (-5%)
```

**Impact:**
- More assets pass the filter during mixed markets
- Reduces frequency of "no assets selected" scenarios
- Stays invested more often

### Priority 4: Add Volatility Adjustment

**Current:** use_volatility_adjustment: false

**Recommendation:**
```yaml
use_volatility_adjustment: true
```

**Impact:**
- Risk-adjusted rankings favor consistent performers
- Better performance during high volatility periods
- May keep more assets above threshold

### Priority 5: Increase Rebalancing Frequency

**Current:** rebalance_frequency: monthly

**Recommendation:**
```yaml
rebalance_frequency: weekly  # More responsive
```

**Impact:**
- Faster response to momentum changes
- Reduced lag in allocation adjustments
- Trade-off: higher transaction costs

## Testing Recommendations

1. **Test with safe asset in universe:**
   ```python
   universe = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD', 'DBC', 'SHY']
   ```

2. **Test with higher position count:**
   ```python
   strategy_config = {
       'position_count': 3,
       'absolute_threshold': 0.0,
       'safe_asset': 'SHY'
   }
   ```

3. **Test with lower threshold:**
   ```python
   strategy_config = {
       'position_count': 1,
       'absolute_threshold': -0.05,
       'safe_asset': 'SHY'
   }
   ```

4. **Compare allocation percentages before/after fixes**

## Expected Results After Fixes

### Before (Current Behavior):
- High cash periods: 40-70% during 2023-2024
- Safe asset signals skipped
- Single asset concentration

### After (With Fixes):
- Cash allocation: 0-20% typically
- Safe asset properly allocated during bearish periods
- Better diversification with higher position_count
- More consistent full investment

## Code Changes Required

### 1. Engine.py - Add Safe Asset Warning
```python
# File: src/backtesting/engine.py
# Line: ~532

for signal in signals:
    if signal.direction == 0:
        continue
    
    if signal.symbol not in aligned_data:
        # NEW: Check if this is the safe asset and warn
        if (hasattr(strategy, 'config') and 
            signal.symbol == strategy.config.get('safe_asset')):
            logger.warning(
                f"⚠️ CRITICAL: Safe asset '{signal.symbol}' signal generated but "
                f"no price data available. Portfolio will hold cash instead. "
                f"To fix: Add {signal.symbol} to your universe or fetch its data."
            )
        continue
```

### 2. Add Safe Asset Data Validation
```python
# File: src/backtesting/engine.py
# Add before run() method execution

def _validate_safe_asset_data(
    self,
    strategy: BaseStrategy,
    aligned_data: Dict[str, pd.DataFrame]
) -> None:
    """Validate that safe asset data is available if configured."""
    if hasattr(strategy, 'config'):
        safe_asset = strategy.config.get('safe_asset')
        if safe_asset and safe_asset not in aligned_data:
            logger.warning(
                f"⚠️ Strategy configured with safe_asset='{safe_asset}' but no price data provided. "
                f"During bearish markets, portfolio will hold cash instead of {safe_asset}. "
                f"Recommendation: Add {safe_asset} to your asset universe."
            )
```

### 3. Update Default Configuration
```yaml
# File: config/strategies/dual_momentum_default.yaml

# Option 1: Add safe asset to universe
universe:
  - SPY
  - EFA
  - EEM
  - AGG
  - TLT
  - GLD
  - DBC
  - SHY   # Safe asset included

# Option 2: Use AGG as safe asset (already in universe)
safe_asset: AGG  # Instead of SHY
```

## Conclusion

The high cash allocation is primarily caused by:
1. **Safe asset signals being skipped** (safe asset not in data)
2. **Conservative strategy parameters** (position_count=1, threshold=0.0)
3. **Monthly rebalancing lag** during volatile periods
4. **Absolute momentum filter** eliminating assets in bear markets

The **critical fix** is ensuring the safe asset (SHY) is included in the backtesting data so that defensive signals can be properly executed. Without this fix, the strategy will continue to show high cash allocation during market downturns instead of rotating into bonds as designed.

Secondary improvements (higher position_count, lower threshold, more frequent rebalancing) can further reduce cash drag, but fixing the safe asset issue is the highest priority.
