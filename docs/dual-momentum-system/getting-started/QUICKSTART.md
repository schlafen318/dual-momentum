# Quick Start Guide

Get up and running with the Dual Momentum Framework in 5 minutes.

## Installation

```bash
# Navigate to the project directory
cd dual_momentum_system

# Install the package in development mode
pip install -e .

# Or just install requirements
pip install -r requirements.txt
```

## Run the Demo

```bash
# See the plugin system in action
python demo_plugin_system.py
```

Expected output:
```
======================================================================
DUAL MOMENTUM FRAMEWORK - PLUGIN SYSTEM DEMONSTRATION
======================================================================

[STEP 1] Initializing Plugin Manager...
----------------------------------------------------------------------
Discovered Plugins:
  Asset Classes:  ['EquityAsset']
  Data Sources:   ['YahooFinanceSource']
  Strategies:     ['DualMomentumStrategy']
  Risk Managers:  ['BasicRiskManager']

...
```

## Run Tests

```bash
# Run all tests
pytest

# Or use the test runner script
./run_tests.sh

# Run specific test file
pytest tests/test_plugin_system.py -v
```

## Basic Usage

### 1. Get Plugin Manager

```python
from src.core import get_plugin_manager

# Auto-discovers all plugins
manager = get_plugin_manager()
```

### 2. List Available Plugins

```python
# See what's available
print("Strategies:", manager.list_strategies())
print("Data Sources:", manager.list_data_sources())
print("Asset Classes:", manager.list_asset_classes())
```

### 3. Create Strategy

```python
# Get the strategy class
DualMomentum = manager.get_strategy('DualMomentumStrategy')

# Create instance with config
strategy = DualMomentum(config={
    'lookback_period': 252,
    'rebalance_frequency': 'monthly',
    'position_count': 1,
    'safe_asset': 'SHY'
})
```

### 4. Get Data Source

```python
# Get data source class
YahooFinance = manager.get_data_source('YahooFinanceSource')

# Create instance
data_source = YahooFinance()
```

### 5. Fetch Data

```python
from datetime import datetime, timedelta

# Fetch historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

data = data_source.fetch_data(
    symbol='SPY',
    start_date=start_date,
    end_date=end_date,
    timeframe='1d'
)

print(data.head())
```

### 6. Create Asset Handler

```python
# Get asset class
Equity = manager.get_asset_class('EquityAsset')

# Create instance
equity = Equity()

# Validate symbols
print(equity.validate_symbol('AAPL'))  # True
print(equity.validate_symbol('invalid'))  # False

# Get metadata
metadata = equity.get_metadata('AAPL')
print(metadata.name)
```

## Add Your First Plugin

### Example: Create a Simple Momentum Strategy

Create `src/strategies/simple_momentum.py`:

```python
from typing import Dict, List, Union
import pandas as pd
from ..core.base_strategy import BaseStrategy
from ..core.types import MomentumType, PriceData, Signal

class SimpleMomentumStrategy(BaseStrategy):
    """A simple 12-month momentum strategy."""
    
    def calculate_momentum(self, price_data: Union[PriceData, Dict[str, PriceData]]):
        """Calculate 12-month returns."""
        if isinstance(price_data, PriceData):
            closes = price_data.data['close']
            return closes.pct_change(252)  # 12 months
        
        # Multiple assets
        momentum_dict = {}
        for symbol, data in price_data.items():
            closes = data.data['close']
            momentum_dict[symbol] = closes.pct_change(252)
        return momentum_dict
    
    def generate_signals(self, price_data: Union[PriceData, Dict[str, PriceData]]) -> List[Signal]:
        """Generate signals for top momentum assets."""
        momentum = self.calculate_momentum(price_data)
        
        # Implementation here...
        return []
    
    def get_momentum_type(self) -> MomentumType:
        return MomentumType.RELATIVE
```

**That's it!** The plugin manager will automatically discover it.

Verify it works:

```python
manager = get_plugin_manager()
print('SimpleMomentumStrategy' in manager.list_strategies())  # True
```

## Configuration

### Using Config Files

Create `config/strategies/my_config.yaml`:

```yaml
lookback_period: 252
rebalance_frequency: monthly
position_count: 3
universe:
  - SPY
  - QQQ
  - IWM
```

Load and use:

```python
from src.config.config_manager import get_config_manager

config_mgr = get_config_manager()
config = config_mgr.load_config('strategies/my_config.yaml')

strategy = DualMomentum(config=config)
```

## Next Steps

1. **Explore the code**: Look at example plugins in `src/`
2. **Read the docs**: Check `README.md` for detailed information
3. **Run tests**: Verify everything works with `pytest`
4. **Create plugins**: Add your own strategies, data sources, or asset classes
5. **Configure**: Customize behavior with YAML config files

## Common Tasks

### Add a New Data Source

1. Create file: `src/data_sources/my_source.py`
2. Inherit from `BaseDataSource`
3. Implement required methods:
   - `fetch_data()`
   - `get_supported_assets()`
   - `get_supported_timeframes()`

### Add a New Asset Class

1. Create file: `src/asset_classes/my_asset.py`
2. Inherit from `BaseAssetClass`
3. Implement required methods:
   - `get_asset_type()`
   - `validate_symbol()`
   - `get_metadata()`
   - `normalize_data()`

### Add a New Risk Manager

1. Create file: `src/backtesting/my_risk.py`
2. Inherit from `BaseRiskManager`
3. Implement required methods:
   - `calculate_position_size()`
   - `check_risk_limits()`
   - `get_max_leverage()`

## Troubleshooting

### Import Errors

Make sure you're in the project directory and have installed dependencies:

```bash
cd dual_momentum_system
pip install -r requirements.txt
```

### Plugin Not Discovered

1. Check file is in correct directory
2. Check class inherits from correct base class
3. Check class is not abstract (all abstract methods implemented)
4. Restart Python interpreter to reload plugin manager

### Tests Failing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_plugin_system.py::TestPluginDiscovery::test_discover_all -v
```

## Getting Help

- Check the `README.md` for comprehensive documentation
- Look at example plugins for reference
- Run the demo script to see everything in action
- Check test files for usage examples

---

**Happy backtesting! 🚀**
