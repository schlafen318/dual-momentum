# Quick Start: Optimization Method Comparison

Compare Grid Search, Random Search, and Bayesian Optimization to find the best method for your parameter tuning.

## 30-Second Start (Frontend)

1. Open Streamlit dashboard
2. Go to **🎯 Hyperparameter Tuning** → **🔬 Compare Methods**
3. Check methods to compare (Grid Search, Random Search, Bayesian)
4. Click **🔬 Start Method Comparison**
5. View which method performs best!

## 2-Minute Start (Python)

```python
from src.backtesting import HyperparameterTuner, ParameterSpace, BacktestEngine
from src.strategies.dual_momentum import DualMomentumStrategy

# Setup (your data and engine)
tuner = HyperparameterTuner(
    strategy_class=DualMomentumStrategy,
    backtest_engine=BacktestEngine(initial_capital=100000),
    price_data=your_price_data,
    base_config={'safe_asset': 'AGG'},
)

# Define what to optimize
param_space = [
    ParameterSpace('lookback_period', 'int', values=[126, 189, 252]),
    ParameterSpace('position_count', 'int', values=[1, 2, 3]),
]

# Compare methods
comparison = tuner.compare_optimization_methods(
    param_space=param_space,
    n_trials=30,
    metric='sharpe_ratio',
)

# Results
print(f"Winner: {comparison.best_method}")
print(f"Score: {comparison.best_overall_score:.4f}")
print(comparison.comparison_metrics)
```

## What You Get

- **Winner Identification** - Which method found the best parameters
- **Performance Table** - Score, time, and efficiency for each method
- **Visual Comparisons** - Charts showing convergence and efficiency
- **Best Parameters** - From each method
- **Export Options** - Save results as CSV or JSON

## Run Demo

```bash
cd dual_momentum_system
python examples/optimization_method_comparison_demo.py

# Or quick version:
python examples/optimization_method_comparison_demo.py --quick
```

## When to Use Each Method

| Method | Best For | Speed | Accuracy |
|--------|----------|-------|----------|
| Grid Search | Small search spaces (<100 combos) | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| Random Search | Large search spaces | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| Bayesian | Expensive evaluations | ⚡ | ⭐⭐⭐⭐⭐ |

## More Information

- **Detailed Guide**: See `OPTIMIZATION_METHOD_COMPARISON_GUIDE.md`
- **Implementation Details**: See `OPTIMIZATION_METHOD_COMPARISON_FEATURE.md`
- **API Docs**: See docstrings in `src/backtesting/hyperparameter_tuner.py`

## Questions?

The comparison will tell you which method works best for YOUR specific problem!
