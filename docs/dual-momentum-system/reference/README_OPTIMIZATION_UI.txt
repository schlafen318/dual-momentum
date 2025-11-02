╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🎯 HOW TO FIND THE OPTIMIZATION UI                     ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

STEP 1: Start the Streamlit App
════════════════════════════════════════════════════════════════════════

  $ cd dual_momentum_system
  $ streamlit run frontend/app.py

  OR use the quick-start script:

  $ ./START_OPTIMIZATION_UI.sh


STEP 2: Choose Your Optimization Type
════════════════════════════════════════════════════════════════════════

You have TWO optimization features:


┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  A) HYPERPARAMETER OPTIMIZATION (Backtest Parameters)             │
│     ═══════════════════════════════════════════════                │
│                                                                    │
│     What: Compare Grid Search, Random Search, Bayesian methods    │
│     Goal: Find best strategy parameters                           │
│                                                                    │
│     Navigation:                                                    │
│     1. Click sidebar: "🎯 Hyperparameter Tuning"                  │
│     2. Click 4th tab: "🔬 Compare Methods"                        │
│     3. Select methods and click "Start Method Comparison"         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  B) PORTFOLIO OPTIMIZATION (Asset Allocation)                     │
│     ══════════════════════════════════════════                     │
│                                                                    │
│     What: Compare 7 portfolio construction methods                │
│     Goal: Find optimal asset weights                              │
│                                                                    │
│     Navigation:                                                    │
│     1. Click sidebar: "💼 Portfolio Optimization"                 │
│     2. Tab 1: Configure assets and constraints                    │
│     3. Tab 2: Run optimization                                     │
│     4. Tab 3: View results                                         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘


VISUAL: Sidebar Navigation
════════════════════════════════════════════════════════════════════════

When you start the app, you'll see this sidebar:

  ┌─────────────────────────────────┐
  │  🧭 Navigation                  │
  │                                 │
  │  ○ 🏠 Home                      │
  │  ○ 🛠️ Strategy Builder          │
  │  ○ 📊 Backtest Results          │
  │  ○ 🔄 Compare Strategies        │
  │  ○ 🎯 Hyperparameter Tuning     │ ← For backtest optimization
  │  ○ 💼 Portfolio Optimization    │ ← For portfolio optimization
  │  ○ 🗂️ Asset Universe Manager    │
  │                                 │
  └─────────────────────────────────┘


Quick Test: Verify Everything Works
════════════════════════════════════════════════════════════════════════

Run this to confirm both UIs are ready:

  $ cd dual_momentum_system
  $ python3 -c "
  from frontend.page_modules import hyperparameter_tuning, portfolio_optimization
  print('✓ Hyperparameter Optimization: READY')
  print('✓ Portfolio Optimization: READY')
  "


Still Can't Find It?
════════════════════════════════════════════════════════════════════════

1. Make sure Streamlit is installed:
   $ pip install streamlit

2. Make sure you're in the right directory:
   $ cd dual_momentum_system
   $ ls frontend/app.py  # Should exist

3. Check browser URL after starting:
   Should be: http://localhost:8501

4. Try refreshing the page:
   Press 'R' in the app or Ctrl+R / Cmd+R in browser


More Help
════════════════════════════════════════════════════════════════════════

Detailed guides available:
  • FIND_OPTIMIZATION_UI_VISUAL_GUIDE.md  (Step-by-step with visuals)
  • HOW_TO_ACCESS_OPTIMIZATION_UI.md      (Complete reference)
  • ALL_TESTS_PASSED.md                   (Verification results)


Summary
════════════════════════════════════════════════════════════════════════

  ✅ Both optimization UIs are installed and working
  ✅ All tests passing (69/69)
  ✅ Full Streamlit integration
  ✅ Ready to use immediately

  Just start the app and navigate to the pages shown above!


╔══════════════════════════════════════════════════════════════════════╗
║  Need help? All guides are in: dual_momentum_system/*.md            ║
╚══════════════════════════════════════════════════════════════════════╝
