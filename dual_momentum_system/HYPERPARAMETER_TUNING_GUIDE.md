# Hyperparameter Tuning Guide

## Overview

The hyperparameter tuning framework provides powerful tools for optimizing strategy parameters to maximize performance metrics. It supports three optimization methods:

1. **Grid Search** - Exhaustive search over all parameter combinations
2. **Random Search** - Random sampling from parameter distributions
3. **Bayesian Optimization** - Smart search using probabilistic models (requires Optuna)

## Key Features

✨ **Multiple Optimization Methods**
- Grid Search for exhaustive exploration
- Random Search for efficient sampling
- Bayesian Optimization for intelligent search

📊 **Comprehensive Results**
- Detailed trial history
- Performance metrics comparison
- Best parameter identification
- Visualization tools

🎯 **Flexible Parameter Spaces**
- Integer, float, and categorical parameters
- Discrete or continuous ranges
- Log-scale sampling support

💾 **Results Management**
- Save/load optimization results
- Export to CSV, JSON, or Pickle
- Reproducible experiments with random seeds

## Quick Start

### Command Line Usage

```python
from src.backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    ParameterSpace,
)
from src.strategies.dual_momentum import DualMomentumStrategy

# Create backtest engine
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage=0.0005,
)

# Create tuner
tuner = HyperparameterTuner(
    strategy_class=DualMomentumStrategy,
    backtest_engine=engine,
    price_data=price_data,  # Dict[str, PriceData]
    base_config={'safe_asset': 'AGG'},
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
)

# Define parameter space
param_space = [
    ParameterSpace(
        name='lookback_period',
        param_type='int',
        values=[126, 189, 252, 315]
    ),
    ParameterSpace(
        name='position_count',
        param_type='int',
        values=[1, 2, 3]
    ),
]

# Run optimization
results = tuner.grid_search(
    param_space=param_space,
    metric='sharpe_ratio',
    higher_is_better=True,
)

print(f"Best Parameters: {results.best_params}")
print(f"Best Score: {results.best_score:.4f}")
```

### Web Dashboard Usage

1. Navigate to **🎯 Hyperparameter Tuning** in the sidebar
2. Configure optimization settings in the **⚙️ Configuration** tab:
   - Set backtest period and capital
   - Choose optimization method and metric
   - Define parameter space
3. Run optimization in the **🚀 Run Optimization** tab
4. View and export results in the **📊 Results** tab

## Parameter Space Configuration

### Integer Parameters

```python
ParameterSpace(
    name='lookback_period',
    param_type='int',
    values=[126, 189, 252, 315]  # Discrete values
)

# Or with range
ParameterSpace(
    name='lookback_period',
    param_type='int',
    min_value=100,
    max_value=400,
    log_scale=False  # Use linear scale
)
```

### Float Parameters

```python
ParameterSpace(
    name='absolute_threshold',
    param_type='float',
    values=[0.0, 0.01, 0.02, 0.05]  # Discrete values
)

# Or with range
ParameterSpace(
    name='absolute_threshold',
    param_type='float',
    min_value=0.0,
    max_value=0.1,
    log_scale=False
)
```

### Categorical Parameters

```python
ParameterSpace(
    name='rebalance_frequency',
    param_type='categorical',
    values=['weekly', 'monthly', 'quarterly']
)

ParameterSpace(
    name='use_volatility_adjustment',
    param_type='categorical',
    values=[True, False]
)
```

## Optimization Methods

### Grid Search

Evaluates all possible parameter combinations. Best for:
- Small parameter spaces (< 100 combinations)
- Ensuring complete coverage
- Reproducible results

```python
results = tuner.grid_search(
    param_space=param_space,
    metric='sharpe_ratio',
    higher_is_better=True,
    n_jobs=1,  # Parallel jobs (future feature)
    verbose=True,
)
```

**Pros:**
- Guaranteed to find best combination in search space
- Simple and deterministic
- No hyperparameters to tune

**Cons:**
- Computational cost grows exponentially
- Not practical for large search spaces
- Doesn't learn from previous trials

### Random Search

Randomly samples parameter combinations. Best for:
- Medium-sized parameter spaces
- Quick exploration
- When some parameters may not matter

```python
results = tuner.random_search(
    param_space=param_space,
    n_trials=50,
    metric='sharpe_ratio',
    higher_is_better=True,
    random_state=42,  # For reproducibility
    verbose=True,
)
```

**Pros:**
- Efficient for high-dimensional spaces
- Can be stopped early
- Good exploration of search space
- Reproducible with random seed

**Cons:**
- May miss optimal configuration
- Doesn't learn from previous trials
- Results vary between runs

### Bayesian Optimization

Uses probabilistic models to intelligently search. Best for:
- Large parameter spaces
- Expensive evaluations (long backtests)
- Finding near-optimal solutions efficiently

```python
results = tuner.bayesian_optimization(
    param_space=param_space,
    n_trials=50,
    n_initial_points=10,  # Random warmup trials
    metric='sharpe_ratio',
    higher_is_better=True,
    random_state=42,
    verbose=True,
)
```

**Pros:**
- Most sample-efficient method
- Learns from previous trials
- Good for expensive evaluations
- Balances exploration and exploitation

**Cons:**
- Requires Optuna installation
- Slight overhead per trial
- Results may vary (though reproducible with seed)

## Optimization Metrics

Choose the metric that best represents your optimization goal:

### Risk-Adjusted Returns
- **`sharpe_ratio`** - Return per unit of total risk (most common)
- **`sortino_ratio`** - Return per unit of downside risk
- **`calmar_ratio`** - Return per unit of maximum drawdown

### Returns
- **`annual_return`** - Annualized return percentage
- **`total_return`** - Total return over period
- **`cagr`** - Compound annual growth rate

### Risk
- **`max_drawdown`** - Maximum peak-to-trough decline (minimize)
- **`volatility`** - Standard deviation of returns (minimize)

### Other
- **`win_rate`** - Percentage of winning periods
- **`alpha`** - Excess return vs benchmark
- **`information_ratio`** - Risk-adjusted active return

## Common Parameter Configurations

### Conservative (Low Risk)
```python
param_space = [
    ParameterSpace('lookback_period', 'int', values=[189, 252, 315]),  # 9-15 months
    ParameterSpace('position_count', 'int', values=[2, 3, 4]),  # Diversified
    ParameterSpace('absolute_threshold', 'float', values=[0.01, 0.02, 0.05]),  # Higher threshold
]
```

### Aggressive (High Return)
```python
param_space = [
    ParameterSpace('lookback_period', 'int', values=[63, 126, 189]),  # 3-9 months
    ParameterSpace('position_count', 'int', values=[1, 2]),  # Concentrated
    ParameterSpace('absolute_threshold', 'float', values=[0.0, 0.01]),  # Lower threshold
]
```

### Comprehensive Search
```python
param_space = [
    ParameterSpace('lookback_period', 'int', values=[63, 126, 189, 252, 315, 378]),
    ParameterSpace('position_count', 'int', values=[1, 2, 3, 4]),
    ParameterSpace('absolute_threshold', 'float', values=[-0.05, 0.0, 0.01, 0.02, 0.05]),
    ParameterSpace('use_volatility_adjustment', 'categorical', values=[True, False]),
]
```

## Results Analysis

### Accessing Results

```python
# Best configuration
print(results.best_params)
print(results.best_score)

# All trials
results_df = results.all_results
print(results_df.head())

# Best backtest details
best_bt = results.best_backtest
print(best_bt.metrics)
print(best_bt.equity_curve)

# Optimization metadata
print(f"Method: {results.method}")
print(f"Time: {results.optimization_time:.2f}s")
print(f"Trials: {results.n_trials}")
```

### Saving Results

```python
from pathlib import Path

# Save all formats
saved_files = tuner.save_results(
    results,
    output_dir=Path("optimization_results"),
    prefix="my_optimization"
)

# Returns:
# {
#     'csv': Path('optimization_results/my_optimization_grid_search_20240123_143022_results.csv'),
#     'json': Path('optimization_results/my_optimization_grid_search_20240123_143022_best_params.json'),
#     'pickle': Path('optimization_results/my_optimization_grid_search_20240123_143022_full_results.pkl')
# }
```

### Loading Results

```python
import pickle

# Load full results
with open('optimization_results/my_optimization_full_results.pkl', 'rb') as f:
    results = pickle.load(f)

# Load just parameters
import json
with open('optimization_results/my_optimization_best_params.json', 'r') as f:
    params = json.load(f)
```

## Best Practices

### 1. Start Small, Scale Up

```python
# First: Quick grid search with 2-3 values per parameter
quick_space = [
    ParameterSpace('lookback_period', 'int', values=[126, 252]),
    ParameterSpace('position_count', 'int', values=[1, 2]),
]

# Then: Refine with more values or random/Bayesian search
refined_space = [
    ParameterSpace('lookback_period', 'int', values=[126, 189, 252, 315]),
    ParameterSpace('position_count', 'int', values=[1, 2, 3]),
]
```

### 2. Use Appropriate Data Periods

- **Training Period**: Use for optimization (e.g., 2018-2021)
- **Validation Period**: Hold out for testing (e.g., 2022-2023)
- **Buffer Period**: Add lookback buffer before training start

```python
# Example: 3-year training + 400-day buffer
training_start = datetime(2018, 1, 1)
training_end = datetime(2021, 12, 31)
data_start = training_start - timedelta(days=400)

# Later: Test on validation period
validation_start = datetime(2022, 1, 1)
validation_end = datetime(2023, 12, 31)
```

### 3. Consider Transaction Costs

Ensure realistic commission and slippage:

```python
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,  # 0.1% - typical for brokers
    slippage=0.0005,   # 0.05% - market impact
)
```

### 4. Use Multiple Metrics

Don't optimize for a single metric:

```python
# Optimize for Sharpe ratio
results = tuner.grid_search(param_space, metric='sharpe_ratio')

# But also check drawdown, volatility, etc.
best_bt = results.best_backtest
print(f"Sharpe: {best_bt.metrics['sharpe_ratio']:.2f}")
print(f"Max DD: {best_bt.metrics['max_drawdown']*100:.1f}%")
print(f"Volatility: {best_bt.metrics['volatility']*100:.1f}%")
```

### 5. Avoid Overfitting

- Use walk-forward validation
- Test on out-of-sample data
- Keep parameter spaces reasonable
- Consider parameter stability

### 6. Document Your Process

```python
# Save configuration with results
metadata = {
    'universe': ['SPY', 'EFA', 'EEM', 'AGG'],
    'period': '2018-2021',
    'commission': 0.001,
    'slippage': 0.0005,
    'notes': 'Initial optimization for conservative portfolio',
}

results.metadata.update(metadata)
```

## Troubleshooting

### Optimization Takes Too Long

1. **Reduce parameter space**:
   - Use fewer values per parameter
   - Fix some parameters to reasonable defaults
   - Focus on most impactful parameters

2. **Use faster methods**:
   - Switch from Grid to Random Search
   - Reduce number of trials
   - Use smaller data period for initial exploration

3. **Profile performance**:
   ```python
   import time
   
   start = time.time()
   results = tuner.grid_search(param_space, metric='sharpe_ratio')
   elapsed = time.time() - start
   
   print(f"Time per trial: {elapsed / results.n_trials:.2f}s")
   ```

### All Trials Fail

1. **Check data quality**:
   - Ensure sufficient history (lookback + buffer)
   - Verify all symbols have data
   - Check for gaps or missing values

2. **Validate parameter ranges**:
   - Test individual configurations manually
   - Ensure parameters are reasonable
   - Check for conflicts (e.g., position_count > universe size)

3. **Review error messages**:
   ```python
   # Examine failed trials
   failed = results.all_results[results.all_results['score'].isna()]
   if 'error' in failed.columns:
       print(failed['error'].unique())
   ```

### Results Not Improving

1. **Check if metric is appropriate**:
   - Different metrics favor different characteristics
   - Ensure direction is correct (maximize vs minimize)

2. **Expand search space**:
   - Current range may not include optimal values
   - Try different parameter ranges

3. **Verify data quality**:
   - Poor quality data leads to noise
   - Check for outliers or data errors

## Advanced Topics

### Walk-Forward Optimization

```python
# Define multiple periods
periods = [
    (datetime(2018, 1, 1), datetime(2020, 12, 31)),  # Train
    (datetime(2021, 1, 1), datetime(2021, 12, 31)),  # Validate
    (datetime(2022, 1, 1), datetime(2022, 12, 31)),  # Test
]

for train_period in periods:
    tuner = HyperparameterTuner(
        strategy_class=DualMomentumStrategy,
        backtest_engine=engine,
        price_data=price_data,
        start_date=train_period[0],
        end_date=train_period[1],
    )
    
    results = tuner.grid_search(param_space, metric='sharpe_ratio')
    # Use results.best_params for next period
```

### Custom Metrics

```python
def custom_metric(backtest_result):
    """Custom metric combining multiple objectives."""
    metrics = backtest_result.metrics
    
    # Example: Weighted combination
    sharpe = metrics.get('sharpe_ratio', 0)
    max_dd = abs(metrics.get('max_drawdown', 1))
    
    # Penalize high drawdowns
    return sharpe * (1 - max_dd)

# Note: Currently not directly supported, but can be added
# as a post-processing step
```

### Parallel Execution

```python
# Future feature - parallel execution
results = tuner.grid_search(
    param_space=param_space,
    metric='sharpe_ratio',
    n_jobs=4,  # Use 4 CPU cores
)
```

## Examples

See the following example scripts for complete demonstrations:

- `examples/hyperparameter_tuning_demo.py` - Comprehensive examples
- `tests/test_hyperparameter_tuner.py` - Unit tests and edge cases

## API Reference

### HyperparameterTuner

```python
HyperparameterTuner(
    strategy_class: type,
    backtest_engine: BacktestEngine,
    price_data: Dict[str, PriceData],
    base_config: Optional[Dict[str, Any]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    benchmark_data: Optional[PriceData] = None,
    risk_manager: Optional[Any] = None,
)
```

### ParameterSpace

```python
ParameterSpace(
    name: str,
    param_type: str,  # 'int', 'float', 'categorical'
    values: Optional[List[Any]] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    log_scale: bool = False,
)
```

### OptimizationResult

```python
@dataclass
class OptimizationResult:
    best_params: Dict[str, Any]
    best_score: float
    best_backtest: BacktestResult
    all_results: pd.DataFrame
    optimization_time: float
    n_trials: int
    metric_name: str
    method: str
    metadata: Dict[str, Any]
```

## Support

For issues, questions, or feature requests:
- Check the examples in `examples/hyperparameter_tuning_demo.py`
- Review the tests in `tests/test_hyperparameter_tuner.py`
- See the main README for general documentation

## License

Part of the Dual Momentum Backtesting Framework.
