# Architecture Documentation

## Overview

The Dual Momentum Backtesting Framework is built on a **plugin-based architecture** that enables maximum extensibility without modifying core code. This document explains the architectural principles and design patterns used.

## Core Principles

### 1. Plugin Architecture

All major components (asset classes, data sources, strategies, risk managers) are implemented as plugins:

- **Auto-Discovery**: Plugins are automatically discovered by scanning designated directories
- **Loose Coupling**: Plugins depend only on abstract base classes, not on each other
- **Hot-Swappable**: Any plugin can be replaced without affecting others
- **Zero Core Modifications**: New functionality is added by creating new files

### 2. Separation of Concerns

The framework is organized into distinct layers:

```
┌─────────────────────────────────────────────┐
│           Frontend Layer (Future)           │
│         (Streamlit UI, Dashboards)          │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│          Backtesting Engine Layer           │
│    (Execution, Results, Performance)        │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│            Strategy Layer                   │
│  (Momentum Calculation, Signal Generation)  │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│             Data Layer                      │
│    (Data Sources, Asset Classes)            │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│             Core Layer                      │
│   (Base Classes, Plugin Manager, Types)     │
└─────────────────────────────────────────────┘
```

### 3. Strategy Pattern

All plugins implement the Strategy pattern:

- Abstract base classes define interfaces
- Concrete implementations provide specific behavior
- Clients program to interfaces, not implementations

### 4. Configuration-Driven

System behavior is controlled through configuration:

- YAML/TOML configuration files
- Per-plugin configuration
- Environment variable support
- Programmatic configuration

## Core Components

### Plugin Manager

**Location**: `src/core/plugin_manager.py`

**Responsibilities**:
- Discover plugins in designated directories
- Register plugin classes in a central registry
- Provide access to registered plugins
- Manage plugin lifecycle

**Key Classes**:
- `PluginManager`: Main manager class
- `PluginRegistry`: Storage for registered plugins

**Plugin Discovery Flow**:

```
1. Scan plugin directories (asset_classes, strategies, etc.)
2. For each Python file:
   a. Import the module
   b. Inspect for classes inheriting from base classes
   c. Register non-abstract classes
3. Make registered plugins available via getters
```

### Base Classes

#### BaseAssetClass

**Location**: `src/core/base_asset.py`

**Purpose**: Define interface for asset class implementations

**Key Methods**:
- `get_asset_type()`: Return asset type (equity, bond, crypto, etc.)
- `validate_symbol()`: Check if symbol format is valid
- `get_metadata()`: Retrieve asset metadata
- `normalize_data()`: Convert raw data to standard format

**Extension Points**:
- `calculate_returns()`: Custom return calculation
- `calculate_volatility()`: Custom volatility calculation
- `get_trading_calendar()`: Asset-specific trading days

#### BaseDataSource

**Location**: `src/core/base_data_source.py`

**Purpose**: Define interface for data source implementations

**Key Methods**:
- `fetch_data()`: Retrieve historical price data
- `get_supported_assets()`: List available symbols
- `get_supported_timeframes()`: List available intervals

**Extension Points**:
- `fetch_multiple()`: Batch fetching optimization
- `get_asset_info()`: Additional asset information
- `is_available()`: Service health check

#### BaseStrategy

**Location**: `src/core/base_strategy.py`

**Purpose**: Define interface for momentum strategy implementations

**Key Methods**:
- `calculate_momentum()`: Calculate momentum scores
- `generate_signals()`: Create trading signals
- `get_momentum_type()`: Return momentum type (absolute/relative/dual)

**Extension Points**:
- `get_required_history()`: Specify data requirements
- `get_rebalance_frequency()`: Define rebalancing schedule
- `should_rebalance()`: Custom rebalancing logic

#### BaseRiskManager

**Location**: `src/core/base_risk.py`

**Purpose**: Define interface for risk management implementations

**Key Methods**:
- `calculate_position_size()`: Determine trade size
- `check_risk_limits()`: Validate risk constraints
- `get_max_leverage()`: Return leverage limit

**Extension Points**:
- `adjust_for_volatility()`: Volatility targeting
- `adjust_for_correlation()`: Correlation-based sizing
- `check_drawdown_limit()`: Drawdown monitoring

### Type System

**Location**: `src/core/types.py`

**Purpose**: Define common data structures

**Key Types**:

```python
@dataclass
class PriceData:
    """Container for OHLCV price data"""
    symbol: str
    data: pd.DataFrame
    metadata: AssetMetadata
    timeframe: str

@dataclass
class Signal:
    """Trading signal from strategy"""
    timestamp: datetime
    symbol: str
    direction: int  # 1=long, -1=short, 0=neutral
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any]

@dataclass
class Position:
    """Open trading position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_timestamp: datetime
    current_price: float
    current_timestamp: datetime
```

### Configuration Manager

**Location**: `src/config/config_manager.py`

**Purpose**: Manage configuration files and settings

**Features**:
- Load YAML/TOML files
- Environment variable substitution
- Configuration caching
- Default configurations

## Design Patterns Used

### 1. Abstract Factory Pattern

The plugin manager acts as an abstract factory:

```python
# Factory creates appropriate implementation
manager = get_plugin_manager()
strategy_class = manager.get_strategy('DualMomentumStrategy')
strategy = strategy_class(config={...})
```

### 2. Strategy Pattern

Each plugin type uses the strategy pattern:

```python
# Different strategies, same interface
class DualMomentumStrategy(BaseStrategy):
    def calculate_momentum(self, price_data):
        # Dual momentum implementation
        pass

class AbsoluteMomentumStrategy(BaseStrategy):
    def calculate_momentum(self, price_data):
        # Absolute momentum implementation
        pass
```

### 3. Template Method Pattern

Base classes provide template methods with extension points:

```python
class BaseAssetClass:
    def calculate_returns(self, price_data, method='simple'):
        # Template method with default behavior
        if method == 'simple':
            return price_data.data['close'].pct_change()
        # Subclasses can override for custom behavior
```

### 4. Registry Pattern

The plugin registry maintains a catalog of available plugins:

```python
class PluginRegistry:
    def __init__(self):
        self.asset_classes = {}
        self.strategies = {}
        # ...
    
    def register_strategy(self, name, cls):
        self.strategies[name] = cls
```

### 5. Singleton Pattern

Global instances for managers:

```python
_global_manager = None

def get_plugin_manager():
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager
```

## Extension Mechanisms

### Adding New Plugin Types

To add a completely new plugin type:

1. Create base class in `src/core/base_<type>.py`
2. Add registry to `PluginRegistry`
3. Add discovery method to `PluginManager`
4. Create plugin directory `src/<type>s/`

### Adding New Plugins

To add a new plugin of existing type:

1. Create file in appropriate directory
2. Inherit from base class
3. Implement required abstract methods
4. Optional: Override extension points

Example:

```python
# src/strategies/my_strategy.py
from ..core.base_strategy import BaseStrategy
from ..core.types import MomentumType

class MyStrategy(BaseStrategy):
    def calculate_momentum(self, price_data):
        # Your implementation
        pass
    
    def generate_signals(self, price_data):
        # Your implementation
        pass
    
    def get_momentum_type(self):
        return MomentumType.CUSTOM
```

## Data Flow

### Typical Backtesting Flow

```
1. Configuration
   ↓
   config_manager.load_config('my_config.yaml')
   ↓
2. Plugin Instantiation
   ↓
   manager = get_plugin_manager()
   data_source = manager.get_data_source('YahooFinanceSource')()
   strategy = manager.get_strategy('DualMomentumStrategy')(config)
   ↓
3. Data Retrieval
   ↓
   price_data = data_source.fetch_data(symbol, start, end)
   ↓
4. Data Normalization
   ↓
   asset_class = manager.get_asset_class('EquityAsset')()
   normalized = asset_class.normalize_data(price_data, symbol)
   ↓
5. Signal Generation
   ↓
   signals = strategy.generate_signals(normalized)
   ↓
6. Position Sizing
   ↓
   risk_manager = manager.get_risk_manager('BasicRiskManager')(config)
   size = risk_manager.calculate_position_size(signal, portfolio_value, positions)
   ↓
7. Execution & Results
   ↓
   backtest_engine.execute(signals, size)
   ↓
8. Performance Analysis
   ↓
   results = backtest_engine.get_results()
```

## Error Handling

The framework uses a layered error handling approach:

1. **Plugin Level**: Plugins validate inputs and raise specific exceptions
2. **Manager Level**: Plugin manager catches and logs errors during discovery
3. **Application Level**: Top-level code handles operational errors

Example:

```python
# Plugin level
def validate_symbol(self, symbol: str) -> bool:
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    return True

# Manager level
try:
    module = self._import_module_from_file(file_path)
except Exception as e:
    logger.error(f"Error loading plugin: {e}")
    continue

# Application level
try:
    data = data_source.fetch_data(symbol, start, end)
except ConnectionError as e:
    logger.error(f"Failed to fetch data: {e}")
    # Fallback or retry logic
```

## Performance Considerations

### Plugin Discovery

- Plugins are discovered once at initialization
- Results are cached in memory
- Re-discovery only on explicit request

### Data Caching

- Data sources implement caching
- Configurable cache policies
- Memory vs. disk tradeoffs

### Batch Operations

- Support for batch data fetching
- Vectorized calculations where possible
- Parallel processing opportunities

## Testing Strategy

### Unit Tests

- Test each base class interface
- Test plugin discovery
- Test plugin registration
- Test configuration loading

### Integration Tests

- Test plugin interaction
- Test data flow
- Test error handling
- Test configuration integration

### Plugin Tests

- Each plugin has its own test suite
- Tests verify interface compliance
- Tests verify specific functionality

## Future Enhancements

### Planned Features

1. **Dynamic Plugin Loading**: Hot-reload plugins without restart
2. **Plugin Dependencies**: Declare dependencies between plugins
3. **Plugin Versioning**: Support multiple versions of same plugin
4. **Plugin Marketplace**: Share and discover community plugins
5. **Performance Profiling**: Built-in profiling for plugins
6. **Plugin Sandboxing**: Isolate plugin execution for security

### Extension Points

1. **Execution Layer**: Trade execution simulation
2. **Optimization Layer**: Parameter optimization
3. **Analysis Layer**: Performance attribution
4. **Visualization Layer**: Interactive dashboards

## Best Practices

### For Plugin Developers

1. **Follow Interface**: Implement all abstract methods
2. **Validate Inputs**: Check and validate all inputs
3. **Document Thoroughly**: Use docstrings and type hints
4. **Handle Errors**: Raise appropriate exceptions
5. **Test Extensively**: Write comprehensive tests
6. **Version Properly**: Use semantic versioning

### For Framework Users

1. **Use Abstractions**: Program to interfaces
2. **Configure Externally**: Use config files
3. **Handle Errors**: Expect and handle failures
4. **Monitor Performance**: Profile critical paths
5. **Update Regularly**: Keep plugins and framework current

## Conclusion

The plugin architecture provides a flexible, extensible foundation for building complex trading systems. By following the established patterns and principles, developers can easily add new functionality while maintaining system integrity and performance.
