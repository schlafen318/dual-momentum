# Benchmark Transaction Costs - Implementation Guide

## Overview

When comparing a trading strategy to a benchmark (e.g., SPY), there are two valid approaches for handling transaction costs:

### 1. Passive Benchmark (Default)
- **No transaction costs applied**
- Represents theoretical buy-and-hold from period start to end
- Standard academic approach used in most research papers
- Assumes benchmark is a low-cost index fund (e.g., SPY with 0.03% annual expense ratio)

### 2. Realistic Benchmark (Optional)
- **Same transaction costs as strategy**
- Represents what an actual investor would get
- Fairer comparison for retail investors
- Includes entry cost + exit cost

## Configuration

```python
# Default: Passive benchmark (no costs)
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
    benchmark_include_costs=False  # Default
)

# Realistic benchmark (with costs)
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
    benchmark_include_costs=True  # Include costs
)
```

## Impact on Results

### Example: SPY Absolute Momentum vs SPY Benchmark

**Scenario:** 3-year backtest, commission=0.1%, slippage=0.05%

#### Passive Benchmark (benchmark_include_costs=False)
```
Strategy Return: 25.00%  (includes all transaction costs)
Benchmark Return: 28.00% (no costs - theoretical buy-and-hold)
Alpha: -3.00%            (strategy underperformed)
```

**Interpretation:** Strategy underperformed the theoretical passive index

#### Realistic Benchmark (benchmark_include_costs=True)
```
Strategy Return: 25.00%  (includes all transaction costs)
Benchmark Return: 27.70% (includes entry 0.15% + exit 0.15% = 0.30%)
Alpha: -2.70%            (strategy still underperformed, but less)
```

**Interpretation:** Strategy underperformed realistic buy-and-hold by retail investor

## When to Use Each Approach

### Use Passive Benchmark (No Costs) When:
1. **Academic comparison** - Following standard research methodology
2. **Index fund comparison** - Comparing to actual index funds (which have minimal costs)
3. **Theoretical maximum** - Want to see maximum possible return from market exposure
4. **Industry standard** - Most published research uses this approach

### Use Realistic Benchmark (With Costs) When:
1. **Retail investor context** - Showing what real person would get
2. **Fair comparison** - Want apples-to-apples cost comparison
3. **Conservative analysis** - Want to be conservative in claims
4. **High-frequency benchmark** - If comparing to actively managed benchmark

## Our Recommendation for SPY-Only Scenario

For your specific case (SPY-only absolute momentum with all buy signals):

**After our fix:**
- Strategy now matches SPY buy-and-hold minus entry/exit costs (~0.30%)
- This is the expected behavior
- Use **passive benchmark (default)** to show you're matching the index
- Alpha will be ~-0.30% due to transaction costs

**Why this is good:**
- Strategy correctly implements buy-and-hold when momentum is positive
- You only pay costs once (entry + exit)
- The ~0.30% difference is the unavoidable cost of entering/exiting the position
- This is equivalent to what an investor would pay with a discount broker

## Implementation Details

### Entry Cost Application
```python
# Applied to initial benchmark value
entry_cost_factor = 1.0 - (commission + slippage)
benchmark_indexed = benchmark_indexed * entry_cost_factor
```

### Exit Cost Application
```python
# Applied to final benchmark value
exit_cost_factor = 1.0 - (commission + slippage)
benchmark_indexed.iloc[-1] = benchmark_indexed.iloc[-1] * exit_cost_factor
```

### Total Impact
```
Entry: 0.001 (commission) + 0.0005 (slippage) = 0.0015 (0.15%)
Exit:  0.001 (commission) + 0.0005 (slippage) = 0.0015 (0.15%)
Total: ~0.30%
```

## Verification

The engine logs clearly indicate which approach is used:

```
# Passive (default)
INFO | Benchmark uses passive buy-and-hold (no transaction costs)
INFO | Benchmark includes transaction costs: NO (passive buy-and-hold)

# Realistic
INFO | Benchmark will include transaction costs for fair comparison
INFO | Applied transaction costs to benchmark:
INFO |    Entry cost: 0.1500%
INFO |    Exit cost: 0.1500%
INFO |    Total impact: ~0.3000%
INFO | Benchmark includes transaction costs: YES
```

## Metadata

Results include benchmark cost setting:
```python
result.metadata['benchmark_include_costs']  # True or False
```

## Academic Standards

Most academic finance papers use **passive benchmark without costs** because:

1. **Standardization** - Allows comparison across papers
2. **Theory vs Practice** - Separates theoretical return from execution costs
3. **Index Funds** - Modern index funds have very low costs (SPY = 0.03%/year)
4. **Clear Attribution** - Shows exactly where performance comes from

Our default follows this standard while giving you the option for realistic comparison.

## Conclusion

- **Default (passive)**: Best for academic comparison, matches industry standard
- **With costs**: Best for showing realistic retail investor experience
- **Both are valid**: Choose based on your audience and goals
- **After our fix**: Strategy returns now correctly match benchmark minus transaction costs
