# Streamlit Portfolio Optimization Guide

## 🎯 Overview

Portfolio optimization has been fully integrated into the Streamlit dashboard! Users can now compare 7 portfolio construction methods through an intuitive web interface.

## 🚀 How to Access

### Start the Dashboard

```bash
cd dual_momentum_system
streamlit run frontend/app.py
```

### Navigate to Portfolio Optimization

In the sidebar, click:
**💼 Portfolio Optimization**

## 📋 User Flow

### Tab 1: ⚙️ Configuration

**Asset Selection:**
1. Choose "Default (Multi-Asset)" or "Custom"
2. For custom: Enter symbols (comma or line-separated)
   - Example: `SPY, AGG, GLD, TLT`
   - Or one per line
3. See confirmation: "Selected N assets: ..."

**Date Range:**
- Select start and end dates
- Default: Last 3 years
- Longer periods = more robust estimates
- See duration: "Analysis period: X.X years"

**Optimization Settings:**

**Method Selection** (checkboxes):
- ☑️ Equal Weight
- ☑️ Inverse Volatility
- ☑️ Minimum Variance
- ☑️ Maximum Sharpe
- ☑️ Risk Parity
- ☑️ Max Diversification
- ☑️ HRP

**Portfolio Constraints:**
- Min Weight (%): Minimum allocation per asset (default: 0%)
- Max Weight (%): Maximum allocation per asset (default: 50%)

**Risk-Free Rate:**
- Annual risk-free rate for Sharpe calculation
- Default: 2.0%

### Tab 2: 🚀 Run Optimization

**Configuration Summary:**
- Shows selected assets, methods, and period
- Expandable method descriptions

**Run Button:**
- Click "🚀 Start Optimization"
- Progress bar shows:
  - Loading price data (10-40%)
  - Calculating returns (40-50%)
  - Running optimization (50-90%)
  - Complete! (100%)
- Success message with balloons 🎈
- Auto-navigates to Results tab

### Tab 3: 📊 Results

#### 🏆 Best Methods (Top Cards)

Three cards showing:
1. **Best Sharpe Ratio** - Highest risk-adjusted returns
2. **Best Diversification** - Most diversified portfolio
3. **Lowest Volatility** - Least risky portfolio

Each shows method name and score.

#### 📊 Method Comparison Table

Sortable table with:
- Method names
- Annual Return (%)
- Annual Volatility (%)
- Sharpe Ratio
- Diversification Ratio

#### 💼 Portfolio Weights Table

Shows allocation percentages for each asset across all methods.

#### 📈 Visual Analysis (4 Tabs)

1. **Sharpe Comparison**
   - Bar chart of Sharpe ratios
   - Best method highlighted in green

2. **Weights Heatmap**
   - Color-coded heatmap
   - Red = low allocation, Green = high allocation
   - Shows allocation patterns across methods

3. **Risk-Return**
   - Scatter plot
   - X-axis: Volatility (risk)
   - Y-axis: Return
   - Best Sharpe marked with green star

4. **Weight Distribution**
   - Stacked bar chart
   - Shows how each method allocates across assets

#### 🔍 Detailed Results by Method

**Dropdown selector:**
- Choose any method to see details

**Shows:**
- Performance metrics (Return, Volatility, Sharpe, Diversification)
- Portfolio weights
- Risk contributions (bar chart showing contribution by asset)

#### 💾 Download Results

Three download buttons:
1. **📥 Comparison CSV** - All comparison metrics
2. **📥 Weights CSV** - Portfolio weights
3. **📥 Summary JSON** - Summary statistics

Files include timestamp in filename.

## 🎨 Visual Elements

### Interactive Charts
All charts are Plotly interactive:
- Hover for details
- Zoom in/out
- Pan
- Download as PNG
- Full-screen mode

### Color Coding
- **Green**: Best performing method
- **Steelblue**: Other methods
- **Red to Yellow to Green**: Heatmap gradient

### Status Messages
- ✅ Success (green)
- ⚠️ Warning (yellow)
- ❌ Error (red)
- ℹ️ Info (blue)

## 📱 Responsive Design

The interface adapts to screen size:
- Desktop: Full multi-column layout
- Tablet: Adjusted column widths
- Mobile: Stacked single column

## 💡 Usage Tips

### Quick Start
1. Go to **Configuration** tab
2. Leave defaults (works for demo)
3. Go to **Run Optimization** tab
4. Click "Start Optimization"
5. View **Results** tab

### Custom Assets
1. In Configuration, select "Custom"
2. Enter your asset symbols
3. Adjust constraints as needed
4. Run optimization

### Conservative Portfolio
- Max Weight: 25%
- Select: Minimum Variance, Risk Parity, Equal Weight

### Aggressive Portfolio
- Max Weight: 50%
- Select: Maximum Sharpe, Max Diversification

### Full Analysis
- Select all 7 methods
- Review all 4 visualization tabs
- Download results for reporting

## 🔧 Technical Details

### Data Loading
- Uses `get_default_data_source()`
- Fetches from yfinance by default
- Handles missing data gracefully
- Progress tracking for each symbol

### Calculations
- Returns: Daily percentage changes
- Annualization: 252 trading days
- Risk-free rate: User-configurable

### Session State
Variables stored in `st.session_state`:
- `portfolio_opt_symbols`: Selected assets
- `portfolio_opt_start_date`: Start date
- `portfolio_opt_end_date`: End date
- `portfolio_opt_methods`: Selected methods
- `portfolio_opt_min_weight`: Min weight constraint
- `portfolio_opt_max_weight`: Max weight constraint
- `portfolio_opt_risk_free_rate`: Risk-free rate
- `portfolio_opt_comparison`: Comparison results
- `portfolio_opt_returns`: Returns DataFrame
- `portfolio_opt_completed`: Completion flag

### Error Handling
- Missing data: Warning shown, continues with available
- Invalid symbols: Warning shown
- Optimization failure: Error message with traceback
- No results: Info message prompts to run first

## 🎯 Example Workflows

### Workflow 1: Quick Demo
```
1. Launch Streamlit
2. Click "💼 Portfolio Optimization"
3. Go to "Run Optimization" tab
4. Click "Start Optimization" (uses defaults)
5. Explore Results tab
```

### Workflow 2: Custom Portfolio
```
1. Click "💼 Portfolio Optimization"
2. Configuration tab:
   - Select "Custom"
   - Enter: AAPL, MSFT, GOOGL, BND, GLD
   - Set Max Weight: 30%
3. Run Optimization tab:
   - Click "Start Optimization"
4. Results tab:
   - View best methods
   - Download Weights CSV
```

### Workflow 3: Conservative Analysis
```
1. Configuration tab:
   - Default assets (Multi-Asset)
   - Uncheck: Maximum Sharpe
   - Keep: Minimum Variance, Risk Parity, Equal Weight
   - Set Max Weight: 25%
2. Run Optimization
3. Results:
   - Check Lowest Volatility method
   - View Risk Contributions
   - Download Summary JSON
```

### Workflow 4: Method Comparison
```
1. Configuration: Select all 7 methods
2. Run Optimization
3. Results:
   - Compare all methods in table
   - Review Sharpe Comparison chart
   - Review Risk-Return scatter
   - Download Comparison CSV for analysis
```

## 🎓 Understanding Results

### Sharpe Ratio
- Risk-adjusted return measure
- Formula: (Return - RiskFree) / Volatility
- **Good:** > 1.0
- **Excellent:** > 2.0

### Diversification Ratio
- Measures diversification benefit
- Formula: WeightedVols / PortfolioVol
- **Well diversified:** > 1.5
- **Highly diversified:** > 2.0

### Risk Contributions
- Shows each asset's contribution to total risk
- Risk Parity aims for equal contributions
- Helpful for understanding risk sources

## 🔍 Troubleshooting

### "No optimization results yet"
**Solution:** Run optimization first in the "Run Optimization" tab

### Data loading fails
**Solutions:**
- Check internet connection
- Verify symbol tickers are valid
- Try different date range
- Use default assets first

### Results look unexpected
**Solutions:**
- Check date range (longer is usually better)
- Verify constraints (min/max weights)
- Try default settings first
- Compare multiple methods

### Charts don't display
**Solutions:**
- Refresh browser
- Check browser console for errors
- Ensure plotly is installed: `pip install plotly`

## 📊 Output Files

When you download results, files are named with timestamp:

```
portfolio_comparison_20241029_142530.csv
portfolio_weights_20241029_142530.csv
portfolio_summary_20241029_142530.json
```

### CSV Format (Comparison)
```csv
method,annual_return,annual_volatility,sharpe_ratio,diversification_ratio
Equal Weight,7.24,8.90,0.8234,1.4567
Risk Parity,7.45,8.20,0.9091,1.5234
...
```

### CSV Format (Weights)
```csv
,equal_weight,risk_parity,maximum_sharpe
SPY,0.167,0.143,0.285
AGG,0.167,0.245,0.189
...
```

### JSON Format (Summary)
```json
{
  "n_methods_compared": 7,
  "n_assets": 6,
  "best_sharpe_method": "risk_parity",
  "best_sharpe_ratio": 0.9091,
  ...
}
```

## 🎉 Benefits

### For Users
- ✅ No coding required
- ✅ Interactive visualizations
- ✅ Real-time feedback
- ✅ Professional outputs
- ✅ Easy to share (download results)

### For Analysts
- ✅ Quick experimentation
- ✅ Multiple method comparison
- ✅ Export for further analysis
- ✅ Visual insights
- ✅ Reproducible results

### For Presentations
- ✅ Professional visualizations
- ✅ Interactive charts
- ✅ Downloadable results
- ✅ Clear summary metrics

## 📚 Next Steps

1. **Try the demo**: Use default settings
2. **Experiment**: Try different assets and constraints
3. **Compare methods**: Run all 7 methods
4. **Download results**: Save for your records
5. **Integrate**: Use optimal weights in your portfolio

## 🔗 Related Documentation

- **PORTFOLIO_OPTIMIZATION_METHODS_GUIDE.md** - Detailed method descriptions
- **USER_GUIDE_PORTFOLIO_OPTIMIZATION.md** - Complete user guide
- **QUICK_START_PORTFOLIO_OPTIMIZATION.md** - Quick reference
- **START_HERE.md** - Ultra-quick start

## ✅ Summary

**Portfolio Optimization is now in Streamlit!**

**Access:** Dashboard sidebar → 💼 Portfolio Optimization

**Steps:**
1. Configure assets and settings
2. Run optimization
3. View results and visualizations
4. Download outputs

**Output:**
- Best methods identified
- Comparison table
- 4 interactive charts
- Detailed results
- Downloadable files

**Time:** 30-60 seconds for full comparison

**Perfect for:** Quick analysis, presentations, decision-making

🎊 **Enjoy your optimized portfolios!** 📈
