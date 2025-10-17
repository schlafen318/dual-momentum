# Configuration System

This directory contains the comprehensive configuration system for asset universes and trading strategies.

## Files

### ASSET_UNIVERSES.yaml
Pre-built asset universes covering various asset classes and strategies:
- **27 universes** across multiple categories
- Global Equity Momentum (GEM)
- Sector rotation (US & International)
- Cryptocurrency
- Multi-asset portfolios
- Factor-based strategies
- Commodities and inflation hedge
- Fixed income
- Thematic strategies
- Geographic focus
- And more...

### STRATEGIES.yaml
Registry of pre-configured trading strategies:
- **16 strategies** across 7 categories
- Dual momentum variants
- Absolute momentum variants
- Sector rotation
- Crypto strategies
- Multi-asset strategies
- Factor strategies
- Income strategies

### custom_universes.yaml (created on demand)
Stores user-defined custom universes created through the API.

## Quick Start

### Using Pre-built Configurations

```python
from src.config import get_config_api

api = get_config_api()

# Get all universes and strategies
universes = api.get_all_universes()
strategies = api.get_all_strategies()

# Create a strategy with a universe
success, strategy, msg = api.create_configured_strategy(
    strategy_id='dual_momentum_classic',
    universe_id='gem_classic'
)
```

### Creating Custom Universes

```python
# Create custom universe
success, msg = api.create_universe('my_stocks', {
    'name': 'My Stock Portfolio',
    'description': 'My favorite tech stocks',
    'asset_class': 'equity',
    'symbols': ['AAPL', 'MSFT', 'GOOGL', 'NVDA'],
    'benchmark': 'QQQ'
})
```

### Searching and Filtering

```python
# Search universes
crypto_universes = api.search_universes('crypto')

# Filter strategies by category
momentum_strategies = api.get_strategies_by_category('momentum')

# Get compatible universes for a strategy
compatible = api.get_compatible_universes('dual_momentum_classic')
```

## Available Universes

### Classic Strategies
- `gem_classic` - Global Equity Momentum (SPY, VEU, BND)
- `gem_extended` - Extended GEM with more asset classes

### Sector Rotation
- `global_sectors_us` - 11 US GICS sectors
- `global_sectors_intl` - Global sector coverage

### Cryptocurrency
- `crypto_major` - Top 5 cryptocurrencies
- `crypto_extended` - Top 15 cryptocurrencies

### Multi-Asset
- `multi_asset_balanced` - 40/40/20 equity/bonds/alternatives
- `multi_asset_aggressive` - 70/20/10 growth-oriented
- `multi_asset_conservative` - 30/60/10 conservative

### Factor-Based
- `factor_momentum` - Momentum factor exposure
- `factor_value` - Value factor exposure
- `factor_quality` - Quality factor exposure

### Fixed Income
- `bonds_treasury_ladder` - US Treasury ladder
- `bonds_credit` - Corporate bond spectrum

### Thematic
- `tech_innovation` - Technology & innovation
- `clean_energy` - ESG & sustainability
- `emerging_markets` - Emerging market focus

### Income
- `dividend_aristocrats` - High-quality dividend stocks
- `global_income` - Diversified income portfolio

### Geographic
- `us_market_cap` - US market by size
- `european_markets` - European equity markets
- `asia_pacific` - Asia-Pacific markets

### Commodities
- `commodities_broad` - Broad commodity exposure
- `precious_metals` - Gold, silver, platinum

### Defensive
- `low_volatility` - Low-volatility equity
- `all_weather` - Risk-parity inspired

## Available Strategies

### Dual Momentum
- `dual_momentum_classic` - Classic GEM strategy (12-month, top 1)
- `dual_momentum_aggressive` - Aggressive variant (6-month, top 3)
- `dual_momentum_defensive` - Conservative with 5% threshold
- `dual_momentum_vol_adjusted` - Risk-adjusted rankings

### Absolute Momentum
- `absolute_momentum_classic` - Time-series momentum (12-month)
- `absolute_momentum_ma_crossover` - 50/200 MA crossover
- `absolute_momentum_fast` - Short-term (3-month)

### Sector Rotation
- `sector_rotation_monthly` - Monthly sector rotation
- `sector_rotation_defensive` - Defensive sector focus

### Crypto
- `crypto_momentum_weekly` - Weekly crypto momentum
- `crypto_absolute_daily` - Daily absolute momentum

### Multi-Asset
- `multi_asset_tactical` - Tactical asset allocation
- `all_weather_momentum` - Risk-parity with momentum

### Factor
- `momentum_factor_long_only` - Pure momentum factor

### Income
- `dividend_momentum` - Dividend-focused momentum

### Commodity
- `commodity_trend` - Commodity trend following

## Parameter Templates

Use parameter templates for quick configuration:

```python
# Conservative: Long lookback, quarterly rebalance, 5% threshold
# Moderate: 12-month lookback, monthly rebalance
# Aggressive: 6-month lookback, weekly rebalance
# High-Frequency: 30-day lookback, daily rebalance

strategy = api.create_strategy(
    'dual_momentum_classic',
    template='conservative'
)
```

## Rebalancing Frequencies

- **Daily**: High-frequency strategies, crypto
- **Weekly**: Short-term tactical, crypto momentum
- **Monthly**: Standard for momentum strategies
- **Quarterly**: Long-term allocation, tax-efficient
- **Yearly**: Buy-and-hold rebalancing

## Safe Assets

Default safe assets for defensive positioning:
- **SHY**: 1-3 year Treasuries (low volatility)
- **BIL**: 1-3 month T-Bills (cash equivalent)
- **AGG**: US aggregate bonds (broad exposure)
- **TLT**: 20+ year Treasuries (higher duration)
- **USDT**: Stablecoin (for crypto strategies)

## Validation

The system includes automatic validation:

```python
# Validate strategy-universe compatibility
is_valid, msg = api.validate_strategy_universe_pair(
    'dual_momentum_classic',
    'gem_classic'
)

# Validate complete configuration
is_valid, errors, warnings = api.validate_config(
    strategy_id='dual_momentum_classic',
    universe_id='gem_classic',
    params={'lookback_period': 252}
)
```

## Quick-Start Recommendations

Get pre-validated strategy-universe pairs:

```python
recommendations = api.get_quick_start_configs()

# Returns configurations like:
# - Classic GEM (Moderate)
# - US Sector Rotation (Moderate)
# - Crypto Momentum (Aggressive)
# - Multi-Asset Tactical (Moderate)
# - Aggressive Growth (Aggressive)
# - Conservative Income (Conservative)
```

## Frontend Integration

### Example: Strategy Selector

```python
import streamlit as st
from src.config import get_config_api

api = get_config_api()

# Get all strategies grouped by category
categories = api.list_categories()
selected_category = st.selectbox("Category", categories)

# Get strategies in category
strategies = api.get_strategies_by_category(selected_category)
strategy_options = {sid: info['name'] for sid, info in strategies.items()}

selected_strategy = st.selectbox("Strategy", strategy_options.keys(),
    format_func=lambda x: strategy_options[x])

# Show strategy details
if selected_strategy:
    info = api.get_strategy(selected_strategy)
    st.write(info['description'])
    
    # Show compatible universes
    compatible = api.get_compatible_universes(selected_strategy)
    st.multiselect("Compatible Universes", compatible)
```

### Example: Universe Manager

```python
# Create universe form
with st.form("create_universe"):
    name = st.text_input("Name")
    symbols = st.text_area("Symbols (one per line)")
    asset_class = st.selectbox("Asset Class",
        ["equity", "crypto", "commodity", "bond", "fx", "multi_asset"])
    
    if st.form_submit_button("Create"):
        symbols_list = [s.strip() for s in symbols.split('\n') if s.strip()]
        success, msg = api.create_universe(name, {
            'name': name,
            'symbols': symbols_list,
            'asset_class': asset_class
        })
        
        if success:
            st.success(msg)
        else:
            st.error(msg)
```

## File Format

### Universe Definition

```yaml
universe_id:
  name: "Universe Display Name"
  description: "Brief description"
  asset_class: equity  # equity, bond, commodity, crypto, fx, multi_asset
  benchmark: SPY  # Reference benchmark
  symbols:
    - SYMBOL1
    - SYMBOL2
    - SYMBOL3
  metadata:
    key: value
    rebalance_recommended: monthly
```

### Strategy Definition

```yaml
strategy_id:
  name: "Strategy Display Name"
  description: "Brief description"
  class: "StrategyClassName"
  module: "src.strategies.module_name"
  version: "1.0.0"
  category: momentum
  parameters:
    lookback_period: 252
    rebalance_frequency: monthly
    # ... other parameters
  recommended_universes:
    - universe_id1
    - universe_id2
  min_assets: 2
  tags:
    - momentum
    - tactical
```

## Adding New Configurations

### Add a New Universe

1. Edit `ASSET_UNIVERSES.yaml`
2. Add new universe definition following the format
3. No code changes needed - automatically loaded

### Add a New Strategy

1. Edit `STRATEGIES.yaml`
2. Add new strategy definition under `strategies:`
3. Ensure the strategy class exists in `src/strategies/`
4. No code changes needed - automatically loaded

## API Reference

See detailed documentation in:
- `src/config/config_api.py` - Main API
- `src/config/universe_loader.py` - Universe management
- `src/config/strategy_loader.py` - Strategy management

## Examples

Run the examples to see the system in action:

```bash
# Verification script
python3 verify_config_system.py

# Usage examples
python3 examples/config_system_usage.py
```

## Support

For detailed documentation, see:
- `CONFIG_SYSTEM_SUMMARY.md` - Complete system overview
- `examples/config_system_usage.py` - Usage examples
- Source code docstrings - API documentation
