# Optimization Method Comparison Guide

This guide explains how to use and compare multiple optimization methods for backtesting strategy parameters in the Dual Momentum System.

## Overview

The system now supports comparing multiple optimization methods to find which works best for your specific problem. Three methods are available:

1. **Grid Search** - Exhaustive search over all parameter combinations
2. **Random Search** - Random sampling from the parameter space
3. **Bayesian Optimization** - Smart search using probabilistic models (requires Optuna)

## Why Compare Methods?

Different optimization methods have different strengths and weaknesses:

- **Grid Search**
  - ✅ Guarantees finding the best solution in the search space
  - ✅ Systematic and reproducible
  - ❌ Computationally expensive for large search spaces
  - ❌ Doesn't scale well with number of parameters

- **Random Search**
  - ✅ Good for large search spaces
  - ✅ Simple and fast
  - ✅ Often finds near-optimal solutions quickly
  - ❌ No guarantee of finding the best solution
  - ❌ Doesn't learn from previous trials

- **Bayesian Optimization**
  - ✅ Most sample-efficient for expensive evaluations
  - ✅ Learns from previous trials
  - ✅ Balances exploration and exploitation
  - ❌ Requires Optuna dependency
  - ❌ Can get stuck in local optima

## Using the Frontend (Streamlit Dashboard)

### Step 1: Configure Parameters

Navigate to the **Hyperparameter Tuning** page and configure:

1. **Backtest Settings** (Configuration tab)
   - Date range
   - Initial capital
   - Transaction costs
   - Benchmark

2. **Parameter Space**
   - Define parameters to optimize (e.g., lookback_period, position_count)
   - Specify value ranges or discrete values
   - Add/remove parameters as needed

### Step 2: Run Method Comparison

1. Go to the **Compare Methods** tab
2. Select which methods to compare (check one or more):
   - ☑️ Grid Search
   - ☑️ Random Search
   - ☑️ Bayesian Optimization

3. Review configuration summary
4. Click **🔬 Start Method Comparison**

### Step 3: Analyze Results

The comparison results include:

- **Overall Winner**: Best performing method
- **Performance Table**: Score, time, and efficiency metrics for each method
- **Visual Comparisons**:
  - Best score by method (bar chart)
  - Total optimization time (bar chart)
  - Time per trial (bar chart)
  - Convergence comparison (line chart showing all trials)
- **Best Parameters**: From each method
- **Export Options**: Download results as CSV or JSON

## Using the API (Python Code)

### Basic Example

```python
from src.backtesting import (
    HyperparameterTuner,
    ParameterSpace,
    BacktestEngine,
)
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources import get_default_data_source

# Load data
data_provider = get_default_data_source()
price_data = {
    symbol: data_provider.fetch_data(symbol, start_date='2015-01-01', end_date='2023-12-31')
    for symbol in ['SPY', 'EFA', 'EEM', 'AGG']
}

# Create backtest engine
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
)

# Define parameter space
param_space = [
    ParameterSpace(
        name='lookback_period',
        param_type='int',
        values=[126, 189, 252, 315]  # 6, 9, 12, 15 months
    ),
    ParameterSpace(
        name='position_count',
        param_type='int',
        values=[1, 2, 3]
    ),
    ParameterSpace(
        name='absolute_threshold',
        param_type='float',
        values=[0.0, 0.01, 0.02]
    ),
]

# Create tuner
tuner = HyperparameterTuner(
    strategy_class=DualMomentumStrategy,
    backtest_engine=engine,
    price_data=price_data,
    base_config={'safe_asset': 'AGG'},
    start_date='2020-01-01',
    end_date='2023-12-31',
)

# Compare all methods
comparison = tuner.compare_optimization_methods(
    param_space=param_space,
    methods=None,  # None = compare all methods
    n_trials=30,  # For random search and Bayesian optimization
    metric='sharpe_ratio',
    higher_is_better=True,
    random_state=42,
    verbose=True,
)

# View results
print(f"Best method: {comparison.best_method}")
print(f"Best score: {comparison.best_overall_score:.4f}")
print(f"Best parameters: {comparison.best_overall_params}")
print("\nComparison metrics:")
print(comparison.comparison_metrics)

# Access individual method results
for method, result in comparison.results.items():
    print(f"\n{method}:")
    print(f"  Best score: {result.best_score:.4f}")
    print(f"  Time: {result.optimization_time:.2f}s")
    print(f"  Trials: {result.n_trials}")
```

### Compare Specific Methods

```python
# Compare only Grid Search and Random Search
comparison = tuner.compare_optimization_methods(
    param_space=param_space,
    methods=['grid_search', 'random_search'],
    n_trials=50,
    metric='sharpe_ratio',
    higher_is_better=True,
    verbose=True,
)
```

### Save Comparison Results

```python
# Save all results to disk
saved_files = tuner.save_comparison_results(
    comparison=comparison,
    output_dir='./optimization_results',
    prefix='method_comparison'
)

print("Saved files:")
for file_type, file_path in saved_files.items():
    print(f"  {file_type}: {file_path}")
```

Files saved:
- `method_comparison_<timestamp>_comparison.csv` - Comparison metrics
- `method_comparison_<timestamp>_grid_search_results.csv` - Grid search trials
- `method_comparison_<timestamp>_random_search_results.csv` - Random search trials
- `method_comparison_<timestamp>_bayesian_optimization_results.csv` - Bayesian trials
- `method_comparison_<timestamp>_summary.json` - Summary with best method and parameters
- `method_comparison_<timestamp>_full_comparison.pkl` - Full MethodComparisonResult object

## Understanding Comparison Metrics

### Key Metrics

| Metric | Description |
|--------|-------------|
| `best_score` | Best metric value found by the method |
| `optimization_time` | Total time taken (seconds) |
| `n_trials` | Number of trials evaluated |
| `time_per_trial` | Average time per trial (seconds) |
| `is_best` | Whether this method found the overall best score |

### Interpreting Results

1. **Best Score**: Higher is better for metrics like Sharpe ratio, lower for metrics like max drawdown
2. **Optimization Time**: Consider the trade-off between time and solution quality
3. **Time per Trial**: Grid search is usually fastest per trial, Bayesian slowest but more efficient overall
4. **Convergence**: Look at convergence plots to see how quickly methods improve

## Best Practices

### When to Use Each Method

**Use Grid Search when:**
- Search space is small (< 100 combinations)
- You need guaranteed optimal solution
- Computation time is not a concern
- Parameters have discrete values

**Use Random Search when:**
- Search space is large
- You need quick results
- Parameters are continuous or have many discrete values
- Computation time is limited

**Use Bayesian Optimization when:**
- Evaluations are expensive (long backtests)
- Search space is moderate to large
- You want most sample-efficient method
- You can install Optuna dependency

### Optimization Tips

1. **Start Small**: Test with a small parameter space first
2. **Use Appropriate Trials**: 
   - Random Search: 50-200 trials typically sufficient
   - Bayesian: 30-100 trials often enough
3. **Set Random Seeds**: For reproducibility
4. **Monitor Progress**: Use `verbose=True` to track progress
5. **Compare Results**: Run comparison to validate method choice
6. **Consider Time Constraints**: Balance accuracy vs. computation time

## Advanced Usage

### Custom Metrics

You can optimize for any metric calculated by the backtesting engine:

```python
comparison = tuner.compare_optimization_methods(
    param_space=param_space,
    methods=['random_search', 'bayesian_optimization'],
    n_trials=50,
    metric='sortino_ratio',  # Or 'calmar_ratio', 'annual_return', etc.
    higher_is_better=True,
)
```

### Minimize Metrics

For metrics where lower is better (e.g., max drawdown):

```python
comparison = tuner.compare_optimization_methods(
    param_space=param_space,
    methods=['grid_search', 'random_search'],
    metric='max_drawdown',
    higher_is_better=False,  # Minimize drawdown
)
```

### Access Detailed Trial Data

```python
# Get all trials from a specific method
grid_results = comparison.results['grid_search']
all_trials = grid_results.all_results

# Analyze parameter importance
import pandas as pd
param_cols = [col for col in all_trials.columns if col.startswith('param_')]
correlations = all_trials[param_cols + ['score']].corr()['score']
print("Parameter correlations with score:")
print(correlations.sort_values(ascending=False))
```

## Troubleshooting

### Issue: Bayesian Optimization Not Available

**Solution**: Install Optuna
```bash
pip install optuna
```

### Issue: Comparison Takes Too Long

**Solutions**:
- Reduce parameter space size
- Decrease `n_trials` for random/Bayesian methods
- Use Random Search instead of Grid Search for large spaces
- Run comparison on a shorter date range first

### Issue: All Methods Find Different Parameters

**This is normal!** Different methods explore the search space differently. Consider:
- Are the scores similar? If yes, parameter sensitivity may be low
- Check convergence plots to see if methods stabilized
- Try increasing `n_trials` for random/Bayesian methods
- Validate results with out-of-sample testing

## API Reference

### MethodComparisonResult

```python
@dataclass
class MethodComparisonResult:
    results: Dict[str, OptimizationResult]  # Results from each method
    best_method: str                        # Name of best method
    best_overall_score: float               # Best score across all methods
    best_overall_params: Dict[str, Any]     # Parameters achieving best score
    comparison_metrics: pd.DataFrame        # Comparison table
    metric_name: str                        # Metric optimized
    higher_is_better: bool                  # Direction of optimization
    metadata: Dict[str, Any]                # Additional metadata
```

### HyperparameterTuner.compare_optimization_methods()

```python
def compare_optimization_methods(
    self,
    param_space: List[ParameterSpace],      # Parameters to optimize
    methods: Optional[List[str]] = None,    # Methods to compare (None = all)
    n_trials: int = 50,                     # Trials for random/Bayesian
    n_initial_points: int = 10,             # Initial random points for Bayesian
    metric: str = 'sharpe_ratio',           # Metric to optimize
    higher_is_better: bool = True,          # Maximize or minimize
    random_state: Optional[int] = None,     # Random seed
    verbose: bool = True,                   # Print progress
) -> MethodComparisonResult:
```

## Examples

See the `examples/` directory for complete examples:
- `examples/hyperparameter_tuning_demo.py` - Basic optimization
- `examples/optimization_method_comparison_demo.py` - Method comparison (new)

## Further Reading

- [Hyperparameter Tuning Guide](HYPERPARAMETER_TUNING_GUIDE.md)
- [Parameter Tuning Integration](PARAMETER_TUNING_INTEGRATION_GUIDE.md)
- [Quick Start Guide](QUICK_START_PARAMETER_TUNING.md)
- [Bayesian Optimization Paper](https://arxiv.org/abs/1807.02811)
- [Random Search Paper](http://www.jmlr.org/papers/volume13/bergstra12a/bergstra12a.pdf)
