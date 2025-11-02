# 🎯 How to Access the Optimization UI in Streamlit

## Two Different Optimization Features

Your Streamlit app has **TWO** optimization features. Here's how to find them:

---

## 1️⃣ **Hyperparameter Optimization** (For Backtesting Parameters)

**What it does:** Compares different optimization methods (Grid Search, Random Search, Bayesian) to find the best strategy parameters for backtesting.

### How to Access:

1. **Start the Streamlit app:**
   ```bash
   cd dual_momentum_system
   streamlit run frontend/app.py
   ```

2. **In the sidebar, click:**
   ```
   🎯 Hyperparameter Tuning
   ```

3. **Click on the 4th tab:**
   ```
   🔬 Compare Methods
   ```

4. **Configure and run:**
   - Select which methods to compare:
     - ✅ Grid Search
     - ✅ Random Search  
     - ✅ Bayesian Optimization
   - Click "🔬 Start Method Comparison"
   - View results showing which method performs best

### What You'll See:
- Sharpe Ratio comparison chart
- Time per trial comparison
- Convergence plots
- Best parameters from each method
- Comprehensive comparison table

---

## 2️⃣ **Portfolio Optimization** (For Asset Allocation)

**What it does:** Compares different portfolio construction methods (Equal Weight, Risk Parity, Maximum Sharpe, etc.) to find optimal asset weights.

### How to Access:

1. **Start the Streamlit app** (same as above)

2. **In the sidebar, click:**
   ```
   💼 Portfolio Optimization
   ```

3. **In the app:**
   - **Tab 1:** Configure assets and constraints
   - **Tab 2:** Run optimization
   - **Tab 3:** View results and charts

### What You'll See:
- 7 portfolio optimization methods:
  - Equal Weight
  - Inverse Volatility
  - Minimum Variance
  - Maximum Sharpe Ratio
  - Risk Parity
  - Maximum Diversification
  - Hierarchical Risk Parity
- Weights comparison
- Risk/return analysis
- Interactive charts

---

## 🚀 Quick Start Guide

### Step-by-Step: Running Hyperparameter Optimization Comparison

```bash
# 1. Start the app
cd /workspace/dual_momentum_system
streamlit run frontend/app.py

# 2. Navigate to: 🎯 Hyperparameter Tuning
# 3. Go to tab: 🔬 Compare Methods
# 4. Check the methods you want to compare
# 5. Click: 🔬 Start Method Comparison
# 6. Wait for results
# 7. View comparison charts
```

### Step-by-Step: Running Portfolio Optimization

```bash
# 1. Start the app (same as above)
# 2. Navigate to: 💼 Portfolio Optimization
# 3. Tab 1: Select assets (e.g., SPY, AGG, GLD)
# 4. Tab 2: Select methods and click Run
# 5. Tab 3: View results
```

---

## 📍 Navigation Menu

When you start the app, you'll see this sidebar menu:

```
🧭 Navigation
  ○ 🏠 Home
  ○ 🛠️ Strategy Builder
  ○ 📊 Backtest Results
  ○ 🔄 Compare Strategies
  ○ 🎯 Hyperparameter Tuning          ← Click here for backtest optimization
  ○ 💼 Portfolio Optimization         ← Click here for portfolio optimization
  ○ 🗂️ Asset Universe Manager
```

---

## ❓ Troubleshooting

### "I don't see Portfolio Optimization in the sidebar"

**Solution:** Make sure you're running the latest version:
```bash
cd /workspace/dual_momentum_system
git pull  # If using git
streamlit run frontend/app.py
```

### "I can't find the Compare Methods tab"

**Steps:**
1. Click "🎯 Hyperparameter Tuning" in the sidebar
2. Look for tabs at the top of the page
3. The 4th tab should be "🔬 Compare Methods"
4. If you don't see it, refresh the page (Ctrl+R or Cmd+R)

### "The app won't start"

**Check dependencies:**
```bash
cd /workspace/dual_momentum_system
pip install -r requirements.txt
```

**Check if Streamlit is installed:**
```bash
streamlit --version
# If not installed:
pip install streamlit
```

---

## 🎨 Visual Guide

### Hyperparameter Tuning Page Layout:

```
┌─────────────────────────────────────────────┐
│  🎯 Hyperparameter Tuning                   │
├─────────────────────────────────────────────┤
│  [⚙️ Configuration] [🚀 Run] [📊 Results] [🔬 Compare Methods] ← Click this!
├─────────────────────────────────────────────┤
│                                             │
│  🔬 Compare Optimization Methods            │
│                                             │
│  Select Methods:                            │
│  ☑ Grid Search                              │
│  ☑ Random Search                            │
│  ☑ Bayesian Optimization                    │
│                                             │
│  [🔬 Start Method Comparison]               │
│                                             │
└─────────────────────────────────────────────┘
```

### Portfolio Optimization Page Layout:

```
┌─────────────────────────────────────────────┐
│  💼 Portfolio Optimization                  │
├─────────────────────────────────────────────┤
│  [⚙️ Configuration] [🚀 Run] [📊 Results]   │
├─────────────────────────────────────────────┤
│                                             │
│  Select Assets: [SPY] [AGG] [GLD] ...       │
│  Select Methods:                            │
│  ☑ Equal Weight                             │
│  ☑ Risk Parity                              │
│  ☑ Maximum Sharpe                           │
│  ...                                        │
│                                             │
│  [▶ Run Optimization]                       │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📝 Summary

**For comparing backtest optimization methods:**
→ Go to **🎯 Hyperparameter Tuning** → **🔬 Compare Methods** tab

**For comparing portfolio allocation methods:**
→ Go to **💼 Portfolio Optimization** page

Both features are fully implemented and working! ✅

---

## 🆘 Still Can't Find It?

Run this test to verify everything is set up:

```bash
cd /workspace/dual_momentum_system
python3 -c "
from frontend.page_modules import hyperparameter_tuning, portfolio_optimization
print('✓ Hyperparameter Tuning module found')
print('✓ Portfolio Optimization module found')
print('\nBoth pages are available in the app!')
"
```

If you see both checkmarks, the pages are there - just need to start the Streamlit app!

---

**Need more help?** Check these files:
- `QUICK_START_METHOD_COMPARISON.md` - Hyperparameter comparison guide
- `STREAMLIT_PORTFOLIO_OPTIMIZATION_GUIDE.md` - Portfolio optimization UI guide
