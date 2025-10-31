# Running Portfolio Optimization - Complete Guide

## 🚀 Quickest Way (One Command)

```bash
cd dual_momentum_system
./run_portfolio_comparison.sh
```

This opens an interactive menu with all options!

## 📋 All Available Methods

### Method 1: Interactive Menu Script ⭐ RECOMMENDED

```bash
cd dual_momentum_system
./run_portfolio_comparison.sh
```

**Menu Options:**
1. Run full comparison (all 7 methods)
2. Run quick comparison (3 methods, faster)
3. Run individual method demo
4. View saved results
5. View saved results + create visualizations
6. Create HTML report

### Method 2: Direct Python Commands

**Full Comparison (All 7 Methods):**
```bash
python3 examples/portfolio_optimization_comparison_demo.py
```

**Quick Comparison (3 Methods):**
```bash
python3 examples/portfolio_optimization_comparison_demo.py --quick
```

**Individual Methods:**
```bash
python3 examples/portfolio_optimization_comparison_demo.py --individual
```

### Method 3: View Results

**View Saved Results:**
```bash
python3 examples/view_portfolio_results.py
```

**Create HTML Report:**
```bash
python3 examples/view_portfolio_results.py --html
```

**Specify Custom Directory:**
```bash
python3 examples/view_portfolio_results.py --dir ./my_results
```

### Method 4: Use in Your Code

**Create `my_comparison.py`:**
```python
from src.portfolio_optimization import compare_portfolio_methods
from src.data_sources import get_default_data_source
import pandas as pd
from datetime import datetime

# Load data
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

# Calculate returns
returns_df = pd.DataFrame({
    symbol: data['close'].pct_change()
    for symbol, data in price_data.items()
}).dropna()

# Run comparison
comparison = compare_portfolio_methods(
    returns=returns_df,
    risk_free_rate=0.02,
    verbose=True
)

# View results
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(comparison.comparison_metrics)
print(comparison.get_weights_df())

# Save
comparison.save(output_dir='./my_results')
```

**Run it:**
```bash
python3 my_comparison.py
```

### Method 5: Interactive Python

```bash
python3
```

```python
>>> from src.portfolio_optimization import compare_portfolio_methods
>>> import pandas as pd
>>> import numpy as np

>>> # Create sample data
>>> np.random.seed(42)
>>> returns_df = pd.DataFrame({
...     'SPY': np.random.randn(1000) * 0.01,
...     'AGG': np.random.randn(1000) * 0.005,
...     'GLD': np.random.randn(1000) * 0.012,
... })

>>> # Run comparison
>>> comparison = compare_portfolio_methods(returns_df, risk_free_rate=0.02)

>>> # Explore
>>> comparison.comparison_metrics
>>> comparison.get_weights_df()
>>> comparison.best_sharpe_method
```

## 📊 What You'll See

### Console Output

```
================================================================================
PORTFOLIO OPTIMIZATION METHODS COMPARISON
================================================================================
Assets: SPY, EFA, EEM, AGG, TLT, GLD
Data points: 1510
Methods: equal_weight, inverse_volatility, minimum_variance, maximum_sharpe, 
         risk_parity, maximum_diversification, hierarchical_risk_parity
================================================================================

Running Equal Weight...
  ✓ Sharpe: 0.8234, Volatility: 0.0089, Diversification: 1.4567

Running Inverse Volatility...
  ✓ Sharpe: 0.9123, Volatility: 0.0076, Diversification: 1.5234

...

================================================================================
COMPARISON COMPLETE
================================================================================
Best Sharpe Ratio: Risk Parity
Best Diversification: Maximum Diversification
Lowest Volatility: Minimum Variance

Comparison Metrics:
                          Method  Expected Return  Expected Volatility  Sharpe Ratio  ...
                    Equal Weight           0.0724               0.0089        0.8234  ...
            Inverse Volatility           0.0698               0.0076        0.9123  ...
              Minimum Variance           0.0612               0.0071        0.8590  ...
               Maximum Sharpe            0.0856               0.0098        0.8735  ...
                  Risk Parity            0.0745               0.0082        0.9091  ...
       Maximum Diversification           0.0723               0.0084        0.8607  ...
Hierarchical Risk Parity           0.0731               0.0080        0.9138  ...

Portfolio Weights:
        equal_weight  inverse_volatility  minimum_variance  ...
SPY           0.167              0.134              0.089  ...
EFA           0.167              0.142              0.156  ...
EEM           0.167              0.089              0.067  ...
AGG           0.167              0.289              0.345  ...
TLT           0.167              0.256              0.267  ...
GLD           0.167              0.090              0.076  ...

Results saved to: dual_momentum_system/portfolio_optimization_results/
  ✓ comparison_csv: full_comparison_demo_20241029_054600_comparison.csv
  ✓ weights_csv: full_comparison_demo_20241029_054600_weights.csv
  ✓ summary_json: full_comparison_demo_20241029_054600_summary.json
```

### Saved Files

**Location:** `portfolio_optimization_results/`

**Files Created:**
- `*_comparison.csv` - Comparison metrics table
- `*_weights.csv` - Portfolio weights from all methods
- `*_summary.json` - Summary with best methods
- `*_<method_name>.json` - Detailed results for each method

### Visualizations (with view_portfolio_results.py)

**Charts Created:**
- `sharpe_comparison.png` - Bar chart of Sharpe ratios
- `weights_heatmap.png` - Heatmap of portfolio weights
- `risk_return_scatter.png` - Risk vs return scatter plot
- `diversification_comparison.png` - Diversification ratios
- `weight_distribution.png` - Weight distribution by method

### HTML Report (with --html flag)

**File:** `portfolio_optimization_report.html`

**Contents:**
- Summary statistics
- Best methods highlighted
- Comparison metrics table
- All visualizations embedded
- Beautiful formatting

**Open in browser:**
```bash
open portfolio_optimization_results/portfolio_optimization_report.html
# or on Linux:
xdg-open portfolio_optimization_results/portfolio_optimization_report.html
```

## 🎯 Common Use Cases

### 1. First Time User - See Everything

```bash
# Run full comparison
./run_portfolio_comparison.sh
# Select option 1

# View results with visualizations
python3 examples/view_portfolio_results.py

# Create HTML report
python3 examples/view_portfolio_results.py --html
```

### 2. Quick Test

```bash
# Fast comparison
python3 examples/portfolio_optimization_comparison_demo.py --quick
```

### 3. Your Own Assets

```python
# Create my_assets_comparison.py
from src.portfolio_optimization import compare_portfolio_methods
from src.data_sources import get_default_data_source
import pandas as pd
from datetime import datetime

# Your assets
MY_ASSETS = ['AAPL', 'MSFT', 'GOOGL', 'BND', 'GLD']

data_provider = get_default_data_source()
price_data = {}

for symbol in MY_ASSETS:
    data = data_provider.fetch_data(
        symbol,
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    price_data[symbol] = data.data

returns_df = pd.DataFrame({
    symbol: data['close'].pct_change()
    for symbol, data in price_data.items()
}).dropna()

comparison = compare_portfolio_methods(
    returns=returns_df,
    max_weight=0.30,  # Max 30% per asset
    risk_free_rate=0.02,
)

print(f"Best method for my assets: {comparison.best_sharpe_method}")
print(comparison.get_weights_df())
```

### 4. Conservative Portfolio

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['minimum_variance', 'risk_parity', 'equal_weight'],
    max_weight=0.25,  # Force diversification
    risk_free_rate=0.02,
)
```

### 5. Aggressive Portfolio

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['maximum_sharpe', 'maximum_diversification'],
    max_weight=0.50,  # Allow concentration
    risk_free_rate=0.02,
)
```

## 📖 Understanding the Output

### Comparison Metrics Table

| Column | Meaning | Good Value |
|--------|---------|------------|
| **expected_return** | Portfolio return | Higher is better |
| **expected_volatility** | Portfolio risk | Lower is better |
| **sharpe_ratio** | Risk-adjusted return | Higher is better (>1 is good) |
| **diversification_ratio** | Diversification benefit | Higher is better (>1 means diversified) |
| **max_weight** | Largest position | Lower means more diversified |
| **min_weight** | Smallest position | Check for tiny positions |
| **n_nonzero** | Number of positions | More means more diversified |

### Portfolio Weights

```
        equal_weight  risk_parity  maximum_sharpe
SPY           0.167        0.143           0.285
AGG           0.167        0.245           0.189
GLD           0.167        0.175           0.123
```

- Values are allocation percentages (sum to 1.0 or 100%)
- Higher number = more allocation to that asset
- Compare across columns to see differences

### Risk Contributions (Risk Parity)

```
{'SPY': 0.334, 'AGG': 0.333, 'GLD': 0.333}
```

- Shows % of total portfolio risk from each asset
- Risk Parity aims for equal contributions
- Sum to 1.0 (100%)

## 🔍 Analyzing Results

### Which Method Should I Choose?

**Look at:**
1. **Best Sharpe Ratio** - Usually the best overall
2. **Your Risk Tolerance**:
   - Conservative? Use lowest volatility method
   - Balanced? Use Risk Parity
   - Aggressive? Use Maximum Sharpe
3. **Diversification Needs**:
   - Need max diversification? Use HRP or Max Diversification
   - OK with concentration? Use Maximum Sharpe
4. **Simplicity Preference**:
   - Want simple? Use Equal Weight
   - Want sophisticated? Use Risk Parity or HRP

### Comparing Methods

```python
# Get all results
for method, result in comparison.results.items():
    print(f"\n{method}:")
    print(f"  Sharpe: {result.sharpe_ratio:.4f}")
    print(f"  Diversification: {result.diversification_ratio:.4f}")
    print(f"  Weights: {result.weights}")
```

### Export for Further Analysis

```python
# Export to Excel
comparison.comparison_metrics.to_excel('comparison.xlsx', index=False)
comparison.get_weights_df().to_excel('weights.xlsx')

# Export to CSV
comparison.comparison_metrics.to_csv('comparison.csv', index=False)
comparison.get_weights_df().to_csv('weights.csv')
```

## ⚠️ Troubleshooting

### "No results found"

**Solution:** Run the demo first
```bash
python3 examples/portfolio_optimization_comparison_demo.py
```

### "Module not found"

**Solution:** Make sure you're in the right directory
```bash
cd dual_momentum_system
pwd  # Should show .../dual_momentum_system
```

### "Optimization failed"

**Solution:** Check your data
```python
# Verify returns data
print(returns_df.head())
print(returns_df.isnull().sum())  # Should be 0
print(returns_df.describe())
```

### Visualizations don't appear

**Solution:** Install matplotlib
```bash
pip install matplotlib seaborn
```

## 📚 Next Steps

1. **Run the demo**: `./run_portfolio_comparison.sh`
2. **View results**: Examine saved CSV/JSON files
3. **Create visualizations**: `python3 examples/view_portfolio_results.py`
4. **Try your assets**: Modify symbols in the demo
5. **Choose your method**: Based on comparison results
6. **Implement**: Use chosen method for real portfolio

## 🎓 Learning More

- **Detailed Guide**: `PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md`
- **Quick Reference**: `QUICK_START_PORTFOLIO_OPTIMIZATION.md`
- **How to Run**: `HOW_TO_RUN_PORTFOLIO_OPTIMIZATION.md`
- **Feature Summary**: `PORTFOLIO_OPTIMIZATION_FEATURE_SUMMARY.md`

## 💡 Pro Tips

✅ Always start with Equal Weight as a baseline
✅ Compare multiple methods before choosing
✅ Use `max_weight` constraint to ensure diversification
✅ Save results for later analysis
✅ Create HTML report for presentations
✅ Test with different date ranges
✅ Consider transaction costs in real implementation

## 🎉 Summary

**To run and view results:**

```bash
# 1. Run comparison
./run_portfolio_comparison.sh

# 2. View results
python3 examples/view_portfolio_results.py

# 3. Create HTML report
python3 examples/view_portfolio_results.py --html

# 4. Open report
open portfolio_optimization_results/portfolio_optimization_report.html
```

**That's it!** You now have complete portfolio optimization results with visualizations and analysis. 📊✨
