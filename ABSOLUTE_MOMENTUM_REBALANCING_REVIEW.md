# Absolute Momentum Strategy - Rebalancing Logic Review

**Date:** 2025-10-18  
**Reviewer:** AI Assistant  
**Branch:** cursor/review-absolute-momentum-rebalancing-logic-6260

---

## Executive Summary

The absolute momentum strategy implements a time-series momentum approach with configurable rebalancing frequencies. The rebalancing logic is functional but has several areas for improvement around edge cases, transaction cost awareness, and flexibility. This review walks through the current implementation, identifies issues, and provides actionable recommendations.

---

## Current Implementation Walkthrough

### 1. Strategy Configuration (`absolute_momentum.py`)

**Location:** `dual_momentum_system/src/strategies/absolute_momentum.py`

The strategy accepts the following rebalancing-related configuration:

```python
default_config = {
    'lookback_period': 252,           # Days for momentum calculation
    'threshold': 0.0,                  # Minimum momentum to invest
    'rebalance_frequency': 'monthly',  # How often to rebalance
    'safe_asset': None,                # Safe asset when momentum negative
    'use_moving_average': False,       # Use MA crossover
    'fast_ma': 50,                     # Fast MA period
    'slow_ma': 200,                    # Slow MA period
}
```

**Key Methods:**

1. **`calculate_momentum()`** (lines 68-119)
   - Calculates either simple momentum (pct_change) or MA crossover signal
   - Returns time series of momentum scores
   
2. **`generate_signals()`** (lines 121-262)
   - Generates trading signals based on momentum
   - Returns Signal objects with direction, strength, and metadata
   - **Issue:** Signal strength calculation is somewhat arbitrary (line 170):
     ```python
     strength = min(1.0, max(0.0, momentum / (self.threshold + 0.1)))
     ```
     The `+0.1` magic number could cause issues with different threshold values

### 2. Rebalancing Logic (`base_strategy.py`)

**Location:** `dual_momentum_system/src/core/base_strategy.py` (lines 323-352)

```python
def should_rebalance(self, current_date: pd.Timestamp, last_rebalance: pd.Timestamp) -> bool:
    frequency = self.get_rebalance_frequency()
    
    if frequency == 'daily':
        return True
    elif frequency == 'weekly':
        return current_date.week != last_rebalance.week  # ⚠️ ISSUE: Week boundary problem
    elif frequency == 'monthly':
        return current_date.month != last_rebalance.month
    elif frequency == 'quarterly':
        return current_date.quarter != last_rebalance.quarter
    elif frequency == 'yearly':
        return current_date.year != last_rebalance.year
    else:
        return False
```

**Issues Identified:**

1. **Week Boundary Problem:** The `.week` property can cause issues at year boundaries
   - Week 52 of 2023 vs Week 1 of 2024 would trigger rebalance
   - But consecutive weeks within same year wouldn't if same week number
   
2. **No Timezone Handling:** Assumes timestamps are compatible
   
3. **No Day-of-Week Control:** Can't specify "rebalance on first Monday"
   
4. **Binary Decision:** No consideration of transaction costs or signal changes

### 3. Backtest Engine Integration (`engine.py`)

**Location:** `dual_momentum_system/src/backtesting/engine.py` (lines 156-255)

The main backtest loop implements rebalancing as follows:

```python
for i, current_date in enumerate(date_index):
    # Update positions and portfolio value...
    
    # Check if we should rebalance
    should_rebalance = (
        last_rebalance is None or
        strategy.should_rebalance(current_date, last_rebalance)
    )
    
    if should_rebalance and i >= strategy.get_required_history():
        # Additional check: verify sufficient data
        sufficient_data = True
        for symbol, df in aligned_data.items():
            date_loc = df.index.get_loc(current_date)
            if date_loc < required_history:
                sufficient_data = False
                break
        
        if not sufficient_data:
            continue  # Skip rebalancing
        
        # Generate signals and execute trades
        current_price_data = self._get_current_data(...)
        signals = strategy.generate_signals(current_price_data)
        self._execute_signals(signals, ...)
        
        last_rebalance = current_date
```

**Strengths:**
- ✅ Properly checks for sufficient historical data
- ✅ Detailed logging of rebalancing activity
- ✅ Handles position closing for symbols not in new signals

**Issues:**

1. **No Signal Change Threshold:** Rebalances even if signals haven't changed materially
2. **No Transaction Cost Filter:** Doesn't consider if costs outweigh benefits
3. **All-or-Nothing:** Either full rebalance or no rebalance (no partial adjustments)
4. **Position Sizing Edge Cases:** Can have cash management issues (see lines 473-497)

### 4. Position Execution (`engine.py`)

**Location:** `dual_momentum_system/src/backtesting/engine.py` (lines 402-521)

The `_execute_signals()` method handles trade execution:

```python
# Calculate position size
if risk_manager:
    position_size_dollars = risk_manager.calculate_position_size(...)
else:
    # Simple equal weight
    target_pct = signal.strength / len(signals)
    position_size_dollars = portfolio_value * target_pct
```

**Issues:**

1. **Equal Weighting Assumption:** Without risk manager, uses equal weighting
2. **Signal Strength Division:** Dividing by `len(signals)` assumes all signals have strength=1.0
3. **No Minimum Trade Size:** Can create tiny positions
4. **Rounding Issues:** Doesn't round shares to lot sizes
5. **Cash Buffer:** No reserved cash buffer for emergencies

---

## Detailed Issues & Recommended Improvements

### Issue #1: Week Rebalancing Logic Bug

**Problem:**
```python
return current_date.week != last_rebalance.week
```

This fails at year boundaries and doesn't handle ISO week numbering correctly.

**Example Failure Case:**
- Last rebalance: December 28, 2023 (Week 52)
- Current date: January 1, 2024 (Week 1)
- Result: Rebalances (correct)

But also:
- Last rebalance: January 1, 2024 (Week 1)
- Current date: January 7, 2024 (Week 1)  
- Result: Does NOT rebalance (incorrect if 7 days passed)

**Recommended Fix:**

```python
def should_rebalance(self, current_date: pd.Timestamp, last_rebalance: pd.Timestamp) -> bool:
    """
    Determine if portfolio should be rebalanced.
    
    Args:
        current_date: Current date
        last_rebalance: Date of last rebalance
    
    Returns:
        True if should rebalance, False otherwise
    """
    frequency = self.get_rebalance_frequency()
    
    if frequency == 'daily':
        return True
    
    elif frequency == 'weekly':
        # Use timedelta to check if 7+ days passed
        days_since_rebalance = (current_date - last_rebalance).days
        return days_since_rebalance >= 7
    
    elif frequency == 'monthly':
        # Check if we're in a different month OR if month rolled over
        return (current_date.year != last_rebalance.year or 
                current_date.month != last_rebalance.month)
    
    elif frequency == 'quarterly':
        # More explicit quarterly check
        return (current_date.year != last_rebalance.year or 
                current_date.quarter != last_rebalance.quarter)
    
    elif frequency == 'yearly':
        return current_date.year != last_rebalance.year
    
    else:
        # Handle custom frequencies (e.g., '14D', '2M')
        return self._check_custom_frequency(current_date, last_rebalance, frequency)

def _check_custom_frequency(self, current_date: pd.Timestamp, 
                            last_rebalance: pd.Timestamp, frequency: str) -> bool:
    """
    Handle custom frequency strings like '7D', '2W', '3M', etc.
    """
    try:
        delta = current_date - last_rebalance
        freq_offset = pd.tseries.frequencies.to_offset(frequency)
        return delta >= freq_offset
    except Exception:
        # Fall back to monthly if can't parse
        logger.warning(f"Unknown frequency '{frequency}', defaulting to monthly")
        return current_date.month != last_rebalance.month
```

### Issue #2: No Signal Change Threshold

**Problem:** Strategy rebalances even if signals are nearly identical, incurring unnecessary transaction costs.

**Example:**
- Previous signal: SPY with strength 0.85
- New signal: SPY with strength 0.86
- Result: Sells entire position, buys back (incurs 2x commission + 2x slippage)

**Recommended Solution:** Add a signal change threshold

```python
def should_rebalance(self, current_date: pd.Timestamp, last_rebalance: pd.Timestamp,
                    current_signals: Optional[List[Signal]] = None,
                    previous_signals: Optional[List[Signal]] = None) -> bool:
    """Enhanced rebalancing logic with signal change awareness."""
    
    # First check time-based rebalancing
    time_to_rebalance = self._check_time_frequency(current_date, last_rebalance)
    
    if not time_to_rebalance:
        return False
    
    # If no previous signals, definitely rebalance
    if not previous_signals:
        return True
    
    # Check if signals have changed materially
    if current_signals:
        signal_change_threshold = self.config.get('signal_change_threshold', 0.1)
        signals_changed = self._signals_changed_materially(
            current_signals, 
            previous_signals,
            signal_change_threshold
        )
        
        # Don't rebalance if signals haven't changed enough
        if not signals_changed:
            logger.info(f"Skipping rebalance - signals changed less than {signal_change_threshold:.1%}")
            return False
    
    return True

def _signals_changed_materially(self, current: List[Signal], 
                               previous: List[Signal],
                               threshold: float) -> bool:
    """
    Check if signals have changed enough to warrant rebalancing.
    
    Returns True if:
    - Different symbols are being signaled
    - Signal strengths changed by more than threshold
    - Direction changed for any symbol
    """
    # Convert to dicts for easier comparison
    current_dict = {s.symbol: (s.direction, s.strength) for s in current}
    previous_dict = {s.symbol: (s.direction, s.strength) for s in previous}
    
    # Check if symbols changed
    if set(current_dict.keys()) != set(previous_dict.keys()):
        return True
    
    # Check if directions or strengths changed materially
    for symbol, (curr_dir, curr_strength) in current_dict.items():
        prev_dir, prev_strength = previous_dict[symbol]
        
        # Direction changed
        if curr_dir != prev_dir:
            return True
        
        # Strength changed materially
        if abs(curr_strength - prev_strength) > threshold:
            return True
    
    return False
```

### Issue #3: Signal Strength Calculation

**Problem:** The signal strength calculation has a magic number:

```python
strength = min(1.0, max(0.0, momentum / (self.threshold + 0.1)))
```

This `+0.1` causes issues:
- If threshold is 0.0, strength saturates at 10% momentum
- If threshold is 0.5, it saturates at 60% momentum
- Inconsistent scaling across different threshold values

**Recommended Fix:**

```python
def _calculate_signal_strength(self, momentum: float) -> float:
    """
    Calculate signal strength from momentum score.
    
    Multiple options supported via config:
    - 'binary': Return 1.0 or 0.0 based on threshold
    - 'linear': Linear scaling from threshold to threshold + scale_range
    - 'rank': Use percentile rank of momentum
    """
    strength_method = self.config.get('strength_method', 'linear')
    
    if strength_method == 'binary':
        # Simple binary: either in or out
        return 1.0 if momentum > self.threshold else 0.0
    
    elif strength_method == 'linear':
        # Linear scaling over a range
        scale_range = self.config.get('strength_scale_range', 0.5)
        # Scale from threshold to threshold + scale_range
        if momentum <= self.threshold:
            return 0.0
        elif momentum >= self.threshold + scale_range:
            return 1.0
        else:
            return (momentum - self.threshold) / scale_range
    
    elif strength_method == 'rank':
        # Would need historical distribution - more complex
        # For now, use linear as fallback
        logger.warning("Rank-based strength not yet implemented, using linear")
        return self._calculate_signal_strength_linear(momentum)
    
    else:
        # Default to linear
        return self._calculate_signal_strength_linear(momentum)
```

### Issue #4: Position Sizing Without Risk Manager

**Problem:** Equal weighting by dividing by signal count assumes uniform strengths:

```python
target_pct = signal.strength / len(signals)
position_size_dollars = portfolio_value * target_pct
```

If one signal has strength 0.5 and another has strength 1.0, they get equal weight.

**Recommended Fix:**

```python
# Calculate total signal strength
total_strength = sum(s.strength for s in signals)

# Weight by relative strength
for signal in signals:
    # Proportional to signal strength
    target_pct = signal.strength / total_strength if total_strength > 0 else (1.0 / len(signals))
    position_size_dollars = portfolio_value * target_pct
    
    # Apply maximum position size limit
    max_position_pct = self.config.get('max_position_size', 1.0)
    position_size_dollars = min(position_size_dollars, portfolio_value * max_position_pct)
```

### Issue #5: No Minimum Trade Size or Rounding

**Problem:** Can create positions worth $1 or fractional shares (for stocks).

**Recommended Fix:**

```python
def _execute_signals(self, signals, current_date, aligned_data, portfolio_value, risk_manager):
    """Execute trading signals with proper size controls."""
    
    # Get configuration
    min_trade_value = self.config.get('min_trade_value', 100)  # Minimum $100 per trade
    round_to_lots = self.config.get('round_to_lots', False)
    lot_size = self.config.get('lot_size', 100)  # Standard lot = 100 shares
    
    for signal in signals:
        # ... calculate position_size_dollars ...
        
        # Skip if too small
        if position_size_dollars < min_trade_value:
            logger.info(f"Skipping {signal.symbol} - position size ${position_size_dollars:.2f} "
                       f"below minimum ${min_trade_value}")
            continue
        
        # Calculate shares
        shares = position_size_dollars / execution_price
        
        # Round to lots if configured
        if round_to_lots and lot_size > 0:
            shares = round(shares / lot_size) * lot_size
            
            # Recalculate position size after rounding
            position_size_dollars = shares * execution_price
            
            # Check if still above minimum after rounding
            if shares == 0 or position_size_dollars < min_trade_value:
                logger.info(f"Skipping {signal.symbol} - rounded to zero lots")
                continue
        
        # ... execute trade ...
```

### Issue #6: No Rebalancing on Specific Day of Period

**Problem:** Can't control which day of the month/week to rebalance on.

Users might want:
- "Last trading day of month"
- "First Monday of month"
- "Third Friday" (for options expiry)

**Recommended Enhancement:**

```python
def get_rebalance_day_of_period(self) -> Optional[str]:
    """
    Get specific day within period to rebalance.
    
    Examples:
    - 'first_day': First trading day of period
    - 'last_day': Last trading day of period
    - 'monday': First Monday of period
    - 'friday': Third Friday (options expiry)
    - None: Any day in new period
    """
    return self.config.get('rebalance_day_of_period', None)

def should_rebalance(self, current_date: pd.Timestamp, last_rebalance: pd.Timestamp,
                    trading_calendar: Optional[pd.DatetimeIndex] = None) -> bool:
    """Enhanced with day-of-period control."""
    
    # Check if we're in a new period
    in_new_period = self._check_time_frequency(current_date, last_rebalance)
    
    if not in_new_period:
        return False
    
    # Check if we're on the right day of the period
    rebal_day = self.get_rebalance_day_of_period()
    
    if rebal_day is None:
        return True  # Rebalance any day in new period
    
    if rebal_day == 'first_day':
        # Check if this is the first trading day of the period
        return self._is_first_trading_day_of_period(current_date, trading_calendar)
    
    elif rebal_day == 'last_day':
        # Check if this is the last trading day of the period
        return self._is_last_trading_day_of_period(current_date, trading_calendar)
    
    elif rebal_day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        # Check if this is the specified day of week
        target_weekday = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].index(rebal_day)
        return current_date.weekday() == target_weekday
    
    return True  # Default to yes if can't determine
```

### Issue #7: No Transaction Cost Awareness in Rebalancing Decision

**Problem:** Doesn't estimate transaction costs before deciding to rebalance.

**Recommended Enhancement:**

```python
def should_rebalance(self, current_date, last_rebalance, 
                    current_signals, previous_signals,
                    current_positions, portfolio_value) -> tuple[bool, dict]:
    """
    Enhanced rebalancing logic with cost awareness.
    
    Returns:
        Tuple of (should_rebalance: bool, reason: dict)
    """
    reasons = {}
    
    # Time check
    if not self._check_time_frequency(current_date, last_rebalance):
        return False, {'reason': 'not_time_yet'}
    
    # Estimate transaction costs
    estimated_costs = self._estimate_rebalance_costs(
        current_signals, 
        previous_signals,
        current_positions,
        portfolio_value
    )
    
    # Check if costs are worth it
    max_rebalance_cost_pct = self.config.get('max_rebalance_cost_pct', 0.02)  # 2% max
    
    if estimated_costs['total_pct'] > max_rebalance_cost_pct:
        reasons['reason'] = 'costs_too_high'
        reasons['estimated_cost_pct'] = estimated_costs['total_pct']
        reasons['max_allowed_pct'] = max_rebalance_cost_pct
        
        # Only rebalance if signals changed dramatically
        force_rebalance_threshold = self.config.get('force_rebalance_threshold', 0.3)
        if not self._signals_changed_materially(current_signals, previous_signals, 
                                               force_rebalance_threshold):
            return False, reasons
    
    return True, {'reason': 'time_and_conditions_met', 'estimated_costs': estimated_costs}

def _estimate_rebalance_costs(self, current_signals, previous_signals, 
                              current_positions, portfolio_value) -> dict:
    """
    Estimate transaction costs for rebalancing.
    
    Returns:
        Dict with 'total_cost', 'total_pct', 'commission', 'slippage'
    """
    commission_rate = self.config.get('commission', 0.001)
    slippage_rate = self.config.get('slippage', 0.0005)
    
    # Calculate what trades would be needed
    target_positions = self._calculate_target_positions(current_signals, portfolio_value)
    
    total_turnover = 0.0
    
    # Calculate sells
    for symbol, position in current_positions.items():
        if symbol not in target_positions:
            total_turnover += abs(position.quantity * position.current_price)
    
    # Calculate buys and adjustments
    for symbol, target_value in target_positions.items():
        if symbol in current_positions:
            current_value = current_positions[symbol].quantity * current_positions[symbol].current_price
            total_turnover += abs(target_value - current_value)
        else:
            total_turnover += target_value
    
    # One-sided turnover (since we count both buy and sell)
    one_sided_turnover = total_turnover / 2
    
    commission_cost = one_sided_turnover * commission_rate
    slippage_cost = one_sided_turnover * slippage_rate
    total_cost = commission_cost + slippage_cost
    
    return {
        'total_cost': total_cost,
        'total_pct': total_cost / portfolio_value if portfolio_value > 0 else 0,
        'commission': commission_cost,
        'slippage': slippage_cost,
        'turnover': one_sided_turnover,
        'turnover_pct': one_sided_turnover / portfolio_value if portfolio_value > 0 else 0
    }
```

---

## Additional Improvements

### 1. Add Rebalancing History Tracking

Track rebalancing decisions for analysis:

```python
class RebalanceEvent:
    """Record of a rebalancing event."""
    timestamp: datetime
    portfolio_value: float
    signals: List[Signal]
    positions_before: Dict[str, Position]
    positions_after: Dict[str, Position]
    transaction_costs: float
    reason: str
    skipped: bool

# In strategy or engine
self.rebalance_history: List[RebalanceEvent] = []
```

### 2. Support Partial Rebalancing

Instead of all-or-nothing, allow gradual adjustment:

```python
def get_rebalance_aggressiveness(self) -> float:
    """
    How aggressively to rebalance toward target weights.
    
    Returns:
        Value between 0.0 and 1.0
        - 1.0: Full rebalance to target (default)
        - 0.5: Move halfway to target
        - 0.0: Don't rebalance
    """
    return self.config.get('rebalance_aggressiveness', 1.0)

# When calculating target positions
actual_position = current_position + (target_position - current_position) * aggressiveness
```

### 3. Add Drift-Based Rebalancing

Rebalance when positions drift too far from target:

```python
def check_drift_rebalancing(self, current_positions, target_weights, 
                           portfolio_value) -> bool:
    """
    Check if any position has drifted beyond threshold.
    
    Returns True if any position is off by more than drift_threshold.
    """
    drift_threshold = self.config.get('drift_threshold', 0.05)  # 5% drift
    
    for symbol, target_weight in target_weights.items():
        if symbol in current_positions:
            current_value = current_positions[symbol].quantity * current_positions[symbol].current_price
            current_weight = current_value / portfolio_value
            
            drift = abs(current_weight - target_weight)
            if drift > drift_threshold:
                logger.info(f"{symbol} drifted {drift:.1%} from target "
                          f"(current: {current_weight:.1%}, target: {target_weight:.1%})")
                return True
    
    return False
```

### 4. Add Rebalancing Tolerance Bands

Similar to drift but with asymmetric bands:

```python
def use_tolerance_bands(self) -> bool:
    """
    Use tolerance bands instead of exact rebalancing.
    
    Only rebalance if outside bands like [target - lower, target + upper].
    Reduces unnecessary trading.
    """
    return self.config.get('use_tolerance_bands', False)

def get_tolerance_bands(self) -> tuple[float, float]:
    """
    Get lower and upper tolerance bands.
    
    Returns:
        (lower_band, upper_band) as percentages
        Example: (0.02, 0.02) means ±2% around target
    """
    lower = self.config.get('tolerance_band_lower', 0.02)
    upper = self.config.get('tolerance_band_upper', 0.02)
    return (lower, upper)
```

### 5. Add Tax-Loss Harvesting Awareness

Don't rebalance positions with short-term gains unless necessary:

```python
def avoid_short_term_gains(self) -> bool:
    """Whether to avoid realizing short-term capital gains."""
    return self.config.get('avoid_short_term_gains', False)

def get_short_term_period(self) -> int:
    """Days to hold before gain becomes long-term (365 in US)."""
    return self.config.get('short_term_period_days', 365)

def should_close_position(self, position: Position, current_date: datetime) -> bool:
    """
    Determine if position should be closed considering tax implications.
    """
    if not self.avoid_short_term_gains():
        return True  # No tax concerns
    
    holding_period = (current_date - position.entry_timestamp).days
    
    # If position has gain and is short-term, be reluctant to close
    if holding_period < self.get_short_term_period():
        if position.current_price > position.entry_price:
            # Only close if really necessary (strong signal change)
            return self.config.get('force_close_short_term_gains', False)
    
    return True
```

---

## Implementation Priority

### Critical (Must Fix)
1. ✅ **Fix weekly rebalancing logic** - Current implementation is buggy
2. ✅ **Fix signal strength calculation** - Remove magic number, make configurable
3. ✅ **Fix position sizing without risk manager** - Use strength-weighted allocation

### High Priority (Should Fix Soon)
4. ✅ **Add signal change threshold** - Reduce unnecessary rebalancing
5. ✅ **Add minimum trade size** - Prevent micro-positions
6. ✅ **Add lot size rounding** - For stocks that trade in lots
7. ✅ **Add transaction cost estimation** - Make rebalancing cost-aware

### Medium Priority (Nice to Have)
8. ⚪ **Add rebalancing day-of-period control** - For month-end, etc.
9. ⚪ **Add partial rebalancing** - Gradual adjustment option
10. ⚪ **Add drift-based rebalancing** - Rebalance on drift, not just time
11. ⚪ **Track rebalancing history** - For analysis

### Low Priority (Future Enhancement)
12. ⚪ **Add tax-loss harvesting** - US-specific optimization
13. ⚪ **Add tolerance bands** - Alternative to exact rebalancing
14. ⚪ **Add custom frequency support** - '14D', '2M', etc.

---

## Configuration Schema Updates

Suggested additions to strategy configuration:

```yaml
# Absolute Momentum Strategy Configuration

# === Existing Parameters ===
lookback_period: 252
threshold: 0.0
rebalance_frequency: monthly
safe_asset: SHY

# === NEW: Signal Strength Configuration ===
strength_method: linear  # Options: binary, linear, rank
strength_scale_range: 0.5  # For linear method: scale from threshold to threshold + range

# === NEW: Rebalancing Controls ===
rebalance_day_of_period: null  # Options: null, first_day, last_day, monday, etc.
signal_change_threshold: 0.1  # Minimum signal change to trigger rebalance (10%)
max_rebalance_cost_pct: 0.02  # Maximum cost as % of portfolio (2%)
force_rebalance_threshold: 0.3  # Force rebalance if signals change this much (30%)

# === NEW: Position Sizing Controls ===
min_trade_value: 100  # Minimum $100 per trade
max_position_size: 1.0  # Maximum 100% in single position
round_to_lots: false  # Round to lot sizes (for stocks)
lot_size: 100  # Standard lot size

# === NEW: Advanced Rebalancing ===
use_tolerance_bands: false  # Use bands instead of exact rebalancing
tolerance_band_lower: 0.02  # Lower band (2%)
tolerance_band_upper: 0.02  # Upper band (2%)
rebalance_aggressiveness: 1.0  # 1.0 = full rebalance, 0.5 = halfway
check_drift: false  # Also rebalance on position drift
drift_threshold: 0.05  # Drift threshold (5%)

# === NEW: Tax Optimization ===
avoid_short_term_gains: false  # Avoid realizing short-term gains
short_term_period_days: 365  # US: 365 days for long-term status
force_close_short_term_gains: false  # Force close even with short-term gains

# === NEW: Cash Management ===
reserve_cash_pct: 0.02  # Keep 2% in cash
target_cash_buffer: 1000  # Target $1000 minimum cash
```

---

## Testing Recommendations

### Unit Tests Needed

1. **Test weekly rebalancing across year boundary**
   ```python
   def test_weekly_rebalance_year_boundary():
       strategy = AbsoluteMomentumStrategy({'rebalance_frequency': 'weekly'})
       last_rebal = pd.Timestamp('2023-12-28')  # Thursday, Week 52
       current = pd.Timestamp('2024-01-04')  # Thursday, Week 1
       assert strategy.should_rebalance(current, last_rebal) == True
   ```

2. **Test signal change threshold**
   ```python
   def test_signal_change_threshold():
       # Test that small signal changes don't trigger rebalance
       # Test that large signal changes do trigger rebalance
   ```

3. **Test minimum trade size filtering**
   ```python
   def test_minimum_trade_size():
       # Test that positions below minimum are skipped
   ```

4. **Test transaction cost estimation**
   ```python
   def test_transaction_cost_estimation():
       # Test cost calculation is accurate
       # Test rebalancing is skipped if costs too high
   ```

### Integration Tests Needed

1. **Test full rebalancing cycle** with various frequencies
2. **Test rebalancing with insufficient cash**
3. **Test rebalancing with different position counts**
4. **Test rebalancing day-of-period logic**

### Backtests for Validation

Run comparative backtests with:
1. Current implementation
2. Fixed implementation
3. Implementation with signal change threshold
4. Implementation with transaction cost awareness

Expected findings:
- Fixed version should perform similarly in most cases
- Signal change threshold should reduce turnover
- Cost awareness should improve risk-adjusted returns

---

## Summary of Key Recommendations

### Immediate Actions

1. **Fix the weekly rebalancing bug** using timedelta instead of `.week` property
2. **Make signal strength calculation configurable** with proper scaling
3. **Fix position sizing** to use strength-weighted allocation
4. **Add minimum trade size** to prevent micro-positions

### Short-Term Improvements

5. **Add signal change threshold** to reduce unnecessary rebalancing
6. **Add transaction cost estimation** to make informed rebalancing decisions
7. **Add configuration schema** for new parameters
8. **Add comprehensive tests** for edge cases

### Long-Term Enhancements

9. **Support flexible rebalancing schedules** (specific days, custom frequencies)
10. **Add drift-based rebalancing** as alternative/supplement to time-based
11. **Add partial rebalancing** for more gradual adjustments
12. **Add tax optimization** for taxable accounts (US-specific)

---

## Code Examples

Complete implementation examples for all recommendations are provided in the sections above. Key files to modify:

1. **`src/core/base_strategy.py`** - Core rebalancing logic
2. **`src/strategies/absolute_momentum.py`** - Signal strength calculation
3. **`src/backtesting/engine.py`** - Position sizing and execution
4. **`config/strategies/*.yaml`** - Configuration schema

---

## Questions for Discussion

1. **Priority:** Which improvements should we tackle first?
2. **Backwards Compatibility:** Should we maintain backwards compatibility with existing configs?
3. **Default Values:** What should defaults be for new parameters?
4. **Testing:** Do we have historical data to validate improvements?
5. **Documentation:** Should we create user guide for rebalancing options?

---

**End of Review**
