# User Guide: Running Portfolio Optimization

## ✨ What You Can Do

You now have **7 different portfolio optimization methods** beyond mean-variance:
1. Equal Weight
2. Inverse Volatility  
3. Minimum Variance
4. Maximum Sharpe Ratio
5. Risk Parity
6. Maximum Diversification
7. Hierarchical Risk Parity (HRP)

You can **compare them all** to find which works best for your portfolio!

## 🎯 Simplest Way to Get Started (3 Steps)

### Step 1: Run the Comparison

```bash
cd dual_momentum_system
./run_portfolio_comparison.sh
```

Select option `1` for full comparison.

**You'll see:**
- Progress as each method runs
- Sharpe ratio, volatility, and diversification for each
- Comparison table showing all metrics
- Best methods identified automatically

**Results saved to:** `portfolio_optimization_results/`

### Step 2: View the Results

```bash
python3 examples/view_portfolio_results.py
```

**You'll see:**
- Summary of best methods
- Comparison metrics table
- Portfolio weights from each method
- **5 visualization charts created automatically:**
  - Sharpe ratio comparison
  - Weights heatmap
  - Risk vs return scatter
  - Diversification comparison
  - Weight distribution

### Step 3: Create HTML Report

```bash
python3 examples/view_portfolio_results.py --html
open portfolio_optimization_results/portfolio_optimization_report.html
```

**You get:**
- Beautiful interactive HTML report
- All visualizations embedded
- Ready to share or present

## 📊 What the Output Looks Like

### Console Output (Step 1)

```
================================================================================
PORTFOLIO OPTIMIZATION METHODS COMPARISON
================================================================================
Assets: SPY, EFA, EEM, AGG, TLT, GLD
Methods: equal_weight, risk_parity, maximum_sharpe, ...

Running Equal Weight...
  ✓ Sharpe: 0.8234, Volatility: 0.0089

Running Risk Parity...
  ✓ Sharpe: 0.9091, Volatility: 0.0082

...

🏆 Best Sharpe Ratio: Risk Parity
   Score: 0.9091
   Return: 7.45% (annualized)
   Volatility: 8.20% (annualized)

Portfolio Weights:
        SPY   EFA   EEM   AGG   TLT   GLD
equal_weight  0.167 0.167 0.167 0.167 0.167 0.167
risk_parity   0.143 0.125 0.089 0.245 0.223 0.175
maximum_sharpe 0.285 0.156 0.098 0.189 0.178 0.094
```

### Files Created

```
portfolio_optimization_results/
├── full_comparison_20241029_054600_comparison.csv    ← Metrics table
├── full_comparison_20241029_054600_weights.csv       ← Portfolio weights
├── full_comparison_20241029_054600_summary.json      ← Summary stats
├── full_comparison_20241029_054600_risk_parity.json  ← Risk Parity details
├── full_comparison_20241029_054600_maximum_sharpe.json ← Max Sharpe details
├── ... (one JSON per method)
├── sharpe_comparison.png                              ← Chart 1
├── weights_heatmap.png                                ← Chart 2
├── risk_return_scatter.png                            ← Chart 3
├── diversification_comparison.png                     ← Chart 4
├── weight_distribution.png                            ← Chart 5
└── portfolio_optimization_report.html                 ← Full HTML report
```

### Visualizations Created (Step 2)

**1. Sharpe Ratio Comparison**
- Bar chart showing Sharpe ratio for each method
- Best method highlighted in green

**2. Weights Heatmap**
- Color-coded heatmap of portfolio weights
- Each row = asset, each column = method
- Easy to see differences across methods

**3. Risk-Return Scatter**
- X-axis: Volatility (risk)
- Y-axis: Return
- Best Sharpe method marked with star

**4. Diversification Comparison**
- Bar chart of diversification ratios
- Higher = more diversified

**5. Weight Distribution**
- Stacked bar chart showing weight allocation
- Compare how each method allocates capital

## 🎮 Interactive Menu (Easiest!)

When you run `./run_portfolio_comparison.sh`, you get:

```
========================================================================
PORTFOLIO OPTIMIZATION COMPARISON
========================================================================

What would you like to do?

1) Run full comparison (all 7 methods)
2) Run quick comparison (3 methods, faster)
3) Run individual method demo
4) View saved results
5) View saved results + create visualizations
6) Create HTML report

Enter choice [1-6]:
```

Just type a number and press Enter!

## 💻 Use in Your Own Code

### Compare All Methods

```python
from src.portfolio_optimization import compare_portfolio_methods
import pandas as pd

# Your returns data (each column = one asset)
returns_df = pd.DataFrame(...)

# Run comparison
comparison = compare_portfolio_methods(
    returns=returns_df,
    risk_free_rate=0.02,
    verbose=True
)

# View results
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(f"Score: {comparison.best_overall_score:.4f}")

# Get weights from best method
best_weights = comparison.results[comparison.best_sharpe_method].weights
print(f"Use these weights: {best_weights}")

# Save for later
comparison.save(output_dir='./my_results')
```

### Use a Specific Method

```python
from src.portfolio_optimization import RiskParityOptimizer

# Create optimizer
optimizer = RiskParityOptimizer(
    min_weight=0.05,  # Min 5% per asset
    max_weight=0.30,  # Max 30% per asset
    risk_free_rate=0.02
)

# Optimize
result = optimizer.optimize(returns_df)

# Use the weights
print(f"Portfolio weights: {result.weights}")
print(f"Expected Sharpe: {result.sharpe_ratio:.4f}")
print(f"Risk contributions: {result.risk_contributions}")
```

### Compare Just 2-3 Methods

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['equal_weight', 'risk_parity', 'maximum_sharpe'],
    max_weight=0.40,  # Max 40% per asset
    risk_free_rate=0.02
)
```

## 📖 Understanding Your Results

### Key Metrics Explained

**Sharpe Ratio** (higher is better, >1 is good)
- Measures risk-adjusted return
- `(Return - RiskFreeRate) / Volatility`
- Best method typically has highest Sharpe

**Diversification Ratio** (higher is better, >1 means diversified)
- Measures diversification benefit
- `WeightedVolatilities / PortfolioVolatility`
- >1.5 is well diversified

**Expected Volatility** (lower is better)
- Portfolio risk/volatility
- Lower = less risky portfolio

**Max Weight**
- Largest single position
- Lower = more diversified

### Choosing a Method

**Question: Which method should I use?**

**Answer:** Look at the comparison results!

```
Best Sharpe Ratio: risk_parity         → Usually best overall choice
Best Diversification: hierarchical_risk_parity  → Most diversified
Lowest Volatility: minimum_variance     → Lowest risk
```

**Rules of Thumb:**
- **Want simplicity?** → Equal Weight
- **Want balance?** → Risk Parity
- **Want low risk?** → Minimum Variance
- **Want high returns?** → Maximum Sharpe
- **Want diversification?** → Max Diversification or HRP

## 🎯 Real-World Examples

### Example 1: Conservative Investor

**Goal:** Minimize risk

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['minimum_variance', 'risk_parity', 'equal_weight'],
    max_weight=0.25,  # Force diversification
    risk_free_rate=0.02
)

# Use the lowest volatility method
best_method = comparison.lowest_volatility_method
weights = comparison.results[best_method].weights
```

### Example 2: Balanced Investor

**Goal:** Balance risk and return

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['risk_parity', 'equal_weight', 'inverse_volatility'],
    max_weight=0.30,
    risk_free_rate=0.02
)

# Use Risk Parity (usually best for balanced)
weights = comparison.results['risk_parity'].weights
```

### Example 3: Aggressive Investor

**Goal:** Maximize returns

```python
comparison = compare_portfolio_methods(
    returns=returns_df,
    methods=['maximum_sharpe', 'maximum_diversification'],
    max_weight=0.50,  # Allow concentration
    risk_free_rate=0.02
)

# Use method with highest Sharpe
best_method = comparison.best_sharpe_method
weights = comparison.results[best_method].weights
```

### Example 4: Your Custom Assets

```python
from src.portfolio_optimization import compare_portfolio_methods
from src.data_sources import get_default_data_source
from datetime import datetime
import pandas as pd

# Define your assets
MY_ASSETS = ['AAPL', 'MSFT', 'GOOGL', 'BND', 'GLD', 'VNQ']

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

# Run comparison
comparison = compare_portfolio_methods(
    returns=returns_df,
    max_weight=0.30,  # Max 30% per stock
    risk_free_rate=0.02
)

# Results
print(f"\nBest method for my assets: {comparison.best_sharpe_method}")
print("\nRecommended portfolio weights:")
best_weights = comparison.results[comparison.best_sharpe_method].weights
for asset, weight in best_weights.items():
    print(f"  {asset}: {weight*100:.1f}%")
```

## 📁 Working with Saved Results

### Load and Analyze Results

```python
import pandas as pd
import json

# Load comparison metrics
comparison_df = pd.read_csv('portfolio_optimization_results/*_comparison.csv')

# Show top 3 methods by Sharpe ratio
top_3 = comparison_df.nlargest(3, 'sharpe_ratio')
print(top_3[['method', 'sharpe_ratio', 'expected_volatility']])

# Load weights
weights_df = pd.read_csv('portfolio_optimization_results/*_weights.csv', index_col=0)
print(weights_df)

# Load summary
with open('portfolio_optimization_results/*_summary.json', 'r') as f:
    summary = json.load(f)
    print(f"Best method: {summary['best_sharpe_method']}")
```

### Export to Excel

```python
import pandas as pd

# Load data
comparison_df = pd.read_csv('portfolio_optimization_results/*_comparison.csv')
weights_df = pd.read_csv('portfolio_optimization_results/*_weights.csv', index_col=0)

# Create Excel file with multiple sheets
with pd.ExcelWriter('portfolio_analysis.xlsx') as writer:
    comparison_df.to_excel(writer, sheet_name='Comparison', index=False)
    weights_df.to_excel(writer, sheet_name='Weights')

print("✓ Saved to portfolio_analysis.xlsx")
```

## ❓ FAQ

**Q: How long does it take?**
A: Full comparison (7 methods) takes 30-60 seconds. Quick comparison (3 methods) takes 10-20 seconds.

**Q: Can I use my own assets?**
A: Yes! Just modify the `symbols` list in the demo or use the code examples above.

**Q: Which method is best?**
A: It depends on your goals! The comparison shows you which performs best. Generally, Risk Parity is a good balanced choice.

**Q: Can I adjust the constraints?**
A: Yes! Use `min_weight` and `max_weight` parameters. Example: `max_weight=0.30` limits any position to 30%.

**Q: How do I interpret the weights?**
A: Weights show allocation percentage. `0.25` means 25% of portfolio. They sum to 1.0 (100%).

**Q: What if a method fails?**
A: The comparison continues with other methods. Check your data for NaN values if problems persist.

**Q: Can I save/load results?**
A: Yes! Results are automatically saved to `portfolio_optimization_results/`. Load CSVs with pandas.

## 🆘 Troubleshooting

### Problem: "No module named 'src'"

**Solution:**
```bash
cd dual_momentum_system  # Make sure you're in the right directory
pwd  # Should show .../dual_momentum_system
```

### Problem: "No results found"

**Solution:** Run the comparison first
```bash
python3 examples/portfolio_optimization_comparison_demo.py
```

### Problem: Visualizations don't appear

**Solution:** Install matplotlib
```bash
pip3 install matplotlib seaborn
```

### Problem: "Optimization did not converge"

**Solution:** Check your returns data
```python
# Verify data quality
print(returns_df.isnull().sum())  # Should be all zeros
print(returns_df.describe())
returns_df = returns_df.dropna()  # Remove NaN values
```

## 🎓 Learn More

| Document | Purpose |
|----------|---------|
| **RUNNING_PORTFOLIO_OPTIMIZATION.md** | Complete running guide |
| **PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md** | Detailed method descriptions |
| **QUICK_START_PORTFOLIO_OPTIMIZATION.md** | Quick reference |
| **PORTFOLIO_OPTIMIZATION_QUICK_REFERENCE.md** | Cheat sheet |
| **HOW_TO_RUN_PORTFOLIO_OPTIMIZATION.md** | All ways to run |

## ✅ Summary Checklist

To run and view portfolio optimization:

- [ ] `cd dual_momentum_system`
- [ ] `./run_portfolio_comparison.sh` (select option 1)
- [ ] `python3 examples/view_portfolio_results.py`
- [ ] `python3 examples/view_portfolio_results.py --html`
- [ ] Open `portfolio_optimization_results/portfolio_optimization_report.html`
- [ ] Choose best method from results
- [ ] Use weights for your portfolio!

## 🎉 You're Ready!

**Everything you need:**
- ✅ 7 optimization methods implemented
- ✅ Easy-to-use comparison framework
- ✅ Automatic visualizations
- ✅ HTML reports
- ✅ Complete documentation
- ✅ Working examples

**Get started now:**
```bash
cd dual_momentum_system
./run_portfolio_comparison.sh
```

**Good luck with your portfolio optimization!** 📈✨
