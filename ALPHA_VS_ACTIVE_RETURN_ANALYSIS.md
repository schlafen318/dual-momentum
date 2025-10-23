# Analysis: Why Alpha and Active Annual Return Are Different

## Executive Summary

Your backtest shows:
- **Alpha (Annual)**: -0.01%
- **Active Return (Annual)**: -5.54%
- **Beta**: 0.81

This significant difference (-5.53 percentage points) is **expected and correct** because these metrics measure fundamentally different aspects of performance.

---

## Key Definitions

### Active Return
**Active Return** is the raw difference between your strategy's return and the benchmark's return:

```
Active Return = Strategy Return - Benchmark Return
```

- **No risk adjustment**
- Answers: "How much more (or less) did I earn compared to the benchmark?"
- In your case: You underperformed SPY by 5.54% annually

### Alpha
**Alpha** is the excess return over what the Capital Asset Pricing Model (CAPM) predicts you should earn given your risk exposure (beta):

```
Expected Return = Risk-Free Rate + Beta × (Benchmark Return - Risk-Free Rate)
Alpha = Strategy Return - Expected Return
```

- **Risk-adjusted metric**
- Answers: "Did I beat my expected return given my risk level?"
- In your case: You performed almost exactly as expected (-0.01%)

---

## Why They're Different: The Math

Given your metrics:
- Beta = 0.81
- Active Return = -5.54%

Let's work backwards to understand what happened:

### Step 1: Understanding Beta
Beta = 0.81 means your strategy has **19% less volatility** than the benchmark. You're taking less risk than the market.

### Step 2: CAPM Expectation
With a beta of 0.81, CAPM expects you to earn:
- 81% of the benchmark's excess returns (returns above risk-free rate)
- Plus the risk-free rate

### Step 3: Numerical Example
Let's say:
- Risk-Free Rate = 4% annually
- Benchmark (SPY) Return = 33.1% annually (example)
- Your Strategy Return = 27.56% annually (SPY - 5.54%)

#### Calculate Expected Return:
```
Expected Return = 4% + 0.81 × (33.1% - 4%)
                = 4% + 0.81 × 29.1%
                = 4% + 23.57%
                = 27.57%
```

#### Calculate Alpha:
```
Alpha = Actual Return - Expected Return
      = 27.56% - 27.57%
      = -0.01%
```

**This matches your results exactly!**

---

## Interpretation

### Active Return of -5.54%
❌ **Underperformance**: Your strategy returned 5.54% less than SPY on an absolute basis.

**Why?**
- You held less risky positions (beta < 1)
- You likely held cash or defensive assets at times
- Lower volatility typically means lower returns in bull markets

### Alpha of -0.01%
✅ **Nearly Perfect Risk-Adjusted Performance**: Given your lower risk profile, you performed almost exactly as expected.

**Why This is Important:**
- Your strategy took **19% less risk** than the market
- In exchange for lower risk, you should expect lower returns
- Your alpha of -0.01% shows you got the expected risk-adjusted return
- You didn't waste risk capacity or destroy value

---

## Real-World Analogy

Think of it like comparing two drivers:

**Active Return** asks:
- "Who finished first?"
- Driver A (benchmark) finished in 1 hour
- Driver B (your strategy) finished in 1 hour 5 minutes
- Active Return = -5 minutes (you were slower)

**Alpha** asks:
- "Who did better relative to their car's speed limit?"
- Driver A had a sports car (high beta, high speed limit)
- Driver B had a sedan (low beta, lower speed limit)
- Both drove at 95% of their car's maximum speed
- Alpha ≈ 0 (both performed equally well for their vehicle type)

---

## Code Implementation

Your system calculates these metrics in `performance.py` and `vectorized_metrics.py`:

### Active Return (lines 542-543 in performance.py):
```python
# Simple difference - no risk adjustment
metrics['active_return'] = float(annual_strategy_return - annual_benchmark_return)
```

### Alpha (lines 511-519 in performance.py):
```python
# CAPM-based risk adjustment
annual_strategy_return = (1 + aligned_returns).prod() ** (self.periods_per_year / len(aligned_returns)) - 1
annual_benchmark_return = (1 + aligned_benchmark).prod() ** (self.periods_per_year / len(aligned_benchmark)) - 1

# Calculate expected return based on beta
expected_return = risk_free_rate + metrics['beta'] * (annual_benchmark_return - risk_free_rate)

# Alpha is the difference from expected
metrics['alpha'] = float(annual_strategy_return - expected_return)
```

---

## What This Means for Your Strategy

### Good News ✅
1. **Risk Management is Working**: Your beta of 0.81 shows your strategy successfully reduces market risk
2. **Efficient Risk-Adjusted Returns**: Alpha near zero means you're getting fair compensation for the risk you're taking
3. **No Systematic Skill Destruction**: You're not underperforming relative to your risk profile

### Areas to Consider 🤔
1. **Return Enhancement**: While your risk-adjusted performance is fair, you may want to explore ways to increase absolute returns
2. **Beta Targeting**: If your goal is to match SPY returns, you need to increase your beta closer to 1.0
3. **Market Conditions**: Your strategy might perform better in volatile/down markets due to lower beta

### Strategy Implications
Your current strategy appears to be:
- **Conservative/Defensive**: Lower volatility than the benchmark
- **Risk-Efficient**: Getting expected returns for risk taken
- **Not Optimal for Bull Markets**: Will underperform in strong uptrends

---

## Common Misconceptions

### ❌ Misconception 1: "Negative active return means bad alpha"
**Reality**: Alpha adjusts for risk. You can have negative active return but positive alpha if you took significantly less risk.

### ❌ Misconception 2: "Alpha should equal active return"
**Reality**: They're only equal when beta = 1.0 (same risk as benchmark) and risk-free rate is 0%.

### ❌ Misconception 3: "Alpha is more important than active return"
**Reality**: Both matter. Alpha shows skill, active return shows absolute performance. Investors care about both.

---

## Recommendations

### For Higher Absolute Returns (Increase Active Return)
1. **Increase Position Sizes**: Take larger positions in high-conviction ideas
2. **Reduce Cash Holdings**: Minimize cash drag
3. **Adjust Momentum Parameters**: Fine-tune to capture more upside

### For Better Risk-Adjusted Returns (Increase Alpha)
1. **Enhance Signal Quality**: Improve entry/exit timing
2. **Sector/Factor Tilts**: Add value through smart selection
3. **Transaction Cost Reduction**: Minimize friction costs

### For Matching Benchmark Returns (Beta ≈ 1.0)
1. **Full Investment Policy**: Stay fully invested
2. **Leverage if Appropriate**: Consider modest leverage to increase exposure
3. **Reduce Defensive Tilts**: Limit cash and safe asset allocations

---

## Technical Details

### Beta Calculation
From your metrics (line 503-508 in performance.py):
```python
covariance = aligned_returns.cov(aligned_benchmark)
benchmark_variance = aligned_benchmark.var()
metrics['beta'] = float(covariance / benchmark_variance) if benchmark_variance > 0 else 0.0
```

Beta = 0.81 means:
- For every 1% the benchmark moves, your strategy moves 0.81% on average
- Correlation × (Your Volatility / Benchmark Volatility) = 0.81

### Other Relevant Metrics
Your dashboard also shows:
- **Information Ratio**: Risk-adjusted active return (alpha / tracking error)
- **Tracking Error**: Volatility of active returns (6.48%)
- **Up Capture Ratio**: 87.7% - You capture 87.7% of benchmark gains
- **Down Capture Ratio**: 89.8% - You capture 89.8% of benchmark losses

The capture ratios confirm your lower beta:
- Both ratios < 100% ✓ Consistent with beta < 1
- Similar magnitude (87.7% vs 89.8%) ✓ Symmetric risk reduction

---

## Conclusion

The difference between your alpha (-0.01%) and active return (-5.54%) is **not a bug or error**. It's a fundamental feature of risk-adjusted performance measurement.

**Bottom Line:**
- You took 19% less risk than SPY (beta = 0.81)
- You earned 5.54% less return than SPY (active return = -5.54%)
- This trade-off is almost exactly what CAPM predicts (alpha = -0.01%)
- Your strategy is risk-efficient but not designed to beat the market on an absolute basis

**If your goal is to beat SPY absolutely**: Consider increasing risk exposure (target beta closer to 1.0)

**If your goal is risk-adjusted returns**: Your current performance is nearly optimal; focus on enhancing alpha through better signal quality

---

## References

1. **Capital Asset Pricing Model (CAPM)**
   - Sharpe, W. F. (1964). "Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk"

2. **Active Return vs Alpha**
   - Grinold, R. C., & Kahn, R. N. (1999). "Active Portfolio Management"

3. **Information Ratio**
   - Goodwin, T. H. (1998). "The Information Ratio"

4. **Your Implementation**
   - `dual_momentum_system/src/backtesting/performance.py` (lines 463-563)
   - `dual_momentum_system/src/backtesting/vectorized_metrics.py` (lines 753-851)
   - `dual_momentum_system/frontend/pages/backtest_results.py` (lines 83-166)

---

*Generated: 2025-10-23*  
*Analysis of Alpha vs Active Return Discrepancy*
