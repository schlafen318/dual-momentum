# Optimization Method Comparison in Backtesting

## Overview

This feature allows you to compare different portfolio optimization methods directly within your backtesting framework. Instead of using a single position sizing approach, you can now run multiple backtests with different optimization methods and see which works best for your strategy.

## What It Does

The optimization method comparison feature:

1. **Runs multiple backtests** - Same strategy, same data, but different position sizing methods
2. **Compares performance** - Shows which optimization method produces the best risk-adjusted returns
3. **Visualizes results** - Side-by-side comparison of equity curves, returns, risk metrics, and drawdowns
4. **Helps decision-making** - Identifies the optimal position sizing approach for your strategy

## Available Optimization Methods

### 1. **Momentum-Based (Baseline)**
- **What it does**: Uses signal strength from momentum calculations to weight positions
- **Best for**: Strategies where momentum strength is a good predictor
- **Pros**: Natural fit for momentum strategies, no additional calculations needed
- **Cons**: May not account for risk differences between assets

### 2. **Equal Weight**
- **What it does**: Allocates equal capital to each selected asset (1/N)
- **Best for**: Simple, robust allocation when you have no strong priors
- **Pros**: Simple, well-diversified, often surprisingly effective
- **Cons**: Ignores risk characteristics and expected returns

### 3. **Inverse Volatility**
- **What it does**: Assets with lower volatility get higher allocation
- **Best for**: Risk-conscious investors who want to reduce portfolio volatility
- **Pros**: Automatically reduces exposure to volatile assets
- **Cons**: May underweight high-return assets

### 4. **Minimum Variance**
- **What it does**: Finds the portfolio with the lowest possible volatility
- **Best for**: Very risk-averse investors prioritizing stability
- **Pros**: Minimizes portfolio risk
- **Cons**: Ignores returns, may have concentration risk

### 5. **Maximum Sharpe**
- **What it does**: Optimizes for the best risk-adjusted return
- **Best for**: Investors seeking optimal risk/reward balance
- **Pros**: Theoretically optimal portfolio
- **Cons**: Sensitive to estimation errors, can be unstable

### 6. **Risk Parity**
- **What it does**: Equalizes risk contribution from each asset
- **Best for**: Balanced portfolios where each asset contributes equally to risk
- **Pros**: Well-diversified from a risk perspective
- **Cons**: Computationally intensive, sensitive to correlation estimates

### 7. **Maximum Diversification**
- **What it does**: Maximizes the diversification ratio
- **Best for**: Maximizing the benefit of diversification
- **Pros**: Explicitly targets diversification
- **Cons**: May underweight correlated assets even if they have good returns

### 8. **Hierarchical Risk Parity (HRP)**
- **What it does**: Uses machine learning clustering to build portfolios
- **Best for**: Complex portfolios with many assets
- **Pros**: Robust to estimation errors, uses modern techniques
- **Cons**: More complex, harder to interpret

## Usage

### From the Streamlit Dashboard

1. **Run a backtest** from the Strategy Builder page
2. **Go to Backtest Results** and click on the **"🔄 Method Comparison"** tab
3. **Select methods** you want to compare (at least 2)
4. **Set optimization lookback** (default: 60 days)
5. **Click "Run Comparison"**
6. **View results** with interactive charts and metrics

### Programmatic Usage

```python
from src.backtesting import compare_optimization_methods_in_backtest
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources import get_default_data_source

# Create strategy
strategy = DualMomentumStrategy({
    'lookback_period': 252,
    'position_count': 3,
    'safe_asset': 'AGG',
})

# Load data
data_provider = get_default_data_source()
price_data = {
    symbol: data_provider.fetch_data(symbol, start_date, end_date)
    for symbol in ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD']
}

# Run comparison
comparison = compare_optimization_methods_in_backtest(
    strategy=strategy,
    price_data=price_data,
    optimization_methods=[
        'momentum_based',
        'equal_weight',
        'risk_parity',
        'maximum_sharpe',
    ],
    initial_capital=100000,
    start_date=datetime(2018, 1, 1),
    end_date=datetime(2023, 12, 31),
    optimization_lookback=60,
    verbose=True,
)

# View results
print(comparison.comparison_metrics)
print(f"Best Sharpe: {comparison.best_sharpe_method}")
print(f"Best Return: {comparison.best_return_method}")
```

## Key Features

### Performance Metrics Compared

- **Total Return**: Overall percentage gain/loss
- **Annualized Return**: Compound annual growth rate
- **Sharpe Ratio**: Risk-adjusted return measure
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Calmar Ratio**: Return vs. max drawdown
- **Win Rate**: Percentage of profitable trades
- **Volatility**: Annualized standard deviation of returns

### Visualizations

1. **Equity Curves**: Compare portfolio values over time
2. **Return Comparison**: Bar charts of total and annualized returns
3. **Risk Metrics**: Sharpe, Sortino ratios and volatility
4. **Drawdown Analysis**: Compare drawdown periods across methods

### Export Options

- **CSV**: Comparison metrics and individual results
- **JSON**: Summary and detailed results
- **Charts**: Interactive Plotly visualizations

## Best Practices

### 1. Start with Baseline
Always include `'momentum_based'` as your baseline to see if alternative methods actually improve performance.

### 2. Use Sufficient Data
The optimization lookback period should be:
- **Minimum**: 20 days
- **Recommended**: 60 days
- **Maximum**: 252 days (1 year)

### 3. Consider Estimation Error
Methods like `maximum_sharpe` and `minimum_variance` are sensitive to estimation errors. Use longer lookback periods or consider simpler methods like `equal_weight` or `risk_parity`.

### 4. Match Method to Strategy
- **High turnover strategies**: Use `equal_weight` or `risk_parity` to reduce complexity
- **Low turnover strategies**: Can use more sophisticated methods like `maximum_sharpe`
- **Risk-focused strategies**: Use `risk_parity` or `minimum_variance`

### 5. Validate Results
- Check if results are stable across different time periods
- Ensure the "winner" has a meaningful advantage (>0.5 Sharpe improvement)
- Consider transaction costs - more complex methods may not justify additional trading

## Example Results Interpretation

```
Method                   | Total Return | Sharpe | Max DD  | Volatility
-------------------------|--------------|--------|---------|------------
Momentum Based (Baseline)|   45.2%     |  1.15  | -18.3%  |   12.1%
Equal Weight             |   52.8%     |  1.28  | -15.2%  |   11.8%
Risk Parity              |   48.3%     |  1.35  | -12.7%  |   10.2%
Maximum Sharpe           |   56.1%     |  1.42  | -14.1%  |   11.3%
```

**Interpretation**:
- **Maximum Sharpe** achieved the best risk-adjusted returns (1.42 Sharpe)
- **Risk Parity** had the lowest drawdown (-12.7%)
- **Equal Weight** provided solid improvement over baseline with simplicity
- All methods outperformed the baseline, suggesting optimization adds value

## Technical Details

### How It Works

1. **Momentum Filter**: Strategy generates signals based on momentum criteria
2. **Asset Selection**: Top N assets pass the filter
3. **Optimization**: For each method, calculate optimal weights for selected assets
4. **Execution**: Execute trades based on optimized weights
5. **Rebalancing**: Repeat at each rebalancing period

### Architecture

```
Strategy (generates signals)
    ↓
Momentum Filter (selects assets)
    ↓
Portfolio Optimizer (sizes positions)
    ↓
Backtest Engine (executes trades)
    ↓
Performance Metrics (evaluates results)
```

### Key Classes

- `OptimizationBacktestEngine`: Extended backtest engine with optimization support
- `OptimizationMethodComparisonResult`: Stores comparison results
- `compare_optimization_methods_in_backtest()`: Main comparison function

## Troubleshooting

### "Insufficient data for optimization"
- **Solution**: Increase the data buffer before your backtest start date
- **Calculation**: Add `optimization_lookback + strategy_lookback` days

### "Optimization failed"
- **Solution**: Some methods require at least 2-3 assets. Check your momentum filter isn't too strict
- **Fallback**: System automatically falls back to equal weights on failure

### "All methods give similar results"
- **Interpretation**: The momentum filter is dominant; position sizing matters less
- **Consider**: Loosen the momentum filter to include more assets

### "Results are unstable"
- **Solution**: Increase `optimization_lookback` period
- **Alternative**: Use simpler methods like `equal_weight` or `inverse_volatility`

## Performance Considerations

- **Runtime**: Comparison takes N times longer (N = number of methods)
- **Memory**: Each backtest stores full results
- **Recommended**: Start with 3-4 methods, then expand if needed

## Related Documentation

- **Hyperparameter Tuning**: See `HYPERPARAMETER_TUNING_GUIDE.md`
- **Portfolio Optimization**: See `PORTFOLIO_OPTIMIZATION_QUICK_REFERENCE.md`
- **Backtesting**: See `HOW_TO_RUN_PORTFOLIO_OPTIMIZATION.md`

## Example Script

See `examples/optimization_comparison_backtest_demo.py` for a complete working example.

## Questions?

This feature integrates portfolio optimization theory directly into your backtesting workflow, helping you make data-driven decisions about position sizing. The results can guide you in choosing the most effective optimization method for your specific strategy and market conditions.
