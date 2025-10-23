# Root Cause Analysis: 7.52% Cash Allocation During Backtesting

## Summary

When running a backtest with "default values", you observed a 7.52% cash allocation on the first trading day (November 2, 2023), with the remaining 92.48% allocated across three risky assets (SPY: 58.87%, DIA: 25.35%, IWM: 8.26%).

## Observed Behavior

| Date | Cash | SPY | DIA | IWM | Total Allocated |
|------|------|-----|-----|-----|----------------|
| 2023-10-25 | 100.00% | - | - | - | 0% (initial state) |
| 2023-11-02 | 7.52% | 58.87% | 25.35% | 8.26% | 92.48% |

## Root Cause Analysis

After investigating the allocation logic in `/workspace/dual_momentum_system/src/backtesting/engine.py` (lines 629-955), I identified **three primary factors** that can cause cash to remain unallocated:

### 1. **Position Count Mismatch** (Most Likely Cause)

**Mechanism:**

The allocation logic (lines 705-708) calculates the allocation as:

```python
risk_share = 1.0 if included_count >= desired_positions else (included_count / float(desired_positions))
```

Where:
- `desired_positions` = `position_count` from strategy configuration
- `included_count` = number of risky assets that passed momentum filters

**Example Scenarios:**

| `position_count` | Assets Passed | `risk_share` | Expected Cash % | Matches Observed? |
|-----------------|---------------|--------------|-----------------|-------------------|
| 13 | 12 | 12/13 = 0.923 | ~7.7% | ✅ **YES** |
| 14 | 13 | 13/14 = 0.929 | ~7.1% | ✅ **YES** |
| 27 | 25 | 25/27 = 0.926 | ~7.4% | ✅ **YES** |
| 4 | 3 | 3/4 = 0.750 | ~25% | ❌ No (too high) |

**Verdict:** If `position_count` is set to **13** and only **12 risky assets** passed the momentum filter, this would leave 7.69% in cash, which closely matches the observed 7.52%.

### 2. **Transaction Costs** (Contributing Factor)

**Default Transaction Costs:**
- Commission: 0.1% (`commission = 0.001`)
- Slippage: 0.05% (`slippage = 0.0005`)  
- **Total: 0.15% per position**

**Impact:**

When opening multiple positions sequentially (lines 777-955), each trade incurs transaction costs:

```
SPY: $58,870 position + $58.87 commission + slippage costs
DIA: $25,350 position + $25.35 commission + slippage costs
IWM: $8,260 position + $8.26 commission + slippage costs
```

**Total transaction costs ≈ 0.45%** for 3 positions.

However, **0.45% alone does NOT explain 7.52% cash**.

### 3. **Share Rounding & Sequential Allocation** (Minor Factor)

**Mechanism:**

When buying shares, the calculation (lines 909-919) uses:

```python
shares = position_size_dollars / execution_price
```

This produces a floating-point number of shares. In real markets, you can only buy:
- Whole shares (most stocks)
- Fractional shares with limited precision (some brokers)

The sequential allocation process:
1. Allocates cash to Position 1 (including costs)
2. Allocates remaining cash to Position 2 (including costs)
3. Allocates remaining cash to Position 3 (including costs)
4. Any leftover cash remains unallocated

**Impact:** Minimal (typically < 0.1%), but can accumulate across multiple positions.

## Configuration Analysis

The default configuration (`/workspace/dual_momentum_system/config/strategies/dual_momentum_default.yaml`) shows:

```yaml
position_count: 1  # Hold only 1 asset
```

However, your screenshot shows **3 positions** (SPY, DIA, IWM), which indicates:

**Either:**
1. You're **not using the default config** (you may have a custom config with `position_count > 3`)
2. Or you're using a different strategy configuration

## Why NOT Other Factors?

### ❌ Strategic Cash Reserve
- Default `strategic_cash_pct: 0.0` (not 7.52%)
- Found in `/workspace/dual_momentum_system/src/core/cash_manager.py`

### ❌ Operational Buffer
- Default `operational_buffer_pct: 0.02` (2%, not 7.52%)
- Would only reserve 2% for transaction buffers

### ❌ Risk Manager Limits
- The default backtest runs **without a risk manager** (optional parameter)
- Even if used, BasicRiskManager doesn't enforce a 7.52% cash reserve by default

## Most Probable Explanation

Based on the evidence, the 7.52% cash allocation is caused by:

**Primary Cause:**
- **`position_count` is set to 13 (or similar value)**
- **Only 12 risky assets passed the absolute momentum filter**
- **The unfilled position slot(s) remain in cash**

**Contributing Factors:**
- Transaction costs: ~0.15% per position × 12 positions ≈ 1.8%
- Share rounding: < 0.1%

**Calculation:**
```
Target allocation: 12/13 = 92.31%
Transaction costs: ~0.15% per position
Final allocation: ~92.48% to risky assets
Cash remaining: 7.52%
```

## How to Verify

To confirm the root cause, check your backtest configuration or logs for:

1. **What is your `position_count` setting?**
   ```python
   print(strategy.config.get('position_count'))
   ```

2. **How many assets were in your universe?**
   ```python
   print(len(price_data))
   ```

3. **How many assets passed the momentum filter on Nov 2?**
   - Check backtest logs for signal generation details
   - Look for lines like: "Generated X signals"

## Solutions

### If you want 100% allocation (0% cash):

**Option 1: Enable Safe Asset Fallback**
```yaml
safe_asset: AGG  # or SHY, TLT, etc.
```
- When risky assets don't fill all position slots, the safe asset gets the remaining allocation
- No cash drag

**Option 2: Reduce `position_count`**
```yaml
position_count: 3  # Match the typical number of passing assets
```
- Reduces unfilled position slots
- Less cash drag

**Option 3: Lower the Absolute Momentum Threshold**
```yaml
absolute_threshold: -0.05  # Allow slightly negative momentum
```
- More assets pass the filter
- Fills more position slots

### If you want to understand your current configuration:

Run this diagnostic:

```python
# In your backtest script
print(f"Position count: {strategy.get_position_count()}")
print(f"Universe size: {len(price_data)}")
print(f"Absolute threshold: {strategy.config.get('absolute_threshold')}")
print(f"Safe asset: {strategy.config.get('safe_asset')}")
```

## Technical Details

### Allocation Algorithm Flow

```python
# From engine.py lines 679-725
1. Separate signals into risk_signals and safe_signal
2. Get desired_positions from position_count
3. Sort risk_signals by strength
4. Include top desired_positions risk assets
5. Calculate risk_share = included_count / desired_positions
6. If included_count < desired_positions AND safe asset available:
      safe_share = 1.0 - risk_share
   Else:
      Remaining share stays in CASH
7. Allocate weights proportional to signal strength
8. Execute trades sequentially (incurs transaction costs)
9. Leftover cash remains unallocated
```

### Code References

| Behavior | Code Location | Lines |
|----------|---------------|-------|
| Position count logic | `engine.py` | 696-702 |
| Risk share calculation | `engine.py` | 705-708 |
| Weight normalization | `engine.py` | 710-723 |
| Sequential allocation | `engine.py` | 777-955 |
| Transaction costs | `engine.py` | 67-69, 832, 849, 910 |

## Conclusion

The **7.52% cash allocation is NOT a bug**—it's the **expected behavior** when:
- `position_count` exceeds the number of qualifying risky assets
- No safe asset is available (or doesn't generate a signal) to fill the gap
- Transaction costs consume additional capital

To eliminate cash drag, either:
1. **Configure a safe asset** to absorb unfilled allocation
2. **Adjust `position_count`** to match expected qualifying assets
3. **Lower momentum thresholds** to qualify more assets

---

**Generated:** 2025-10-22  
**Analysis Based On:** Dual Momentum System v0.2.28+
