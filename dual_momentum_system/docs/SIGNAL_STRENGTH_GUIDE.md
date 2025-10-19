# Signal Strength Calculation Guide

## Overview

When the Absolute Momentum strategy generates trading signals, it needs to determine **how much weight to allocate** to each asset. The `strength_method` parameter controls this calculation.

This guide explains:
- Why signal strength matters
- The four calculation methods available
- When to use each method
- Configuration examples
- How the fix addresses previous issues

---

## Why Signal Strength Matters

### The Problem

When multiple assets pass the momentum threshold, you need to decide:
1. **Equal weight?** Give each asset the same allocation (e.g., 3 assets = 33.3% each)
2. **Momentum-weighted?** Give more allocation to assets with higher momentum
3. **Something in between?** Scale gradually based on momentum

The `strength` parameter (0.0 to 1.0) controls an asset's weight in the portfolio.

### Example Scenario

You have 3 assets that pass the 0% momentum threshold:
- **SPY**: 5% momentum
- **QQQ**: 15% momentum  
- **DIA**: 10% momentum

Different strength methods will allocate differently:

| Method | SPY Weight | QQQ Weight | DIA Weight | Reasoning |
|--------|------------|------------|------------|-----------|
| **binary** | 33.3% | 33.3% | 33.3% | Equal weight |
| **linear** | 16.7% | 50.0% | 33.3% | Scaled by excess momentum |
| **proportional** | 16.7% | 50.0% | 33.3% | Weighted by momentum |
| **momentum_ratio** | 16.7% | 50.0% | 33.3% | Relative to leader |

---

## The Four Strength Methods

### 1. Binary (Simple Equal Weight)

**Config:**
```yaml
strength_method: binary
```

**Behavior:**
- All assets that pass threshold get `strength = 1.0`
- Results in equal weighting

**Formula:**
```python
if momentum > threshold:
    strength = 1.0
```

**Example:**
```
Threshold: 0.0
Assets:
  SPY:  5% momentum → strength = 1.0
  QQQ: 20% momentum → strength = 1.0
  DIA: 10% momentum → strength = 1.0

Portfolio: 33.3% SPY, 33.3% QQQ, 33.3% DIA
```

**When to Use:**
- ✅ Simple equal-weight strategies
- ✅ When all passing assets should be treated equally
- ✅ When momentum is binary (trend or no trend)
- ✅ Simplicity and interpretability are priorities

**Advantages:**
- Simple and intuitive
- Reduces concentration risk
- Easy to backtest and understand

**Disadvantages:**
- Doesn't differentiate between strong and weak momentum
- May underweight winners, overweight laggards

---

### 2. Linear (Gradual Scaling)

**Config:**
```yaml
strength_method: linear
strength_scale_range: 0.10  # Scale from threshold to threshold + 10%
```

**Behavior:**
- Strength scales linearly from threshold to threshold + scale_range
- Below threshold: filtered out
- At threshold: strength = 0.0 (or very small)
- At threshold + scale_range: strength = 1.0
- Above threshold + scale_range: strength = 1.0 (capped)

**Formula:**
```python
if momentum > threshold:
    excess = momentum - threshold
    strength = min(1.0, excess / scale_range)
```

**Example:**
```
Threshold: 0.0
Scale Range: 0.10
Assets:
  SPY:  5% momentum → (0.05 - 0.0) / 0.10 = 0.5
  QQQ: 15% momentum → (0.15 - 0.0) / 0.10 = 1.0 (capped)
  DIA: 10% momentum → (0.10 - 0.0) / 0.10 = 1.0

Total strength: 2.5
Portfolio: 20% SPY, 40% QQQ, 40% DIA
```

**Key Feature: Threshold Independence**

The scaling range is **independent** of the threshold:

```
Threshold = 0.0, Scale = 0.10:
  5% momentum → 0.5 strength
  10% momentum → 1.0 strength

Threshold = 0.05, Scale = 0.10:
  10% momentum → (0.10 - 0.05) / 0.10 = 0.5 strength
  15% momentum → (0.15 - 0.05) / 0.10 = 1.0 strength
```

Same excess → Same strength! 🎯

**When to Use:**
- ✅ Want smooth transition from weak to strong signals
- ✅ Gradual position sizing as momentum increases
- ✅ Reducing noise from barely-passing assets
- ✅ Fine control over allocation curve

**Advantages:**
- Flexible and tunable
- Reduces allocation to marginal signals
- Scaling independent of threshold (key fix!)

**Disadvantages:**
- Need to choose appropriate scale_range
- More complex than binary

---

### 3. Proportional (Momentum-Weighted)

**Config:**
```yaml
strength_method: proportional
```

**Behavior:**
- Strength proportional to momentum magnitude
- Automatically normalized to sum to 1.0
- Higher momentum = higher allocation

**Formula:**
```python
if momentum > threshold:
    strength = momentum / sum(all_momentums)
```

**Example:**
```
Threshold: 0.0
Assets:
  SPY:  5% momentum
  QQQ: 15% momentum
  DIA: 10% momentum
  Total: 30%

Strengths:
  SPY: 5/30 = 0.167 → 16.7% weight
  QQQ: 15/30 = 0.500 → 50.0% weight
  DIA: 10/30 = 0.333 → 33.3% weight
```

**When to Use:**
- ✅ Want to overweight high-momentum assets
- ✅ Momentum quality matters more than equal weighting
- ✅ Multiple assets in portfolio
- ✅ Concentration in winners is acceptable

**Advantages:**
- Automatically normalizes to 100%
- Emphasizes strongest momentum
- No parameters to tune

**Disadvantages:**
- Can be top-heavy (concentrated in leaders)
- Sensitive to outliers
- Lower diversification

---

### 4. Momentum Ratio (Relative to Leader)

**Config:**
```yaml
strength_method: momentum_ratio
```

**Behavior:**
- Normalize by the **maximum momentum** asset
- Leader gets strength = 1.0
- Others scaled relative to leader

**Formula:**
```python
if momentum > threshold:
    strength = momentum / max_momentum
```

**Example:**
```
Threshold: 0.0
Assets:
  SPY:  5% momentum
  QQQ: 15% momentum (leader)
  DIA: 10% momentum

Strengths:
  SPY: 5/15 = 0.333
  QQQ: 15/15 = 1.000
  DIA: 10/15 = 0.667

Total: 2.0
Portfolio: 16.7% SPY, 50% QQQ, 33.3% DIA
```

**When to Use:**
- ✅ Want to identify and emphasize the leader
- ✅ Leader-follower portfolio strategy
- ✅ Relative strength is key metric
- ✅ Satellite positions around a core

**Advantages:**
- Clear leader identification (strength=1.0)
- Others positioned relative to leader
- Good for trend-following

**Disadvantages:**
- Very top-heavy allocation
- Leader gets 50%+ of portfolio typically
- Less diversified than other methods

---

## Comparison Table

| Aspect | Binary | Linear | Proportional | Momentum Ratio |
|--------|--------|--------|--------------|----------------|
| **Complexity** | Simple | Medium | Medium | Medium |
| **Diversification** | High | Medium | Low | Low |
| **Momentum Sensitivity** | None | Medium | High | High |
| **Parameters Needed** | None | scale_range | None | None |
| **Leader Emphasis** | None | Low | Medium | High |
| **Best For** | Equal weight | Gradual scaling | Momentum weight | Leader focus |

---

## Configuration Examples

### Conservative (Equal Weight)

```yaml
# Treat all momentum signals equally
strength_method: binary
threshold: 0.05  # Require 5% minimum return
```

**Use Case:** Diversified trend-following, reduce concentration risk

---

### Moderate (Gradual Scaling)

```yaml
# Scale gradually as momentum increases
strength_method: linear
strength_scale_range: 0.10  # Full strength at threshold + 10%
threshold: 0.0
```

**Use Case:** Reward stronger momentum without extreme concentration

---

### Aggressive (Momentum-Weighted)

```yaml
# Overweight high momentum assets
strength_method: proportional
threshold: 0.0
```

**Use Case:** Maximize exposure to winners, accept concentration

---

### Leader-Focused

```yaml
# Identify and follow the leader
strength_method: momentum_ratio
threshold: 0.0
position_count: 3  # Hold top 3, but leader gets most weight
```

**Use Case:** Core-satellite approach, leader-follower strategy

---

## The Bug That Was Fixed

### The Old Behavior (WRONG)

Previously, strength was calculated as:

```python
strength = momentum / (threshold + 0.1)
```

**Problem:** The scaling changed with the threshold!

```
Threshold = 0.0:
  5% momentum → 0.05 / 0.1 = 0.5 ✓
  
Threshold = 0.05:
  10% momentum → 0.10 / 0.15 = 0.667 ✗
```

Both have 5% excess momentum, but got different strengths!

### The New Behavior (CORRECT)

With `linear` method:

```python
strength = (momentum - threshold) / scale_range
```

**Fixed:** The scaling is independent of threshold!

```
Threshold = 0.0, scale_range = 0.10:
  5% momentum → (0.05 - 0.0) / 0.10 = 0.5 ✓
  
Threshold = 0.05, scale_range = 0.10:
  10% momentum → (0.10 - 0.05) / 0.10 = 0.5 ✓
```

Same excess → Same strength! 🎉

---

## Choosing the Right Method

### Decision Tree

```
Do you want equal weighting?
├─ YES → Use 'binary'
└─ NO ↓

Do you want to emphasize high momentum?
├─ SLIGHTLY → Use 'linear' (scale_range = 0.10-0.20)
├─ MODERATELY → Use 'proportional'
└─ HEAVILY → Use 'momentum_ratio'

Is there a clear leader you want to follow?
├─ YES → Use 'momentum_ratio'
└─ NO → Use 'proportional' or 'linear'
```

### By Strategy Style

| Strategy Style | Recommended Method | Reasoning |
|----------------|-------------------|-----------|
| **Trend Following** | binary or linear | Equal weight or gradual scaling |
| **Momentum Concentration** | proportional | Overweight winners |
| **Leader-Follower** | momentum_ratio | Identify and follow leader |
| **Risk Parity** | binary | Equal risk contribution |
| **Tactical Allocation** | linear | Smooth adjustments |

---

## Performance Considerations

### Transaction Costs

More momentum-sensitive methods (proportional, momentum_ratio) can increase turnover:

- **binary**: Low turnover (positions change only on threshold crossing)
- **linear**: Medium turnover (strengths adjust gradually)
- **proportional**: Higher turnover (weights shift with momentum changes)
- **momentum_ratio**: Higher turnover (leader changes cause large shifts)

**Recommendation:** For high transaction costs, prefer `binary` or `linear` with wider scale_range.

### Rebalancing Frequency

Match method to rebalancing frequency:

- **Monthly rebalancing**: Any method works
- **Weekly rebalancing**: Prefer linear or binary (less noise)
- **Daily rebalancing**: Binary recommended (minimize turnover)

---

## Advanced Configuration

### Combining with Position Limits

```yaml
strength_method: proportional
position_count: 5  # Hold top 5 assets
max_position_size: 0.40  # Cap any position at 40%
```

This prevents excessive concentration even with momentum-weighting.

### Threshold and Strength Interaction

```yaml
threshold: 0.03  # Require 3% minimum return
strength_method: linear
strength_scale_range: 0.12  # Full strength at 15% (3% + 12%)
```

Creates a two-stage filter:
1. Absolute filter: Must exceed 3%
2. Strength scaling: Gradually increase from 3% to 15%

---

## Testing Your Configuration

Use these test scenarios to validate your settings:

### Test 1: Threshold Independence
```python
# Should give same strength for same excess momentum
threshold_0 = {'threshold': 0.0, 'momentum': 0.05}
threshold_5 = {'threshold': 0.05, 'momentum': 0.10}
# Both have 5% excess → should have same strength
```

### Test 2: Normalization
```python
# Strengths should be properly normalized
assets = ['SPY', 'QQQ', 'DIA']
strengths = [calculate_strength(a) for a in assets]
# Sum should make sense for portfolio allocation
```

### Test 3: Edge Cases
```python
# Test with single asset, all negative, all equal
```

---

## Migration Guide

### If You Were Using Default Settings

**Before:**
```yaml
# Old implicit behavior
lookback_period: 252
threshold: 0.0
# Strength was momentum / (threshold + 0.1)
```

**After (Equivalent):**
```yaml
# New explicit configuration
lookback_period: 252
threshold: 0.0
strength_method: linear
strength_scale_range: 0.10
# Strength is (momentum - threshold) / scale_range
```

**Note:** The behavior is similar but **now consistent across different thresholds**!

### If You Want Equal Weighting

```yaml
strength_method: binary
# All other settings remain the same
```

---

## FAQs

### Q: Which method is "best"?

**A:** Depends on your goals:
- Diversification → binary
- Smooth scaling → linear  
- Momentum concentration → proportional
- Leader-focused → momentum_ratio

### Q: What's a good scale_range for linear method?

**A:** Common values:
- **0.05-0.10**: Tight scaling (reaches full strength quickly)
- **0.10-0.20**: Medium scaling (default, balanced)
- **0.20-0.50**: Wide scaling (very gradual)

### Q: Can strength be > 1.0?

**A:** No, strength is always clamped to [0.0, 1.0] range.

### Q: Do methods work with single asset?

**A:** Yes! All methods handle single-asset portfolios correctly.

### Q: What happens if all assets have negative momentum?

**A:** All are filtered out. If `safe_asset` is configured, switch to that.

---

## Examples in Code

### Example 1: Testing Different Methods

```python
from src.strategies.absolute_momentum import AbsoluteMomentumStrategy

# Test binary
strategy = AbsoluteMomentumStrategy({
    'lookback_period': 252,
    'threshold': 0.0,
    'strength_method': 'binary'
})

signals = strategy.generate_signals(price_data)
for signal in signals:
    print(f"{signal.symbol}: strength={signal.strength:.3f}")
```

### Example 2: Comparing Methods

```python
methods = ['binary', 'linear', 'proportional', 'momentum_ratio']

for method in methods:
    strategy = AbsoluteMomentumStrategy({
        'strength_method': method,
        'strength_scale_range': 0.10
    })
    
    signals = strategy.generate_signals(price_data)
    print(f"\n{method}:")
    for signal in signals:
        print(f"  {signal.symbol}: {signal.strength:.3f}")
```

---

## Summary

The new signal strength calculation system provides:

1. **Flexibility**: Choose from 4 methods based on your strategy
2. **Consistency**: Scaling is independent of threshold (bug fixed!)
3. **Clarity**: Explicit configuration with documented behavior
4. **Control**: Fine-tune allocation preferences

**Recommended starting point:**
```yaml
strength_method: linear
strength_scale_range: 0.10
```

This provides balanced behavior with smooth scaling and consistent results.

---

## See Also

- [Absolute Momentum Strategy Guide](../README.md)
- [Configuration System](../config/README.md)
- [Backtesting Guide](../QUICKSTART.md)
- [Test Suite](../tests/test_signal_strength_calculation.py)
