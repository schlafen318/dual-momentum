# Strategy Comparison Agent

Automated agent for testing all available strategies against a benchmark to identify outperforming strategies.

## Features

- **Automatic Discovery**: Discovers and tests all available strategies
- **Benchmark Comparison**: Compares each strategy against a benchmark
- **Parallel Execution**: Runs multiple backtests in parallel for speed
- **Comprehensive Metrics**: Calculates returns, Sharpe ratio, drawdown, and more
- **Outperformance Detection**: Automatically identifies strategies that outperform the benchmark
- **Detailed Reporting**: Generates comprehensive comparison reports

## Quick Start

### Python Usage

```python
from datetime import datetime
from src.agents.strategy_comparison_agent import (
    StrategyComparisonAgent,
    ComparisonConfig
)

# Create agent
agent = StrategyComparisonAgent()

# Configure comparison
config = ComparisonConfig(
    start_date=datetime(2015, 1, 1),
    end_date=datetime(2024, 1, 1),
    universe=['SPY', 'EFA', 'EEM', 'AGG'],
    benchmark_symbol='SPY',
    min_excess_return=0.0,  # At least match benchmark
    parallel=True,
    max_workers=4
)

# Run comparison
results = agent.compare_all_strategies(config)

# Get outperforming strategies
outperforming = agent.get_outperforming_strategies(results, config)

# Print results
for strategy in outperforming:
    print(f"{strategy.strategy_name}: {strategy.excess_return:.2%} excess return")

# Generate report
report = agent.generate_report(results, output_file=Path("report.txt"))
```

### REST API Usage

```python
import requests

# Submit comparison request
response = requests.post("http://localhost:8000/api/strategies/compare", json={
    "universe": ["SPY", "EFA", "EEM", "AGG"],
    "benchmark_symbol": "SPY",
    "start_date": "2015-01-01",
    "end_date": "2024-01-01",
    "min_excess_return": 0.0
})

comparison_id = response.json()["comparison_id"]

# Poll for results
import time
while True:
    status = requests.get(f"http://localhost:8000/api/strategies/compare/{comparison_id}").json()
    if status["status"] == "completed":
        results = status["results"]
        print(f"Outperforming: {results['summary']['outperforming']}")
        break
    time.sleep(2)
```

## Configuration Options

### ComparisonConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | datetime | Required | Backtest start date |
| `end_date` | datetime | Required | Backtest end date |
| `universe` | List[str] | Required | Asset symbols to test |
| `benchmark_symbol` | str | Required | Benchmark symbol |
| `initial_capital` | float | 100000.0 | Starting capital |
| `commission` | float | 0.001 | Commission rate |
| `slippage` | float | 0.0005 | Slippage rate |
| `risk_free_rate` | float | 0.0 | Risk-free rate |
| `strategy_ids` | List[str] | None | Specific strategies to test (all if None) |
| `exclude_strategy_ids` | List[str] | None | Strategies to exclude |
| `min_excess_return` | float | 0.0 | Minimum excess return for outperformance |
| `min_sharpe_ratio` | float | None | Minimum Sharpe ratio |
| `max_workers` | int | 4 | Number of parallel workers |
| `parallel` | bool | True | Run in parallel |
| `api_keys` | Dict[str, str] | None | API keys for data sources |

## Output

### StrategyResult

Each strategy test returns a `StrategyResult` object with:

- **Basic Info**: `strategy_id`, `strategy_name`, `success`, `error`
- **Performance Metrics**: `total_return`, `annualized_return`, `sharpe_ratio`, `max_drawdown`, `volatility`
- **Benchmark Comparison**: `benchmark_total_return`, `excess_return`, `outperformance`
- **Additional Metrics**: Full `metrics` dictionary

### Report Format

The generated report includes:

1. **Summary**: Total strategies tested, successful, outperforming
2. **Outperforming Strategies**: Table of strategies that beat the benchmark
3. **All Results**: Complete table of all tested strategies

## Examples

See `examples/strategy_comparison_example.py` for a complete example.

## Performance Tips

1. **Use Parallel Execution**: Set `parallel=True` and adjust `max_workers` based on your CPU
2. **Filter Strategies**: Use `strategy_ids` to test only specific strategies
3. **Adjust Date Range**: Shorter periods run faster but may be less meaningful
4. **Cache Data**: The agent reuses fetched data when possible

## Integration with API

The agent is integrated into the REST API:

- **POST** `/api/strategies/compare` - Start comparison
- **GET** `/api/strategies/compare/{id}` - Get results

See the API documentation for details.

