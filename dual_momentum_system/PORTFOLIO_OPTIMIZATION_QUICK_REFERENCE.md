# Portfolio Optimization - Quick Reference Card

## 🚀 One-Line Quick Start

```bash
cd dual_momentum_system && ./run_portfolio_comparison.sh
```

## 📋 Methods Available

| # | Method | Description | Best For |
|---|--------|-------------|----------|
| 1 | Equal Weight | Simple 1/N | Baseline, simplicity |
| 2 | Inverse Volatility | Weight by inverse vol | Quick risk adjustment |
| 3 | Minimum Variance | Lowest risk | Conservative investors |
| 4 | Maximum Sharpe | Best risk-adjusted return | Aggressive investors |
| 5 | Risk Parity | Equal risk contribution | Balanced portfolios |
| 6 | Max Diversification | Highest diversification | Diversification focus |
| 7 | HRP | ML clustering | Complex correlations |

## ⚡ Quick Commands

### Run Comparisons

```bash
# Full comparison (all 7 methods)
python3 examples/portfolio_optimization_comparison_demo.py

# Quick comparison (3 methods)
python3 examples/portfolio_optimization_comparison_demo.py --quick

# Individual methods
python3 examples/portfolio_optimization_comparison_demo.py --individual

# Interactive menu
./run_portfolio_comparison.sh
```

### View Results

```bash
# View text results
python3 examples/view_portfolio_results.py

# Create visualizations
python3 examples/view_portfolio_results.py

# Create HTML report
python3 examples/view_portfolio_results.py --html

# Open HTML report
open portfolio_optimization_results/portfolio_optimization_report.html
```

## 💻 Code Snippets

### Compare All Methods

```python
from src.portfolio_optimization import compare_portfolio_methods

comparison = compare_portfolio_methods(
    returns=returns_df,
    risk_free_rate=0.02
)

print(f"Best: {comparison.best_sharpe_method}")
```

### Use Specific Method

```python
from src.portfolio_optimization import RiskParityOptimizer

optimizer = RiskParityOptimizer(risk_free_rate=0.02)
result = optimizer.optimize(returns_df)
print(result.weights)
```

### Compare 2-3 Methods

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['equal_weight', 'risk_parity', 'maximum_sharpe']
)
```

### Get Weights

```python
# All methods
weights_df = comparison.get_weights_df()

# Specific method
rp_weights = comparison.results['risk_parity'].weights
```

### Save Results

```python
comparison.save(output_dir='./results')
```

## 📊 Interpreting Results

### Metrics

| Metric | Good Value | Meaning |
|--------|------------|---------|
| Sharpe Ratio | > 1.0 | Risk-adjusted return |
| Diversification Ratio | > 1.5 | Diversification benefit |
| Expected Volatility | Lower | Portfolio risk |
| Max Weight | < 0.30 | Position size limit |

### Best Methods Identified

- **Best Sharpe** → Highest risk-adjusted returns
- **Best Diversification** → Most diversified portfolio
- **Lowest Volatility** → Lowest risk portfolio

## 🎯 Use Cases

### Conservative
```python
methods=['minimum_variance', 'risk_parity']
max_weight=0.25
```

### Balanced
```python
methods=['risk_parity', 'equal_weight']
max_weight=0.30
```

### Aggressive
```python
methods=['maximum_sharpe']
max_weight=0.50
```

## 📁 Output Files

**Directory:** `portfolio_optimization_results/`

| File | Contents |
|------|----------|
| `*_comparison.csv` | Metrics table |
| `*_weights.csv` | Portfolio weights |
| `*_summary.json` | Summary stats |
| `*.png` | Visualization charts |
| `*.html` | Interactive report |

## 🔍 Quick Analysis

### View Saved CSV
```bash
cat portfolio_optimization_results/*_comparison.csv
```

### Load in Pandas
```python
import pandas as pd
df = pd.read_csv('portfolio_optimization_results/*_comparison.csv')
print(df.sort_values('sharpe_ratio', ascending=False))
```

### View JSON Summary
```bash
cat portfolio_optimization_results/*_summary.json | python3 -m json.tool
```

## 🎨 Visualizations Generated

1. **sharpe_comparison.png** - Sharpe ratio bar chart
2. **weights_heatmap.png** - Weights heatmap
3. **risk_return_scatter.png** - Risk vs return
4. **diversification_comparison.png** - Diversification ratios
5. **weight_distribution.png** - Weight distribution

## ⚙️ Common Options

```python
compare_portfolio_methods(
    returns=returns_df,
    methods=None,           # All methods
    min_weight=0.0,         # No shorts
    max_weight=1.0,         # Full allocation
    risk_free_rate=0.02,    # 2% rf rate
    verbose=True            # Print progress
)
```

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `cd dual_momentum_system` |
| No results | Run demo first |
| Import error | Check Python path |
| Optimization fails | Check data for NaN |

## 📖 Documentation

- 📘 **RUNNING_PORTFOLIO_OPTIMIZATION.md** - Complete guide
- 📗 **PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md** - Method details
- 📙 **QUICK_START_PORTFOLIO_OPTIMIZATION.md** - Quick start
- 📕 **HOW_TO_RUN_PORTFOLIO_OPTIMIZATION.md** - How to run

## ✨ Pro Tips

1. ✅ Start with `Equal Weight` baseline
2. ✅ Use `max_weight=0.30` for diversification
3. ✅ Compare multiple methods
4. ✅ Create HTML report for presentations
5. ✅ Save results for analysis
6. ✅ Test with different date ranges

## 🎯 Decision Tree

```
Need simplicity? → Equal Weight
Need balanced risk? → Risk Parity  
Need low volatility? → Minimum Variance
Need max returns? → Maximum Sharpe
Need max diversification? → Max Diversification or HRP
Need stability? → HRP
```

## 🔗 Quick Links

**Run:** `./run_portfolio_comparison.sh`
**View:** `python3 examples/view_portfolio_results.py`
**Docs:** See MD files in root directory

---

**That's all you need! Pick a command and go!** 🚀
