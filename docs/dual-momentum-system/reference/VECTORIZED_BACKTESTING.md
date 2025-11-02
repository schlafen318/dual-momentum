# Vectorized Multi-Asset Backtesting Engine

A high-performance vectorized backtesting framework using `vectorbt` for efficient multi-asset portfolio backtesting with comprehensive analytics.

## Features

### 🚀 Core Backtesting Engine

- **Vectorized Operations**: Leverages vectorbt for maximum performance
- **Multi-Asset Support**: Efficient handling of portfolios with multiple assets
- **Flexible Signal Types**: Support for position sizes, entry/exit signals, and custom strategies
- **Transaction Costs**: Commission and slippage modeling
- **Portfolio Features**: Cash sharing, position sizing, and execution ordering

### 📊 Standard Performance Metrics

Comprehensive calculation of all standard metrics:

- **Return Metrics**: CAGR, total return, cumulative return
- **Risk Metrics**: Annual volatility, downside volatility, max drawdown
- **Risk-Adjusted**: Sharpe ratio, Sortino ratio, Calmar ratio, Omega ratio
- **Trade Metrics**: Win rate, profit factor, average win/loss, expectancy
- **Timing Metrics**: Best/worst periods, recovery time
- **Risk Measures**: Value at Risk (VaR), Conditional VaR (CVaR)

### 🔬 Advanced Analytics

#### Rolling Statistics
- Rolling returns, volatility, Sharpe ratio
- Rolling max drawdown and win rate
- Rolling skewness and kurtosis

#### Monte Carlo Simulation
- Bootstrap resampling from historical returns
- Parametric simulation (normal and t-distribution)
- Confidence intervals and percentile analysis
- Risk metrics (VaR, CVaR) from simulations

#### Regime Analysis
- Multiple detection methods:
  - Volatility-based regimes
  - Trend-based regimes
  - Hidden Markov Models (HMM)
  - Percentile-based regimes
- Performance analysis by regime
- Regime transition analysis

#### Additional Analytics
- Detailed drawdown analysis
- Stress testing with crisis scenarios
- Performance attribution vs benchmark
- Rolling correlation analysis

## Installation

Ensure you have the required dependencies:

```bash
pip install vectorbt>=0.26.0
pip install empyrical>=0.5.5
pip install scipy>=1.10.0
pip install hmmlearn  # Optional, for HMM regime detection
```

## Quick Start

### Basic Momentum Strategy

```python
from src.backtesting import VectorizedBacktestEngine, SignalGenerator
import pandas as pd

# Load your price data
prices = pd.DataFrame({
    'AAPL': [...],
    'MSFT': [...],
    'GOOGL': [...]
})

# Create engine
engine = VectorizedBacktestEngine(
    initial_capital=100000,
    commission=0.001,  # 0.1%
    slippage=0.0005,   # 0.05%
    freq='D'
)

# Generate momentum signals
signals = SignalGenerator.momentum_signals(
    prices,
    lookback=252,  # 1 year
    top_n=2,       # Top 2 assets
    normalize=True # Normalize weights to sum to 1
)

# Run backtest
results = engine.run_backtest(
    price_data=prices,
    signals=signals,
    size_type='percent'
)

# View results
print(f"Total Return: {results.total_return:.2%}")
print(f"CAGR: {results.metrics['cagr']:.2%}")
print(f"Sharpe Ratio: {results.metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results.metrics['max_drawdown']:.2%}")
```

### Signal-Based Strategy (Entry/Exit)

```python
# Generate SMA crossover signals
entries, exits = SignalGenerator.sma_crossover_signals(
    prices,
    fast_window=50,
    slow_window=200
)

# Run backtest
results = engine.run_signal_strategy(
    price_data=prices,
    entries=entries,
    exits=exits,
    size=0.5,  # 50% of capital per signal
    direction='longonly'
)
```

### Custom Strategy Function

```python
def custom_strategy(prices, **kwargs):
    """Your custom signal generation logic."""
    # Calculate your indicators
    momentum = prices.pct_change(kwargs['lookback'])
    volatility = prices.pct_change().rolling(20).std()
    
    # Create signals based on momentum/volatility
    signals = (momentum > 0) & (volatility < volatility.median())
    
    # Convert to position sizes
    return signals.astype(float) * 0.5

# Run with custom strategy
results = engine.run_custom_strategy(
    price_data=prices,
    signal_func=custom_strategy,
    signal_func_kwargs={'lookback': 126}
)
```

## Advanced Analytics

### Rolling Metrics Analysis

```python
from src.backtesting import AdvancedAnalytics

analytics = AdvancedAnalytics(freq='D')

# Calculate rolling metrics
rolling_stats = analytics.calculate_rolling_metrics(
    returns=results.returns,
    window=252,  # 1-year rolling window
    metrics=['return', 'volatility', 'sharpe', 'sortino', 'max_drawdown']
)

# Plot rolling Sharpe ratio
import matplotlib.pyplot as plt
rolling_stats['rolling_sharpe'].plot(title='Rolling 1-Year Sharpe Ratio')
plt.show()
```

### Monte Carlo Simulation

```python
# Run Monte Carlo simulation
mc_results = analytics.monte_carlo_simulation(
    returns=results.returns,
    num_simulations=1000,
    num_periods=252,  # 1 year forward
    method='bootstrap',  # or 'parametric', 'parametric_t'
    confidence_levels=[0.05, 0.25, 0.50, 0.75, 0.95]
)

# View statistics
stats = mc_results['statistics']
print(f"Expected Return: {stats['expected_return']:.2%}")
print(f"Probability of Profit: {stats['probability_positive']:.2%}")
print(f"VaR (95%): {stats['var_95']:.2%}")
print(f"CVaR (95%): {stats['cvar_95']:.2%}")

# Access simulation paths
paths_df = mc_results['paths']  # All simulation paths
percentiles_df = mc_results['percentiles']  # Percentile paths
```

### Regime Detection and Analysis

```python
# Detect market regimes
regimes = analytics.detect_regimes(
    returns=results.returns,
    method='volatility',  # or 'trend', 'hmm', 'percentile'
    n_regimes=2  # 2 for bull/bear, 3 for bull/neutral/bear
)

# Analyze performance by regime
regime_analysis = analytics.analyze_regimes(
    returns=results.returns,
    regimes=regimes
)

print(regime_analysis)
# Shows mean return, volatility, Sharpe, win rate for each regime
```

### Drawdown Analysis

```python
# Detailed analysis of top drawdowns
dd_analysis = analytics.calculate_drawdown_analysis(
    equity_curve=results.equity_curve,
    top_n=5
)

print(dd_analysis)
# Shows depth, start/trough/recovery dates, duration for each drawdown
```

### Stress Testing

```python
# Perform stress tests
stress_results = analytics.calculate_stress_tests(
    returns=results.returns,
    scenarios={
        '2008_crisis': {'shock': -0.50, 'duration': 252},
        'flash_crash': {'shock': -0.10, 'duration': 1},
        'moderate_correction': {'shock': -0.20, 'duration': 60}
    }
)

print(stress_results)
```

### Performance Attribution

```python
# Compare vs benchmark
attribution = analytics.calculate_performance_attribution(
    returns=results.returns,
    benchmark_returns=benchmark_returns
)

print(f"Alpha: {attribution['alpha']:.2%}")
print(f"Beta: {attribution['beta']:.2f}")
print(f"Information Ratio: {attribution['information_ratio']:.2f}")
print(f"Tracking Error: {attribution['tracking_error']:.2%}")
```

## Strategy Comparison

```python
# Define multiple strategies
strategies = {
    'Momentum_12M_Top3': SignalGenerator.momentum_signals(
        prices, lookback=252, top_n=3
    ),
    'Momentum_6M_Top5': SignalGenerator.momentum_signals(
        prices, lookback=126, top_n=5
    ),
    'Equal_Weight_Monthly': SignalGenerator.equal_weight_signals(
        prices, rebalance_freq='M'
    ),
    'Equal_Weight_Quarterly': SignalGenerator.equal_weight_signals(
        prices, rebalance_freq='Q'
    )
}

# Compare all strategies
comparison = engine.run_multi_strategy_comparison(
    price_data=prices,
    strategies=strategies
)

# Create comparison table
comparison_df = pd.DataFrame({
    name: {
        'Return': result.total_return,
        'CAGR': result.metrics['cagr'],
        'Sharpe': result.metrics['sharpe_ratio'],
        'Max DD': result.metrics['max_drawdown'],
        'Calmar': result.metrics['calmar_ratio']
    }
    for name, result in comparison.items()
}).T

print(comparison_df)
```

## Parameter Optimization

```python
# Define parameter grid
param_grid = {
    'lookback': [63, 126, 252],  # 3, 6, 12 months
    'top_n': [2, 3, 5]
}

# Optimize on Sharpe ratio
best_params, best_result = engine.optimize_strategy(
    price_data=prices,
    signal_func=lambda p, **kw: SignalGenerator.momentum_signals(p, **kw),
    param_grid=param_grid,
    metric='sharpe_ratio',
    maximize=True
)

print(f"Best Parameters: {best_params}")
print(f"Best Sharpe: {best_result.metrics['sharpe_ratio']:.2f}")
```

## Built-in Signal Generators

### Momentum Signals
```python
signals = SignalGenerator.momentum_signals(
    prices,
    lookback=252,
    top_n=3,
    normalize=True
)
```

### SMA Crossover
```python
entries, exits = SignalGenerator.sma_crossover_signals(
    prices,
    fast_window=50,
    slow_window=200
)
```

### Mean Reversion
```python
entries, exits = SignalGenerator.mean_reversion_signals(
    prices,
    window=20,
    entry_std=2.0,
    exit_std=0.5
)
```

### Equal Weight Rebalancing
```python
signals = SignalGenerator.equal_weight_signals(
    prices,
    rebalance_freq='M'  # 'D', 'W', 'M', 'Q', 'Y'
)
```

## Performance Considerations

### Vectorization Benefits
- **Speed**: 10-100x faster than iterative backtesting for multi-asset portfolios
- **Memory Efficiency**: Efficient handling of large datasets
- **Scalability**: Easily scale to hundreds of assets

### Best Practices
1. **Use vectorized operations**: Avoid loops in signal generation
2. **Pre-compute indicators**: Calculate all indicators before backtesting
3. **Batch processing**: Use multi-strategy comparison for efficiency
4. **Memory management**: For very large datasets, consider chunking

## API Reference

### VectorizedBacktestEngine

#### Constructor
```python
VectorizedBacktestEngine(
    initial_capital: float = 100000.0,
    commission: float = 0.001,
    slippage: float = 0.0005,
    freq: str = 'D',
    risk_free_rate: float = 0.0,
    **kwargs
)
```

#### Methods
- `run_backtest()`: Run backtest with position size signals
- `run_signal_strategy()`: Run backtest with entry/exit signals
- `run_custom_strategy()`: Run backtest with custom signal function
- `run_multi_strategy_comparison()`: Compare multiple strategies
- `optimize_strategy()`: Parameter optimization via grid search

### VectorizedMetricsCalculator

#### Constructor
```python
VectorizedMetricsCalculator(
    freq: str = 'D',
    periods_per_year: Optional[int] = None
)
```

#### Methods
- `calculate_all_metrics()`: Calculate comprehensive metrics
- `calculate_return_metrics()`: Return-based metrics
- `calculate_risk_metrics()`: Risk metrics
- `calculate_risk_adjusted_metrics()`: Sharpe, Sortino, etc.
- `calculate_trade_metrics()`: Trade statistics
- Individual metric calculators: `calculate_sharpe_ratio()`, `calculate_cagr()`, etc.

### AdvancedAnalytics

#### Constructor
```python
AdvancedAnalytics(freq: str = 'D')
```

#### Methods
- `calculate_rolling_metrics()`: Rolling performance statistics
- `monte_carlo_simulation()`: Monte Carlo simulation
- `detect_regimes()`: Regime detection
- `analyze_regimes()`: Performance analysis by regime
- `calculate_drawdown_analysis()`: Detailed drawdown analysis
- `calculate_stress_tests()`: Stress testing
- `calculate_performance_attribution()`: Attribution vs benchmark
- `calculate_rolling_correlation()`: Rolling correlation

## Examples

See the comprehensive demo:
```bash
python examples/vectorized_backtest_demo.py
```

This runs 8 different demos showing all features:
1. Basic vectorized backtest
2. Signal-based strategy
3. Multi-strategy comparison
4. Rolling metrics analysis
5. Monte Carlo simulation
6. Regime analysis
7. Drawdown analysis
8. Stress testing

## Testing

Run the test suite:
```bash
pytest tests/test_vectorized_engine.py -v
```

## Integration with Existing System

The vectorized engine integrates seamlessly with the existing dual momentum framework:

```python
from src.strategies import DualMomentumStrategy
from src.backtesting import VectorizedBacktestEngine
from src.data_sources import YahooFinanceDataSource

# Load data
data_source = YahooFinanceDataSource()
price_data = data_source.get_historical_data(['SPY', 'EFA', 'AGG'])

# Create strategy
strategy = DualMomentumStrategy(config={
    'lookback_period': 252,
    'universe': ['SPY', 'EFA', 'AGG']
})

# Convert strategy signals to vectorized format
def strategy_to_signals(prices, strategy):
    signals = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    
    # Generate signals for each date (simplified)
    for date in prices.index:
        current_data = {sym: PriceData(...) for sym in prices.columns}
        sigs = strategy.generate_signals(current_data)
        
        for sig in sigs:
            signals.loc[date, sig.symbol] = sig.strength
    
    return signals

signals = strategy_to_signals(price_data, strategy)

# Run vectorized backtest
engine = VectorizedBacktestEngine(initial_capital=100000)
results = engine.run_backtest(price_data, signals)
```

## Contributing

When adding new features:
1. Ensure vectorized operations (no loops over dates)
2. Add comprehensive unit tests
3. Update documentation
4. Include usage examples

## License

Part of the Dual Momentum System. See main README for license information.
