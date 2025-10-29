

# Portfolio Optimization Methods Guide

This guide explains the multiple portfolio construction methods available beyond traditional mean-variance optimization.

## Overview

The Dual Momentum System now supports 7 different portfolio optimization methods:

1. **Equal Weight** - Simple 1/N allocation
2. **Inverse Volatility** - Weight by inverse volatility
3. **Minimum Variance** - Minimize portfolio volatility
4. **Maximum Sharpe Ratio** - Maximize risk-adjusted returns
5. **Risk Parity** - Equal risk contribution from all assets
6. **Maximum Diversification** - Maximize diversification ratio
7. **Hierarchical Risk Parity (HRP)** - Machine learning clustering approach

## Why Use Different Methods?

Traditional mean-variance optimization (Markowitz) has several limitations:
- **Estimation Error**: Sensitive to input estimates
- **Concentration**: Often produces concentrated portfolios
- **Instability**: Small changes in inputs cause large weight changes
- **Assumptions**: Requires accurate return forecasts

Alternative methods address these issues by:
- Using only covariance (not returns)
- Focusing on specific objectives (diversification, risk parity)
- Being more robust to estimation error
- Producing more stable allocations

## Method Descriptions

### 1. Equal Weight (1/N)

**Description**: Allocates equal weight to each asset.

**Formula**: \( w_i = \frac{1}{N} \) for all assets

**Pros**:
- Simple and transparent
- No parameter estimation needed
- Surprisingly effective in practice
- Robust to estimation error

**Cons**:
- Ignores all asset characteristics
- No risk adjustment
- Can be suboptimal with heterogeneous assets

**When to Use**:
- As a benchmark
- When you distrust estimates
- For highly diversified portfolios
- When simplicity is valued

### 2. Inverse Volatility

**Description**: Weights assets inversely proportional to their volatility.

**Formula**: \( w_i = \frac{1/\sigma_i}{\sum_j 1/\sigma_j} \)

**Pros**:
- Simple to compute
- Risk-aware allocation
- More stable than mean-variance
- No covariance matrix needed

**Cons**:
- Ignores correlations
- Doesn't optimize specific objective
- May underweight high-return assets

**When to Use**:
- Quick risk-adjusted allocation
- When correlations are unknown
- For stable, conservative portfolios

### 3. Minimum Variance

**Description**: Finds the portfolio with the lowest possible volatility.

**Optimization**: Minimize \( w^T \Sigma w \) subject to \( \sum w_i = 1 \)

**Pros**:
- Lowest volatility possible
- No return estimates needed
- Works well empirically
- Stable allocations

**Cons**:
- May sacrifice returns
- Can be concentrated
- Ignores return objectives

**When to Use**:
- Risk-averse investors
- Uncertain return expectations
- Defensive allocation
- Low-volatility mandates

### 4. Maximum Sharpe Ratio

**Description**: Maximizes the risk-adjusted return (Sharpe ratio).

**Optimization**: Maximize \( \frac{w^T \mu - r_f}{\sqrt{w^T \Sigma w}} \)

**Pros**:
- Best risk-adjusted returns
- Balances return and risk
- Theoretically optimal

**Cons**:
- Requires return estimates
- Sensitive to estimation error
- Can produce extreme weights
- Unstable allocations

**When to Use**:
- Confident in return forecasts
- Seeking optimal risk-adjusted returns
- With robust return estimates
- Short-term tactical allocation

### 5. Risk Parity

**Description**: Equalizes risk contribution from each asset.

**Objective**: Each asset contributes \( \frac{1}{N} \) to portfolio risk

**Pros**:
- Balanced risk exposure
- Stable allocations
- No return estimates needed
- Works well across market cycles

**Cons**:
- May underweight high-return assets
- Requires optimization
- Complexity vs. equal weight

**When to Use**:
- Long-term strategic allocation
- Balanced multi-asset portfolios
- When you want equal risk exposure
- Institutional portfolios

### 6. Maximum Diversification

**Description**: Maximizes the diversification ratio.

**Optimization**: Maximize \( \frac{w^T \sigma}{\sqrt{w^T \Sigma w}} \)

**Pros**:
- Maximum diversification benefit
- Reduces concentration risk
- No return estimates needed
- Robust allocations

**Cons**:
- May sacrifice returns
- Can underweight correlated assets
- Computational complexity

**When to Use**:
- Seeking maximum diversification
- Reducing concentration risk
- Multi-strategy portfolios
- Risk management focus

### 7. Hierarchical Risk Parity (HRP)

**Description**: Uses machine learning (hierarchical clustering) to build portfolios.

**Method**:
1. Cluster assets by correlation
2. Build hierarchy tree
3. Recursively allocate using inverse variance

**Pros**:
- Robust to estimation error
- Handles non-normal distributions
- Stable allocations
- Accounts for asset structure

**Cons**:
- Complex algorithm
- Requires more computation
- Harder to explain
- Newer method (less track record)

**When to Use**:
- Complex asset universe
- Non-normal returns
- Seeking stability
- Machine learning preference

## Comparison Framework

### Using the Comparison Function

```python
from src.portfolio_optimization import compare_portfolio_methods
import pandas as pd

# Your returns data
returns_df = pd.DataFrame(...)  # Each column is an asset

# Compare all methods
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=None,  # None = compare all
    min_weight=0.0,  # No shorting
    max_weight=0.5,  # Max 50% per asset
    risk_free_rate=0.02,  # 2% risk-free rate
    verbose=True,
)

# View results
print(comparison.comparison_metrics)
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(f"Best Diversification: {comparison.best_diversification_method}")
print(f"Lowest Volatility: {comparison.lowest_volatility_method}")

# Get weights from all methods
weights_df = comparison.get_weights_df()
print(weights_df)

# Save results
comparison.save(output_dir='./results', prefix='my_comparison')
```

### Comparison Metrics

The comparison provides:

| Metric | Description |
|--------|-------------|
| `expected_return` | Expected portfolio return |
| `expected_volatility` | Expected portfolio volatility |
| `sharpe_ratio` | Risk-adjusted return |
| `diversification_ratio` | Diversification benefit |
| `max_weight` | Largest single position |
| `min_weight` | Smallest single position |
| `n_nonzero` | Number of non-zero positions |

## Practical Guidelines

### For Different Investor Types

**Conservative Investors**:
- Primary: Minimum Variance
- Secondary: Risk Parity
- Consider: Equal Weight as benchmark

**Balanced Investors**:
- Primary: Risk Parity
- Secondary: Maximum Diversification
- Consider: HRP for stability

**Aggressive Investors**:
- Primary: Maximum Sharpe
- Secondary: Inverse Volatility
- Consider: Equal Weight as discipline

**Institutional Investors**:
- Primary: Risk Parity
- Secondary: HRP
- Consider: Maximum Diversification

### For Different Asset Classes

**Equities Only**:
- Equal Weight often works well
- Maximum Sharpe if you have edge
- Minimum Variance for defensive

**Multi-Asset (Stocks/Bonds)**:
- Risk Parity excellent choice
- Minimum Variance for conservative
- Maximum Diversification for balance

**Alternative Assets**:
- HRP handles complex correlations
- Maximum Diversification reduces concentration
- Risk Parity for balanced exposure

### Parameter Selection

**Weight Constraints**:
```python
# No constraints (allow concentration)
min_weight=0.0, max_weight=1.0

# Moderate diversification
min_weight=0.0, max_weight=0.3  # Max 30% per asset

# High diversification
min_weight=0.05, max_weight=0.20  # 5-20% per asset
```

**Risk-Free Rate**:
- Use current T-bill rate for accuracy
- Use long-term average (2-3%) for stability
- Set to 0 if comparing gross returns

## Code Examples

### Individual Method Usage

```python
from src.portfolio_optimization import RiskParityOptimizer
import pandas as pd

# Create optimizer
optimizer = RiskParityOptimizer(
    min_weight=0.05,
    max_weight=0.30,
    risk_free_rate=0.02
)

# Optimize
result = optimizer.optimize(returns_df)

# Access results
print(result.weights)  # Dict of weights
print(result.sharpe_ratio)
print(result.diversification_ratio)
print(result.risk_contributions)  # Risk contribution by asset
```

### Comparing Specific Methods

```python
# Compare only 3 methods
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['equal_weight', 'risk_parity', 'maximum_sharpe'],
    risk_free_rate=0.02,
)
```

### Accessing Detailed Results

```python
# Get results from specific method
rp_result = comparison.results['risk_parity']

# Analyze risk contributions
risk_df = pd.DataFrame({
    'Asset': list(rp_result.risk_contributions.keys()),
    'Weight': [rp_result.weights[k] for k in rp_result.risk_contributions.keys()],
    'Risk_Contribution': list(rp_result.risk_contributions.values())
})
print(risk_df)

# Get summary
summary = comparison.get_summary()
print(summary)
```

## Advanced Topics

### Rebalancing Frequency

Portfolio optimization should be rebalanced periodically:
- **Monthly**: Typical for institutional investors
- **Quarterly**: Balance of turnover and optimization
- **Annually**: Tax-efficient for taxable accounts
- **Tactical**: When significant market changes occur

### Combining Methods

You can combine multiple methods:

```python
# Get weights from multiple methods
ew_weights = equal_weight_result.weights
rp_weights = risk_parity_result.weights

# Blend 50/50
blended = {
    asset: 0.5 * ew_weights[asset] + 0.5 * rp_weights[asset]
    for asset in ew_weights.keys()
}
```

### Handling Missing Data

```python
# Remove assets with insufficient data
min_periods = 252  # 1 year daily data
returns_clean = returns_df.dropna(thresh=min_periods, axis=1)

# Fill forward for occasional missing values
returns_filled = returns_df.fillna(method='ffill').dropna()
```

### Out-of-Sample Testing

```python
# In-sample optimization
train_returns = returns_df['2015':'2020']
comparison_train = compare_portfolio_methods(train_returns)

# Apply to out-of-sample period
test_returns = returns_df['2021':'2023']
weights = comparison_train.results['risk_parity'].weights

# Calculate out-of-sample performance
oos_return = sum(weights[asset] * test_returns[asset].mean() 
                 for asset in weights.keys())
```

## Troubleshooting

### Optimization Fails to Converge

**Problem**: Optimizer doesn't find solution

**Solutions**:
- Check for missing/infinite values in returns
- Ensure covariance matrix is positive definite
- Relax weight constraints
- Try different method (e.g., Equal Weight always works)

### Extreme Weights

**Problem**: One asset gets 80%+ allocation

**Solutions**:
- Add max_weight constraint (e.g., max_weight=0.30)
- Use Risk Parity or HRP for balanced weights
- Check for data quality issues
- Consider Equal Weight as baseline

### Unstable Allocations

**Problem**: Weights change dramatically over time

**Solutions**:
- Use more robust method (Risk Parity, HRP, Equal Weight)
- Increase lookback period for return calculation
- Add turnover constraints
- Rebalance less frequently

## Performance Considerations

**Speed Rankings** (fastest to slowest):
1. Equal Weight (instant)
2. Inverse Volatility (very fast)
3. Minimum Variance (fast)
4. Maximum Diversification (fast)
5. Maximum Sharpe (medium)
6. Risk Parity (medium)
7. HRP (slower, clustering step)

For large universes (100+ assets):
- Equal Weight and Inverse Volatility scale perfectly
- HRP becomes slow due to clustering
- Consider parallel computation for optimization

## References and Further Reading

### Academic Papers
- **Risk Parity**: Qian (2005) "Risk Parity Portfolios"
- **HRP**: López de Prado (2016) "Building Diversified Portfolios that Outperform Out of Sample"
- **Maximum Diversification**: Choueifaty & Coignard (2008) "Toward Maximum Diversification"

### Books
- **"Advances in Portfolio Construction and Implementation"** - Guerard & Saxena
- **"Machine Learning for Asset Managers"** - Marcos López de Prado
- **"Expected Returns"** - Antti Ilmanen

## API Reference

### Core Classes

```python
class PortfolioOptimizer:
    """Base class for all optimizers"""
    def __init__(self, min_weight=0.0, max_weight=1.0, risk_free_rate=0.0)
    def optimize(self, returns: pd.DataFrame) -> OptimizationResult

class OptimizationResult:
    """Results from optimization"""
    weights: Dict[str, float]
    method: str
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    diversification_ratio: float
    risk_contributions: Dict[str, float]
```

### Available Optimizers

- `EqualWeightOptimizer`
- `InverseVolatilityOptimizer`
- `MinimumVarianceOptimizer`
- `MaximumSharpeOptimizer`
- `RiskParityOptimizer`
- `MaximumDiversificationOptimizer`
- `HierarchicalRiskParityOptimizer`

### Comparison Function

```python
def compare_portfolio_methods(
    returns: pd.DataFrame,
    methods: Optional[List[str]] = None,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.0,
    verbose: bool = True,
) -> PortfolioMethodComparison
```

## Examples

See `examples/portfolio_optimization_comparison_demo.py` for complete working examples.

## Conclusion

Multiple portfolio optimization methods provide flexibility to match your investment objectives:
- **Need simplicity?** Use Equal Weight
- **Want balanced risk?** Use Risk Parity
- **Seeking max returns?** Use Maximum Sharpe
- **Need stability?** Use HRP or Minimum Variance

**Best practice**: Compare multiple methods and understand their tradeoffs before selecting one for your portfolio.
