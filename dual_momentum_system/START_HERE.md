# START HERE: Portfolio Optimization

## 🎯 What This Does

Compares **7 portfolio construction methods** to find which works best for your assets.

## ⚡ Run It (3 Commands)

```bash
cd dual_momentum_system
./run_portfolio_comparison.sh
python3 examples/view_portfolio_results.py --html
```

That's it! You'll get:
- ✅ Comparison of all 7 methods
- ✅ Best method identified
- ✅ Portfolio weights for each method
- ✅ 5 visualization charts
- ✅ HTML report

## 📊 The 7 Methods

1. **Equal Weight** - Simple baseline
2. **Inverse Volatility** - Risk-weighted
3. **Minimum Variance** - Lowest risk
4. **Maximum Sharpe** - Best returns
5. **Risk Parity** - Balanced
6. **Max Diversification** - Most diversified
7. **HRP** - Machine learning

## 🎯 What You Get

**Files created in `portfolio_optimization_results/`:**
- CSV files with all data
- PNG charts (5 visualizations)
- HTML report
- JSON summaries

**Open the HTML report:**
```bash
open portfolio_optimization_results/portfolio_optimization_report.html
```

## 💻 Use Your Own Assets

Edit this and run it:

```python
# my_portfolio.py
from src.portfolio_optimization import compare_portfolio_methods
from src.data_sources import get_default_data_source
from datetime import datetime
import pandas as pd

# YOUR ASSETS HERE
MY_ASSETS = ['AAPL', 'MSFT', 'GOOGL', 'BND', 'GLD']

# Load data
data_provider = get_default_data_source()
price_data = {}
for symbol in MY_ASSETS:
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

# Compare methods
comparison = compare_portfolio_methods(
    returns=returns_df,
    max_weight=0.30,  # Max 30% per asset
    risk_free_rate=0.02
)

# Results
print(f"\nBest method: {comparison.best_sharpe_method}")
print("\nWeights:")
for asset, weight in comparison.results[comparison.best_sharpe_method].weights.items():
    print(f"  {asset}: {weight*100:.1f}%")

comparison.save(output_dir='./my_results')
```

```bash
python3 my_portfolio.py
```

## 🆘 Need Help?

**Full documentation:**
- `USER_GUIDE_PORTFOLIO_OPTIMIZATION.md` - Complete user guide
- `PORTFOLIO_OPTIMIZATION_QUICK_REFERENCE.md` - Quick commands
- `RUNNING_PORTFOLIO_OPTIMIZATION.md` - All running methods

**Quick tips:**
- Start with Equal Weight as baseline
- Risk Parity is good for balanced portfolios
- Use `max_weight=0.30` to limit concentration
- Compare multiple methods before choosing

## ✅ That's It!

Run the 3 commands at the top and you're done!

Questions? See the documentation files listed above.

**Happy optimizing!** 📈
