# Dual Momentum Backtesting REST API

REST API for programmatic backtesting of momentum strategies.

## Quick Start

### 1. Start the API Server

```bash
# From the project root
cd dual_momentum_system
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 2. Run a Backtest

```python
import requests

# Submit backtest
response = requests.post("http://localhost:8000/api/backtest/run", json={
    "strategy_id": "dual_momentum_classic",
    "universe": ["SPY", "EFA", "EEM", "AGG"],
    "start_date": "2015-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000.0,
    "benchmark_symbol": "SPY"
})

backtest_id = response.json()["backtest_id"]

# Poll for results
import time
while True:
    status = requests.get(f"http://localhost:8000/api/backtest/{backtest_id}").json()
    if status["status"] == "completed":
        results = status["result"]
        print(f"Total Return: {results['total_return']:.2%}")
        break
    time.sleep(2)
```

## API Endpoints

### Backtesting

#### `POST /api/backtest/run`
Run a backtest asynchronously.

**Request Body:**
```json
{
  "strategy_id": "dual_momentum_classic",
  "universe": ["SPY", "EFA", "EEM"],
  "start_date": "2015-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000.0,
  "commission": 0.001,
  "slippage": 0.0005,
  "benchmark_symbol": "SPY",
  "strategy_params": {
    "lookback_period": 252
  }
}
```

**Response:** `202 Accepted`
```json
{
  "backtest_id": "uuid-here",
  "status": "queued",
  "message": "Backtest queued successfully"
}
```

#### `GET /api/backtest/{backtest_id}`
Get backtest status and results.

**Query Parameters:**
- `summary` (optional): If `true`, return only summary metrics

**Response:** `200 OK`
```json
{
  "backtest_id": "uuid-here",
  "status": "completed",
  "result": {
    "strategy_name": "Dual Momentum Classic",
    "start_date": "2015-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000.0,
    "final_capital": 150000.0,
    "total_return": 0.50,
    "annualized_return": 0.055,
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.15,
    "metrics": {...},
    "trades": [...],
    "equity_curve": {...}
  }
}
```

#### `POST /api/backtest/validate`
Validate backtest configuration without running it.

#### `GET /api/backtests`
List recent backtests (up to 50).

#### `DELETE /api/backtest/{backtest_id}`
Delete a backtest result.

### Strategies

#### `GET /api/strategies`
List all available strategies.

#### `GET /api/strategies/{strategy_id}`
Get strategy information.

### Universes

#### `GET /api/universes`
List all available universes.

#### `GET /api/universes/{universe_id}`
Get universe information.

### Health

#### `GET /api/health`
Health check endpoint.

## Request Models

### BacktestRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_id` | string | Yes | Strategy identifier |
| `universe` | array[string] | Yes | List of asset symbols |
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |
| `strategy_params` | object | No | Custom strategy parameters |
| `initial_capital` | float | No | Initial capital (default: 100000) |
| `commission` | float | No | Commission rate (default: 0.001) |
| `slippage` | float | No | Slippage rate (default: 0.0005) |
| `risk_free_rate` | float | No | Risk-free rate (default: 0.0) |
| `benchmark_symbol` | string | No | Benchmark symbol |
| `api_keys` | object | No | API keys for data sources |

## Response Models

### BacktestResult

The result object contains:

- **Summary Metrics:**
  - `total_return`: Total return percentage
  - `annualized_return`: Annualized return
  - `sharpe_ratio`: Sharpe ratio
  - `max_drawdown`: Maximum drawdown
  - `initial_capital`: Starting capital
  - `final_capital`: Ending capital

- **Time Series Data:**
  - `equity_curve`: Portfolio value over time
  - `returns`: Daily returns
  - `benchmark_curve`: Benchmark performance (if provided)

- **Trade History:**
  - `trades`: List of all trades with entry/exit details

- **Position History:**
  - `positions`: Position snapshots over time

- **Additional Metrics:**
  - `metrics`: Dictionary of performance metrics

## Examples

See `examples/api_usage_example.py` for complete examples.

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `202 Accepted`: Request accepted (async operation)
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with error information.

## Production Considerations

### Storage

The current implementation uses in-memory storage for backtest results. For production:

1. **Use a database** (PostgreSQL, MongoDB) for persistent storage
2. **Use Redis** for caching and job queues
3. **Implement result expiration** to manage storage

### Async Processing

For better scalability:

1. **Use Celery** or **RQ** for background job processing
2. **Implement job queues** for managing concurrent backtests
3. **Add rate limiting** to prevent abuse

### Security

1. **Add authentication** (API keys, OAuth)
2. **Implement rate limiting**
3. **Validate and sanitize inputs**
4. **Use HTTPS** in production

### Monitoring

1. **Add logging** (already using loguru)
2. **Implement metrics** (Prometheus, StatsD)
3. **Add health checks** (already implemented)
4. **Monitor resource usage**

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Railway/Heroku

Add to `Procfile`:
```
api: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables

- `PORT`: Server port (default: 8000)
- `ALPHAVANTAGE_API_KEY`: Alpha Vantage API key (optional)
- `TWELVEDATA_API_KEY`: Twelve Data API key (optional)

## Testing

```bash
# Run API server
uvicorn src.api.main:app --reload

# In another terminal, run examples
python examples/api_usage_example.py
```

## Support

For issues or questions, see the main project documentation.

