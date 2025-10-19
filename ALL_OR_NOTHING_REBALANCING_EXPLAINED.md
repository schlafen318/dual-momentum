# "All-or-Nothing" Rebalancing Logic - Explained

## What Does "All-or-Nothing" Mean?

The current rebalancing logic is **binary**: 

```
if should_rebalance:
    ✅ Do COMPLETE rebalance (adjust to exact target weights)
else:
    ❌ Do NOTHING (keep current positions unchanged)
```

There's **no middle ground** - no way to gradually adjust positions or partially rebalance.

---

## The Code

Here's the critical part from `engine.py`:

```python
# Line 170-174: Binary decision
should_rebalance = (
    last_rebalance is None or
    strategy.should_rebalance(current_date, last_rebalance)
)

if should_rebalance:  # ← All-or-nothing starts here
    # Line 420-428: Close EVERYTHING not in new signals
    signal_symbols = {s.symbol for s in signals if s.direction != 0}
    positions_to_close = [
        symbol for symbol in self.positions.keys()
        if symbol not in signal_symbols
    ]
    
    for symbol in positions_to_close:
        self._close_position(symbol, current_date, aligned_data)
    
    # Line 430-454: Open/adjust to EXACT target weights
    for signal in signals:
        target_pct = signal.strength / len(signals)
        position_size_dollars = portfolio_value * target_pct  # ← Target weight
        # ... execute to reach exact target
```

---

## Example: The Problem in Action

### Scenario 1: Small Signal Change

**Current Portfolio (just rebalanced last month):**
- SPY: 50% ($50,000)
- QQQ: 50% ($50,000)

**New Signals (this month):**
- SPY: momentum = 10% → strength = 1.0
- QQQ: momentum = 12% → strength = 1.0

Technically the signals are the same (both 1.0), but let's say using proportional method:
- SPY: 45% target weight
- QQQ: 55% target weight

**What the current logic does (ALL-OR-NOTHING):**

```
✅ REBALANCE (time-based trigger)

Step 1: Sell positions not in signals
  → None to close (both still in signals)

Step 2: Adjust to exact targets
  → Sell $5,000 of SPY
  → Buy $5,000 of QQQ
  → Commission: ~$100 (0.1% on $10,000 turnover)
  
Result: Paid $100 to adjust a 5% drift
```

**What a "partial rebalance" could do:**

```
❓ SHOULD WE REBALANCE?
  → Drift = 5% (small)
  → Cost = $100
  → Decision: Rebalance 50% of the way

Step: Adjust halfway to target
  → Sell $2,500 of SPY (half of $5,000)
  → Buy $2,500 of QQQ
  → Commission: ~$50 (0.1% on $5,000 turnover)
  
Result: Portfolio is 47.5% SPY / 52.5% QQQ
        Saved $50 in costs, still close to target
```

---

### Scenario 2: High Transaction Costs

**Current Portfolio:**
- SPY: 100% ($100,000)

**New Signals:**
- SPY: momentum = 5% → strength = 0.5
- QQQ: momentum = 6% → strength = 0.6

Using proportional method:
- SPY: 45% target
- QQQ: 55% target

**What current logic does:**

```
✅ REBALANCE (month changed)

Sell $55,000 of SPY
Buy $55,000 of QQQ

Transaction costs:
  Commission: 0.1% × $110,000 = $110
  Slippage: 0.05% × $110,000 = $55
  Total: $165

Result: Paid $165 to chase a small momentum difference
```

**What a "cost-aware" partial rebalance could do:**

```
❓ SHOULD WE REBALANCE?
  → Signal change: SPY momentum 5% → 6% (small)
  → Estimated cost: $165 (0.165% of portfolio)
  → Decision: Only rebalance if savings > costs

Analysis:
  Expected benefit: ~0.1% from better allocation
  Transaction cost: 0.165%
  Net benefit: NEGATIVE

Decision: SKIP rebalancing this month
```

---

### Scenario 3: Weekly Rebalancing with Noise

**Strategy:** Weekly rebalancing, linear strength method

**Week 1:**
- SPY: 10% momentum → 1.0 strength → 100% allocation

**Week 2:**
- SPY: 9.5% momentum → 0.95 strength → 100% allocation (still only asset)

**Week 3:**
- SPY: 10.2% momentum → 1.0 strength → 100% allocation

**What current logic does:**

```
Week 1 → Week 2:
  ✅ REBALANCE (week changed)
  → No actual change needed (still 100% SPY)
  → BUT: System goes through full rebalancing logic
  → Generates signals, checks all positions
  → "Adjusts" to same position

Week 2 → Week 3:
  ✅ REBALANCE (week changed)
  → Again, no change needed
  → Still going through full logic
```

**What a "signal-aware" system could do:**

```
Week 1 → Week 2:
  ❓ SHOULD WE REBALANCE?
  → Time: New week ✓
  → Signal change: 0.05 (5% relative change)
  → Signal change threshold: 0.10 (10%)
  → Decision: SKIP (signals haven't changed enough)

Week 2 → Week 3:
  ❓ SHOULD WE REBALANCE?
  → Signal change: 0.05 again
  → Decision: SKIP
```

---

## Why Is This "All-or-Nothing"?

The logic has these characteristics:

### 1. Binary Rebalance Decision

```python
if should_rebalance:
    # Do EVERYTHING
else:
    # Do NOTHING
```

No concept of:
- "Rebalance 50% of the way"
- "Only rebalance if drift > X%"
- "Only rebalance if expected benefit > cost"

### 2. Complete Portfolio Reconstruction

When rebalancing:
```python
# Close everything not in new signals
for symbol in positions_to_close:
    self._close_position(...)

# Open/adjust everything in signals
for signal in signals:
    # ... go to exact target weight
```

Doesn't consider:
- Current positions vs. targets (drift amount)
- Transaction costs for each adjustment
- Whether adjustment is material

### 3. No Gradual Adjustment

Current:
```
Current: 100% SPY
Target: 100% QQQ
Action: Sell ALL SPY, buy ALL QQQ (100% turnover)
```

Could be:
```
Current: 100% SPY
Target: 100% QQQ
Action: Move 25% per month (25% turnover per month)

Month 1: 75% SPY / 25% QQQ
Month 2: 50% SPY / 50% QQQ
Month 3: 25% SPY / 75% QQQ
Month 4: 0% SPY / 100% QQQ
```

---

## Real-World Impact

### Example Backtest Comparison

**Strategy:** Absolute Momentum, monthly rebalancing, 3 assets

**Scenario A: Current (All-or-Nothing)**
```
Month 1: 33% SPY, 33% QQQ, 33% DIA
Month 2: Signals barely change
  → Still rebalances to: 34% SPY, 33% QQQ, 33% DIA
  → Turnover: 2%
  → Cost: 0.003% (commission + slippage)

Annual turnover: 24%
Annual transaction costs: 0.036%
```

**Scenario B: With Signal-Change Threshold (10%)**
```
Month 1: 33% SPY, 33% QQQ, 33% DIA
Month 2: Signals change by 1%
  → SKIP rebalancing (< 10% threshold)
  → Portfolio drifts to: 33.5% SPY, 33% QQQ, 33.5% DIA
  → Turnover: 0%
  → Cost: 0%

Month 3: Signals change by 15%
  → REBALANCE (> 10% threshold)

Annual turnover: 12% (50% reduction!)
Annual transaction costs: 0.018% (50% savings!)
```

---

## The Four "All-or-Nothing" Aspects

### 1. Time-Based Only

**Current:**
```python
if current_date.month != last_rebalance.month:
    return True  # Rebalance regardless of anything else
```

**Better:**
```python
if current_date.month != last_rebalance.month:
    if signals_changed_materially():
        return True  # Rebalance only if needed
    else:
        return False  # Skip if signals unchanged
```

### 2. Full Rebalance Always

**Current:**
```python
# Always adjust to exact target
position_size = portfolio_value * target_weight
```

**Better:**
```python
# Adjust partially based on aggressiveness
current_weight = current_position / portfolio_value
target_weight = signal.strength / total_strength
adjustment = (target_weight - current_weight) * aggressiveness
new_weight = current_weight + adjustment
```

### 3. No Cost Awareness

**Current:**
```python
# Just rebalance if it's time
if should_rebalance:
    execute_signals(...)
```

**Better:**
```python
# Estimate costs first
estimated_cost = estimate_transaction_costs(current, target)
expected_benefit = estimate_benefit_from_rebalancing(current, target)

if expected_benefit > estimated_cost:
    execute_signals(...)
else:
    logger.info("Skipping rebalance - costs exceed benefits")
```

### 4. No Tolerance Bands

**Current:**
```python
# Always go to exact target
target_weight = 0.333...
```

**Better:**
```python
# Only rebalance if outside tolerance band
target_weight = 0.333
current_weight = 0.350
tolerance = 0.02  # ±2%

if abs(current_weight - target_weight) > tolerance:
    rebalance()
else:
    # Within tolerance, skip
    pass
```

---

## Recommended Improvements

### 1. Add Signal Change Threshold (High Priority)

```python
def should_rebalance(self, current_date, last_rebalance, 
                    current_signals=None, previous_signals=None):
    # Time check
    if not self._time_to_rebalance(current_date, last_rebalance):
        return False
    
    # Signal change check
    if current_signals and previous_signals:
        threshold = self.config.get('signal_change_threshold', 0.10)
        if not self._signals_changed_enough(current_signals, previous_signals, threshold):
            logger.info(f"Skipping rebalance - signals changed < {threshold:.0%}")
            return False
    
    return True
```

### 2. Add Partial Rebalancing (Medium Priority)

```python
def calculate_target_adjustment(self, current_position, target_position):
    aggressiveness = self.config.get('rebalance_aggressiveness', 1.0)
    # 1.0 = full rebalance, 0.5 = move halfway, 0.0 = don't move
    
    adjustment = (target_position - current_position) * aggressiveness
    return current_position + adjustment
```

### 3. Add Cost Estimation (Medium Priority)

```python
def should_rebalance_with_cost_check(self, current_positions, target_signals, 
                                     portfolio_value):
    # Estimate transaction costs
    estimated_cost = self._estimate_rebalance_cost(
        current_positions, target_signals, portfolio_value
    )
    
    # Check against threshold
    max_cost_pct = self.config.get('max_rebalance_cost_pct', 0.02)  # 2%
    
    if estimated_cost > portfolio_value * max_cost_pct:
        logger.info(f"Estimated cost {estimated_cost:.2%} exceeds max {max_cost_pct:.2%}")
        return False
    
    return True
```

### 4. Add Tolerance Bands (Lower Priority)

```python
def needs_rebalancing(self, current_weights, target_weights):
    tolerance = self.config.get('rebalance_tolerance', 0.02)  # ±2%
    
    for symbol in target_weights:
        current = current_weights.get(symbol, 0)
        target = target_weights[symbol]
        
        if abs(current - target) > tolerance:
            return True  # Outside tolerance, needs rebalancing
    
    return False  # Within tolerance for all assets
```

---

## Configuration Examples

### Current (All-or-Nothing)

```yaml
lookback_period: 252
threshold: 0.0
rebalance_frequency: monthly
# That's it - always rebalances every month
```

### Improved (Conditional Rebalancing)

```yaml
lookback_period: 252
threshold: 0.0
rebalance_frequency: monthly

# NEW: Signal change filter
signal_change_threshold: 0.10  # Only rebalance if signals change > 10%

# NEW: Cost awareness
max_rebalance_cost_pct: 0.02  # Skip if costs > 2% of portfolio

# NEW: Partial rebalancing
rebalance_aggressiveness: 0.75  # Move 75% toward target

# NEW: Tolerance bands
rebalance_tolerance: 0.02  # Only rebalance if drift > 2%
```

---

## Comparison Table

| Aspect | Current (All-or-Nothing) | Improved (Conditional) |
|--------|-------------------------|------------------------|
| **Decision** | Binary (yes/no) | Graduated (yes/partial/no) |
| **Trigger** | Time only | Time + signals + cost + drift |
| **Adjustment** | 100% to target | Configurable % to target |
| **Cost awareness** | None | Estimates before rebalancing |
| **Tolerance** | Exact targets | Tolerance bands |
| **Turnover** | Higher | Lower |
| **Costs** | Higher | Lower |
| **Flexibility** | Low | High |

---

## Summary

"All-or-nothing" means the system makes a **binary choice**:

1. ✅ **Rebalance**: Completely reconstruct portfolio to exact targets
2. ❌ **Don't rebalance**: Keep everything as is

**No middle ground:**
- Can't partially rebalance
- Can't skip when signals barely changed
- Can't consider transaction costs
- Can't use tolerance bands

**Real impact:**
- Higher turnover than necessary
- Higher transaction costs
- Chasing noise instead of signals
- Lower net returns

**Solution:** Add conditional rebalancing logic that considers:
- Signal change magnitude
- Transaction costs
- Drift amount
- Partial adjustment options

This gives you **control** over when and how much to rebalance, rather than "always rebalance fully" or "never rebalance at all."

---

**Key Insight:** The current system is like a light switch (on/off). The improved system would be like a dimmer switch (can be at any level from 0% to 100%).
