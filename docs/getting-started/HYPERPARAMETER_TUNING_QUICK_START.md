# Hyperparameter Tuning - Quick Start Guide

## 🚀 What's New

Your backtesting system now has powerful hyperparameter optimization capabilities!

## ⚡ Quick Usage

### Option 1: Web Dashboard (Easiest)

```bash
# Start the dashboard
cd dual_momentum_system
streamlit run frontend/app.py
```

Then:
1. Click **🎯 Hyperparameter Tuning** in sidebar
2. Configure your optimization in the **⚙️ Configuration** tab
3. Run optimization in the **🚀 Run Optimization** tab
4. View results in the **📊 Results** tab

### Option 2: Python Script

```python
from datetime import datetime, timedelta
from src.backtesting import BacktestEngine, HyperparameterTuner, ParameterSpace
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources.multi_source import MultiSourceDataProvider

# Load data
data_provider = MultiSourceDataProvider()
price_data = {}
for symbol in ["SPY", "EFA", "EEM", "AGG", "TLT", "GLD"]:
    price_data[symbol] = data_provider.fetch_data(
        symbol, 
        start_date=datetime.now() - timedelta(days=5*365),
        end_date=datetime.now()
    )

# Create engine
engine = BacktestEngine(initial_capital=100000, commission=0.001, slippage=0.0005)

# Create tuner
tuner = HyperparameterTuner(
    strategy_class=DualMomentumStrategy,
    backtest_engine=engine,
    price_data=price_data,
    base_config={'safe_asset': 'AGG'},
)

# Define parameters to optimize
param_space = [
    ParameterSpace('lookback_period', 'int', values=[126, 189, 252, 315]),
    ParameterSpace('position_count', 'int', values=[1, 2, 3]),
]

# Run optimization
results = tuner.grid_search(
    param_space=param_space,
    metric='sharpe_ratio',
    higher_is_better=True,
)

# Get results
print(f"Best Sharpe Ratio: {results.best_score:.4f}")
print(f"Best Parameters: {results.best_params}")
```

## 🎯 Available Optimization Methods

### 1. Grid Search
**Best for**: Small parameter spaces (< 100 combinations)
```python
results = tuner.grid_search(param_space, metric='sharpe_ratio')
```

### 2. Random Search
**Best for**: Medium spaces, quick exploration
```python
results = tuner.random_search(param_space, n_trials=50, metric='sharpe_ratio')
```

### 3. Bayesian Optimization
**Best for**: Large spaces, expensive evaluations (requires `pip install optuna`)
```python
results = tuner.bayesian_optimization(param_space, n_trials=50, metric='sharpe_ratio')
```

## 📊 Available Metrics

Optimize for any of these metrics:
- `sharpe_ratio` - Risk-adjusted return (most common) ⭐
- `sortino_ratio` - Downside risk-adjusted return
- `calmar_ratio` - Return vs max drawdown
- `annual_return` - Annualized return
- `total_return` - Total return
- `max_drawdown` - Maximum drawdown (minimize)

## 🎛️ Tunable Parameters

### Dual Momentum Strategy
- `lookback_period` (int): 63-378 (3-18 months)
- `position_count` (int): 1-10 assets
- `absolute_threshold` (float): -0.05 to 0.10
- `use_volatility_adjustment` (bool): True/False
- `rebalance_frequency` (categorical): 'weekly', 'monthly', 'quarterly'

## 💾 Save Results

```python
# Save all formats (CSV, JSON, Pickle)
saved_files = tuner.save_results(
    results, 
    output_dir="optimization_results",
    prefix="my_optimization"
)
```

## 📖 Full Documentation

- **Complete Guide**: `dual_momentum_system/HYPERPARAMETER_TUNING_GUIDE.md`
- **Implementation Details**: `HYPERPARAMETER_TUNING_IMPLEMENTATION.md`
- **Example Script**: `dual_momentum_system/examples/hyperparameter_tuning_demo.py`
- **Tests**: `dual_momentum_system/tests/test_hyperparameter_tuner.py`

## 🔧 Installation

All dependencies are already in `requirements.txt`. Just run:

```bash
pip install -r dual_momentum_system/requirements.txt
```

For Bayesian optimization:
```bash
pip install optuna
```

## 📁 New Files

### Core Implementation
- `src/backtesting/hyperparameter_tuner.py` - Main optimization engine
- `src/backtesting/__init__.py` - Updated exports

### Frontend
- `frontend/pages/hyperparameter_tuning.py` - Web dashboard page
- `frontend/app.py` - Added navigation

### Examples & Tests
- `examples/hyperparameter_tuning_demo.py` - Complete demo
- `tests/test_hyperparameter_tuner.py` - Unit tests

### Documentation
- `HYPERPARAMETER_TUNING_GUIDE.md` - Complete user guide (800+ lines)
- `HYPERPARAMETER_TUNING_IMPLEMENTATION.md` - Implementation summary
- `HYPERPARAMETER_TUNING_QUICK_START.md` - This file

## 💡 Pro Tips

1. **Start Small**: Begin with 2-3 values per parameter
2. **Use Benchmarks**: Compare against buy-and-hold
3. **Validate Results**: Test on out-of-sample data
4. **Save Everything**: Export results for later analysis
5. **Try Multiple Metrics**: Don't optimize for just one metric

## 🎓 Example Workflow

```python
# 1. Quick exploration with random search
results_random = tuner.random_search(param_space, n_trials=20)

# 2. Refine with Bayesian optimization
refined_space = [
    ParameterSpace('lookback_period', 'int', 
                   values=[results_random.best_params['lookback_period']-63,
                          results_random.best_params['lookback_period'],
                          results_random.best_params['lookback_period']+63]),
    # ... other parameters
]
results_bayesian = tuner.bayesian_optimization(refined_space, n_trials=30)

# 3. Validate on separate period
# ... test best_params on validation data

# 4. Save final results
tuner.save_results(results_bayesian, "final_results")
```

## ❓ Common Questions

**Q: How long does optimization take?**
A: Depends on parameter space size and backtest period. Typically 1-10 seconds per trial.

**Q: Can I optimize multiple strategies?**
A: Yes! Just pass different `strategy_class` to the tuner.

**Q: What if optimization fails?**
A: Check the error messages in the results DataFrame. Common issues:
- Insufficient data history
- Invalid parameter combinations
- Missing safe asset data

**Q: How do I avoid overfitting?**
A: Always validate on out-of-sample data. Use walk-forward testing.

## 🚀 Next Steps

1. **Try the demo**: `python examples/hyperparameter_tuning_demo.py`
2. **Open the dashboard**: Run Streamlit and explore the UI
3. **Read the full guide**: See `HYPERPARAMETER_TUNING_GUIDE.md`
4. **Optimize your strategy**: Start with your existing configuration

## 🎉 You're Ready!

You now have a complete hyperparameter optimization system. Happy tuning! 🚀

---

**Need Help?**
- Full documentation: `HYPERPARAMETER_TUNING_GUIDE.md`
- Example code: `examples/hyperparameter_tuning_demo.py`
- Tests: `tests/test_hyperparameter_tuner.py`
