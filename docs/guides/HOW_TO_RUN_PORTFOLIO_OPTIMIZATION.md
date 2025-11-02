# How to Run and View Portfolio Optimization Comparison

This guide shows you exactly how to run portfolio optimization comparisons and view the results.

## Method 1: Run the Demo Script (Easiest)

### Full Comparison (All 7 Methods)

```bash
cd dual_momentum_system
python examples/portfolio_optimization_comparison_demo.py
```

**What You'll See:**
```
================================================================================
PORTFOLIO OPTIMIZATION METHODS COMPARISON DEMO
================================================================================

Configuration:
  Assets: SPY, EFA, EEM, AGG, TLT, GLD
  Date Range: 2018-01-01 to 2023-12-31

Loading price data...
  ✓ Loaded SPY
  ✓ Loaded EFA
  ✓ Loaded EEM
  ...

Running Equal Weight...
  ✓ Sharpe: 0.8234, Volatility: 0.0089, Diversification: 1.4567

Running Risk Parity...
  ✓ Sharpe: 0.9091, Volatility: 0.0082, Diversification: 1.5234

...

BEST METHODS
================================================================================
🏆 Best Sharpe Ratio: Risk Parity
   Sharpe: 0.9091
   Return: 7.45% (annualized)
   Volatility: 8.20% (annualized)

Portfolio Weights by Method:
        SPY   EFA   EEM   AGG   TLT   GLD
equal_weight  0.167 0.167 0.167 0.167 0.167 0.167
risk_parity   0.143 0.125 0.089 0.245 0.223 0.175
...

Results saved to: dual_momentum_system/portfolio_optimization_results/
  ✓ comparison_csv: full_comparison_demo_20241029_054600_comparison.csv
  ✓ weights_csv: full_comparison_demo_20241029_054600_weights.csv
  ✓ summary_json: full_comparison_demo_20241029_054600_summary.json
```

### Quick Comparison (3 Methods, Faster)

```bash
python examples/portfolio_optimization_comparison_demo.py --quick
```

Compares only Equal Weight, Risk Parity, and Maximum Sharpe for faster results.

### Individual Method Demo

```bash
python examples/portfolio_optimization_comparison_demo.py --individual
```

Shows how to use each optimizer individually.

## Method 2: Use in Your Own Python Code

### Basic Usage

Create a file `my_portfolio_comparison.py`:

```python
from src.portfolio_optimization import compare_portfolio_methods
from src.data_sources import get_default_data_source
import pandas as pd
from datetime import datetime

# 1. Load your data
data_provider = get_default_data_source()
symbols = ['SPY', 'AGG', 'GLD', 'TLT']

price_data = {}
for symbol in symbols:
    data = data_provider.fetch_data(
        symbol,
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    price_data[symbol] = data.data

# 2. Calculate returns
returns_df = pd.DataFrame({
    symbol: data['close'].pct_change()
    for symbol, data in price_data.items()
}).dropna()

# 3. Compare methods
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=None,  # Compare all 7 methods
    min_weight=0.0,  # No shorting
    max_weight=0.40,  # Max 40% per asset
    risk_free_rate=0.02,  # 2% risk-free rate
    verbose=True,  # Print progress
)

# 4. View results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

# Best methods
print(f"\n🏆 Best Sharpe Ratio: {comparison.best_sharpe_method}")
print(f"📊 Best Diversification: {comparison.best_diversification_method}")
print(f"📉 Lowest Volatility: {comparison.lowest_volatility_method}")

# Comparison table
print("\nComparison Metrics:")
print(comparison.comparison_metrics.to_string(index=False))

# Weights from all methods
print("\nPortfolio Weights:")
weights_df = comparison.get_weights_df()
print(weights_df.to_string())

# 5. Get specific method results
best_method = comparison.best_sharpe_method
best_result = comparison.results[best_method]

print(f"\nBest Method Details ({best_method}):")
print(f"  Weights: {best_result.weights}")
print(f"  Expected Return: {best_result.expected_return*252:.2%} (annualized)")
print(f"  Expected Volatility: {best_result.expected_volatility*252**0.5:.2%} (annualized)")
print(f"  Sharpe Ratio: {best_result.sharpe_ratio:.4f}")
print(f"  Diversification Ratio: {best_result.diversification_ratio:.4f}")

# 6. Save results
comparison.save(output_dir='./my_results', prefix='portfolio_comparison')
print("\n✓ Results saved to ./my_results/")
```

Run it:
```bash
python my_portfolio_comparison.py
```

## Method 3: Interactive Python Session

```python
# Start Python
python

# Import
from src.portfolio_optimization import compare_portfolio_methods
import pandas as pd
import numpy as np

# Create sample returns data
np.random.seed(42)
dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
returns_df = pd.DataFrame({
    'SPY': np.random.randn(len(dates)) * 0.01,
    'AGG': np.random.randn(len(dates)) * 0.005,
    'GLD': np.random.randn(len(dates)) * 0.012,
}).iloc[1:]  # Remove first row

# Run comparison
comparison = compare_portfolio_methods(returns_df, risk_free_rate=0.02)

# Explore results interactively
comparison.comparison_metrics
comparison.get_weights_df()
comparison.get_summary()
```

## Method 4: View Saved Results

After running any comparison, results are saved to disk. You can view them:

### CSV Files (Open in Excel/Sheets)

```bash
# View comparison metrics
cat portfolio_optimization_results/*_comparison.csv
# or
open portfolio_optimization_results/*_comparison.csv

# View weights from all methods
cat portfolio_optimization_results/*_weights.csv
```

### JSON Files (Programmatic Access)

```python
import json

# Load summary
with open('portfolio_optimization_results/..._summary.json', 'r') as f:
    summary = json.load(f)
    print(json.dumps(summary, indent=2))

# Load specific method results
with open('portfolio_optimization_results/..._risk_parity.json', 'r') as f:
    rp_results = json.load(f)
    print(f"Risk Parity Weights: {rp_results['weights']}")
```

## Method 5: Pandas Analysis

```python
import pandas as pd

# Load comparison results
comparison_df = pd.read_csv('portfolio_optimization_results/*_comparison.csv')

# View top methods by Sharpe ratio
print(comparison_df.sort_values('sharpe_ratio', ascending=False))

# Load weights
weights_df = pd.read_csv('portfolio_optimization_results/*_weights.csv', index_col=0)

# Plot weights
import matplotlib.pyplot as plt
weights_df.plot(kind='bar', figsize=(12, 6))
plt.title('Portfolio Weights by Method')
plt.ylabel('Weight')
plt.xlabel('Asset')
plt.legend(title='Method', bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('portfolio_weights_comparison.png')
print("Saved visualization to portfolio_weights_comparison.png")
```

## Method 6: Compare Specific Methods Only

```python
from src.portfolio_optimization import compare_portfolio_methods

# Compare just 2-3 methods you're interested in
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['equal_weight', 'risk_parity'],  # Only these 2
    risk_free_rate=0.02,
    verbose=True
)
```

## Method 7: Use Individual Optimizers

```python
from src.portfolio_optimization import (
    EqualWeightOptimizer,
    RiskParityOptimizer,
    MaximumSharpeOptimizer
)

# Equal Weight
ew = EqualWeightOptimizer()
ew_result = ew.optimize(returns_df)
print(f"Equal Weight: {ew_result.weights}")

# Risk Parity
rp = RiskParityOptimizer(risk_free_rate=0.02)
rp_result = rp.optimize(returns_df)
print(f"Risk Parity: {rp_result.weights}")
print(f"Risk Contributions: {rp_result.risk_contributions}")

# Maximum Sharpe
ms = MaximumSharpeOptimizer(risk_free_rate=0.02, max_weight=0.40)
ms_result = ms.optimize(returns_df)
print(f"Max Sharpe: {ms_result.weights}")
```

## Understanding the Output

### Comparison Metrics Table

```
Method                      Expected Return  Expected Volatility  Sharpe Ratio  Diversification Ratio
Equal Weight                         0.0724               0.0089        0.8234                 1.4567
Risk Parity                          0.0745               0.0082        0.9091                 1.5234
Maximum Sharpe                       0.0856               0.0098        0.8735                 1.3456
...
```

**Columns Explained:**
- **Expected Return**: Portfolio return (higher is better)
- **Expected Volatility**: Portfolio risk (lower is better)
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Diversification Ratio**: Diversification benefit (higher is better)

### Weights Table

```
        equal_weight  risk_parity  maximum_sharpe
SPY           0.167        0.143           0.285
AGG           0.167        0.245           0.189
GLD           0.167        0.175           0.123
...
```

Shows allocation percentage for each asset under each method.

### Risk Contributions

```python
result.risk_contributions
# Output: {'SPY': 0.334, 'AGG': 0.333, 'GLD': 0.333}
```

Shows what percentage of total portfolio risk comes from each asset.
- For Risk Parity, these should be roughly equal (0.333 each for 3 assets)

## Visualizing Results

### Create Comparison Charts

```python
import matplotlib.pyplot as plt
import pandas as pd

# Load results
comparison_df = pd.read_csv('portfolio_optimization_results/*_comparison.csv')
weights_df = pd.read_csv('portfolio_optimization_results/*_weights.csv', index_col=0)

# 1. Sharpe Ratio Comparison
plt.figure(figsize=(10, 6))
comparison_df.plot(x='method', y='sharpe_ratio', kind='bar', legend=False)
plt.title('Sharpe Ratio by Optimization Method')
plt.ylabel('Sharpe Ratio')
plt.xlabel('Method')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('sharpe_comparison.png')

# 2. Weights Heatmap
import seaborn as sns
plt.figure(figsize=(12, 8))
sns.heatmap(weights_df, annot=True, fmt='.3f', cmap='YlOrRd')
plt.title('Portfolio Weights by Method')
plt.tight_layout()
plt.savefig('weights_heatmap.png')

print("Saved charts: sharpe_comparison.png, weights_heatmap.png")
```

## Common Use Cases

### 1. Find Best Method for Your Portfolio

```python
comparison = compare_portfolio_methods(returns_df, risk_free_rate=0.02)

print(f"Use this method: {comparison.best_sharpe_method}")
print(f"With these weights: {comparison.results[comparison.best_sharpe_method].weights}")
```

### 2. Conservative Investor

```python
comparison = compare_portfolio_methods(
    returns_df,
    methods=['minimum_variance', 'risk_parity', 'equal_weight'],
    max_weight=0.25  # Max 25% per asset for diversification
)
print(f"Lowest risk method: {comparison.lowest_volatility_method}")
```

### 3. Aggressive Investor

```python
comparison = compare_portfolio_methods(
    returns_df,
    methods=['maximum_sharpe', 'maximum_diversification'],
    max_weight=0.50  # Allow more concentration
)
print(f"Best returns method: {comparison.best_sharpe_method}")
```

## Troubleshooting

### Issue: No Output

**Solution**: Make sure you're in the correct directory
```bash
cd dual_momentum_system
pwd  # Should show .../dual_momentum_system
```

### Issue: Import Errors

**Solution**: Check Python path
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Missing Data

**Solution**: Demo will download data automatically, but you need internet connection
```python
# Check if data loads
from src.data_sources import get_default_data_source
data_provider = get_default_data_source()
test = data_provider.fetch_data('SPY', start_date='2023-01-01')
print(f"Loaded {len(test.data)} data points")
```

## Next Steps

1. **Try the demo**: `python examples/portfolio_optimization_comparison_demo.py`
2. **Experiment with your assets**: Modify the `symbols` list
3. **Try different constraints**: Adjust `min_weight` and `max_weight`
4. **Save and analyze**: Export results and create visualizations
5. **Pick your method**: Choose the one that best fits your goals

## Quick Reference

```bash
# Run full demo
python examples/portfolio_optimization_comparison_demo.py

# Run quick demo
python examples/portfolio_optimization_comparison_demo.py --quick

# Run individual methods
python examples/portfolio_optimization_comparison_demo.py --individual

# View saved results
ls -lh portfolio_optimization_results/
cat portfolio_optimization_results/*_summary.json
```

## Getting Help

- See `PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md` for detailed method descriptions
- See `QUICK_START_PORTFOLIO_OPTIMIZATION.md` for quick reference
- Check example code in `examples/portfolio_optimization_comparison_demo.py`
