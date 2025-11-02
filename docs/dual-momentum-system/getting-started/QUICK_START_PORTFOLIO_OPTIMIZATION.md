# Quick Start: Portfolio Optimization Methods

Compare 7 portfolio construction methods beyond mean-variance optimization.

## 30-Second Start

```python
from src.portfolio_optimization import compare_portfolio_methods
import pandas as pd

# Your returns data (each column = asset)
returns_df = pd.DataFrame(...)

# Compare all methods
comparison = compare_portfolio_methods(returns=returns_df, risk_free_rate=0.02)

# Results
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(comparison.comparison_metrics)
print(comparison.get_weights_df())
```

## 7 Methods Available

1. **Equal Weight** - Simple 1/N
2. **Inverse Volatility** - Weight by inverse vol
3. **Minimum Variance** - Lowest risk
4. **Maximum Sharpe** - Best risk-adjusted returns
5. **Risk Parity** - Equal risk contribution  
6. **Maximum Diversification** - Max diversification ratio
7. **Hierarchical Risk Parity** - ML clustering approach

## Run Demo

```bash
cd dual_momentum_system

# Full demo (all 7 methods)
python examples/portfolio_optimization_comparison_demo.py

# Quick demo (3 methods)
python examples/portfolio_optimization_comparison_demo.py --quick
```

## Use Individual Method

```python
from src.portfolio_optimization import RiskParityOptimizer

optimizer = RiskParityOptimizer(risk_free_rate=0.02)
result = optimizer.optimize(returns_df)

print(result.weights)  # Portfolio allocation
print(result.sharpe_ratio)
print(result.risk_contributions)  # Risk by asset
```

## Compare Specific Methods

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['equal_weight', 'risk_parity', 'maximum_sharpe'],
    min_weight=0.05,  # Min 5% per asset
    max_weight=0.30,  # Max 30% per asset
    risk_free_rate=0.02,
)
```

## When to Use Each Method

| Your Goal | Use This Method |
|-----------|-----------------|
| Simple baseline | Equal Weight |
| Balanced risk | Risk Parity |
| Lowest volatility | Minimum Variance |
| Best returns | Maximum Sharpe |
| Max diversification | Max Diversification or HRP |
| Stable allocations | HRP or Risk Parity |

## Get Results

```python
# Comparison metrics
print(comparison.comparison_metrics)

# Weights from all methods
weights_df = comparison.get_weights_df()
print(weights_df)

# Best methods
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(f"Best Diversification: {comparison.best_diversification_method}")
print(f"Lowest Volatility: {comparison.lowest_volatility_method}")

# Save results
comparison.save(output_dir='./results')
```

## What You Get

Each method returns:
- Portfolio weights (allocation to each asset)
- Expected return and volatility
- Sharpe ratio
- Diversification ratio
- Risk contributions by asset

## More Information

- **Full Guide**: See `PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md`
- **Feature Summary**: See `PORTFOLIO_OPTIMIZATION_FEATURE_SUMMARY.md`
- **API Docs**: See docstrings in `src/portfolio_optimization/`

## Pro Tips

✅ Start with Equal Weight as baseline
✅ Compare multiple methods
✅ Use constraints (min_weight, max_weight) for diversification
✅ Risk Parity works well for long-term portfolios
✅ HRP is most robust to estimation error

## Dependencies

Required: pandas, numpy, scipy

That's it! Compare methods and find what works best for your portfolio. 🎯
