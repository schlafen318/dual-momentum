# Vectorized Backtesting - Quick Start Guide

Get started with the vectorized backtesting engine in 5 minutes.

## Installation

Ensure dependencies are installed:
```bash
pip install vectorbt>=0.26.0 pandas numpy scipy loguru
```

## Basic Example (30 seconds)

```python
from src.backtesting import VectorizedBacktestEngine, SignalGenerator
import pandas as pd

# Your price data (DataFrame with symbols as columns)
prices = pd.DataFrame({
    'AAPL': [100, 102, 105, 103, 108, ...],
    'MSFT': [200, 205, 203, 210, 215, ...],
    'GOOGL': [150, 148, 152, 155, 158, ...]
}, index=pd.date_range('2020-01-01', periods=1000, freq='D'))

# Create engine
engine = VectorizedBacktestEngine(
    initial_capital=100000,
    commission=0.001  # 0.1%
)

# Generate momentum signals (top 2 assets)
signals = SignalGenerator.momentum_signals(
    prices, 
    lookback=252,  # 1 year
    top_n=2
)

# Run backtest
results = engine.run_backtest(prices, signals)

# View results
print(f"Return: {results.total_return:.2%}")
print(f"Sharpe: {results.metrics['sharpe_ratio']:.2f}")
print(f"Max DD: {results.metrics['max_drawdown']:.2%}")
```

## Common Use Cases

### 1. Compare Multiple Strategies

```python
strategies = {
    'Momentum_12M': SignalGenerator.momentum_signals(prices, 252, top_n=2),
    'Momentum_6M': SignalGenerator.momentum_signals(prices, 126, top_n=3),
    'Equal_Weight': SignalGenerator.equal_weight_signals(prices, 'M')
}

results = engine.run_multi_strategy_comparison(prices, strategies)

for name, result in results.items():
    print(f"{name}: {result.metrics['sharpe_ratio']:.2f}")
```

### 2. Monte Carlo Simulation

```python
from src.backtesting import AdvancedAnalytics

analytics = AdvancedAnalytics(freq='D')

mc_results = analytics.monte_carlo_simulation(
    returns=results.returns,
    num_simulations=1000
)

print(f"Prob of profit: {mc_results['statistics']['probability_positive']:.0%}")
print(f"Expected return: {mc_results['statistics']['expected_return']:.2%}")
```

### 3. Rolling Performance

```python
rolling = analytics.calculate_rolling_metrics(
    results.returns,
    window=252,
    metrics=['return', 'sharpe', 'max_drawdown']
)

# Plot rolling Sharpe
rolling['rolling_sharpe'].plot(title='1-Year Rolling Sharpe')
```

### 4. Regime Analysis

```python
regimes = analytics.detect_regimes(
    results.returns,
    method='volatility',
    n_regimes=2
)

regime_stats = analytics.analyze_regimes(results.returns, regimes)
print(regime_stats)
```

## Built-in Signal Generators

### Momentum
```python
signals = SignalGenerator.momentum_signals(
    prices, lookback=252, top_n=3, normalize=True
)
```

### SMA Crossover
```python
entries, exits = SignalGenerator.sma_crossover_signals(
    prices, fast_window=50, slow_window=200
)
results = engine.run_signal_strategy(prices, entries, exits)
```

### Mean Reversion
```python
entries, exits = SignalGenerator.mean_reversion_signals(
    prices, window=20, entry_std=2.0
)
```

### Equal Weight
```python
signals = SignalGenerator.equal_weight_signals(
    prices, rebalance_freq='M'  # Monthly rebalancing
)
```

## Custom Strategy

```python
def my_strategy(prices, **params):
    """Your custom logic here."""
    # Calculate indicators
    momentum = prices.pct_change(params['lookback'])
    volatility = prices.pct_change().rolling(20).std()
    
    # Generate signals
    signals = (momentum > 0) & (volatility < volatility.median())
    return signals.astype(float) * 0.5

results = engine.run_custom_strategy(
    price_data=prices,
    signal_func=my_strategy,
    signal_func_kwargs={'lookback': 126}
)
```

## All Metrics Available

```python
results.metrics = {
    # Returns
    'total_return', 'cagr', 'annual_return',
    
    # Risk
    'annual_volatility', 'max_drawdown', 'avg_drawdown',
    'var_95', 'var_99', 'cvar_95', 'cvar_99',
    
    # Risk-Adjusted
    'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'omega_ratio',
    
    # Trade Stats
    'win_rate', 'profit_factor', 'avg_win', 'avg_loss',
    'num_trades', 'expectancy',
    
    # Timing
    'best_day', 'worst_day', 'best_month', 'worst_month',
    'max_drawdown_duration'
}
```

## Advanced Features

### Stress Testing
```python
stress = analytics.calculate_stress_tests(results.returns)
```

### Drawdown Analysis
```python
drawdowns = analytics.calculate_drawdown_analysis(
    results.equity_curve, top_n=5
)
```

### Performance Attribution
```python
attribution = analytics.calculate_performance_attribution(
    returns=results.returns,
    benchmark_returns=spy_returns
)
print(f"Alpha: {attribution['alpha']:.2%}")
print(f"Beta: {attribution['beta']:.2f}")
```

## Performance Tips

1. **Pre-compute indicators**: Calculate all indicators before backtesting
2. **Vectorize signals**: Avoid loops in signal generation
3. **Batch strategies**: Use `run_multi_strategy_comparison()` for efficiency
4. **Cache results**: Save results for later analysis

## Examples

See `examples/vectorized_backtest_demo.py` for 8 comprehensive examples covering:
1. Basic momentum backtest
2. Signal-based strategies
3. Strategy comparison
4. Rolling metrics
5. Monte Carlo simulation
6. Regime analysis
7. Drawdown analysis
8. Stress testing

## Documentation

- **Full Guide**: See `VECTORIZED_BACKTESTING.md`
- **API Reference**: All classes and methods documented
- **Implementation**: See `IMPLEMENTATION_SUMMARY.md`

## Need Help?

- Check examples in `examples/vectorized_backtest_demo.py`
- Read full documentation in `VECTORIZED_BACKTESTING.md`
- Review test cases in `tests/test_vectorized_engine.py`

---

**Ready to go!** Start with the basic example above and explore the advanced features as needed.
