# How `position_count` is Set

## Overview

`position_count` controls the maximum number of positions the strategy will hold. It flows through multiple layers of the system:

```
YAML Config → Strategy Loader → Strategy Instance → Backtest Engine
```

## Default Value

**Hard-coded default: `1`**

Location: `/workspace/dual_momentum_system/src/strategies/dual_momentum.py` (line 50)

```python
default_config = {
    'lookback_period': 252,
    'rebalance_frequency': 'monthly',
    'position_count': 1,  # ← DEFAULT
    'absolute_threshold': 0.0,
    'use_volatility_adjustment': False,
    'safe_asset': None,
}
```

## Configuration Sources (in Priority Order)

### 1. **Direct Code Override** (Highest Priority)

When creating a strategy instance directly in Python:

```python
from src.strategies import DualMomentumStrategy

strategy = DualMomentumStrategy(config={
    'lookback_period': 252,
    'position_count': 5,  # ← Override here
    'safe_asset': 'AGG'
})
```

**Example locations:**
- `examples/complete_backtest_example.py` (line 142)
- Test scripts
- Jupyter notebooks

---

### 2. **YAML Configuration File**

When loading from a YAML config file:

**File:** `/workspace/dual_momentum_system/config/strategies/dual_momentum_default.yaml`

```yaml
# Default configuration for Dual Momentum Strategy
lookback_period: 252
rebalance_frequency: monthly
position_count: 1  # ← Set here
absolute_threshold: 0.0
safe_asset: AGG
```

**Loading method:**

```python
from src.config import ConfigManager

config_mgr = ConfigManager()
strategy_config = config_mgr.load_config('strategies/dual_momentum_default.yaml')

strategy = DualMomentumStrategy(config=strategy_config)
```

---

### 3. **Strategy Registry (STRATEGIES.yaml)**

Centralized strategy definitions in the registry:

**File:** `/workspace/dual_momentum_system/config/STRATEGIES.yaml`

```yaml
strategies:
  dual_momentum_classic:
    name: "Classic Dual Momentum"
    class: DualMomentumStrategy
    parameters:
      lookback_period: 252
      position_count: 1  # ← Defined in registry
      safe_asset: AGG
      
  dual_momentum_multi:
    name: "Multi-Asset Dual Momentum"
    class: DualMomentumStrategy
    parameters:
      lookback_period: 252
      position_count: 3  # ← Different value for this variant
      safe_asset: AGG
```

**Loading method:**

```python
from src.config import get_strategy_loader

loader = get_strategy_loader()
strategy = loader.create_strategy('dual_momentum_classic')
# or with override:
strategy = loader.create_strategy(
    'dual_momentum_classic',
    custom_params={'position_count': 5}  # ← Override registry value
)
```

---

### 4. **Frontend UI (Strategy Builder)**

When using the Streamlit dashboard:

**File:** `/workspace/dual_momentum_system/frontend/pages/strategy_builder.py` (lines 163-170)

```python
position_count = st.number_input(
    "Number of Positions",
    min_value=1,
    max_value=len(symbols) if symbols else 10,
    value=min(3, len(symbols) if symbols else 3),  # ← UI default: 3
    help="How many top-ranked assets to hold simultaneously"
)
st.session_state.position_count = position_count
```

**UI Flow:**
1. User selects position count in the UI (default: 3)
2. Saved to `st.session_state.position_count`
3. Passed to strategy config when running backtest:

```python
strategy_config = {
    'lookback_period': st.session_state.get('lookback_period'),
    'position_count': st.session_state.get('position_count'),  # ← From UI
    # ... other params
}
```

---

## How to Check Current Value

### Method 1: Query the Strategy Instance

```python
# After creating strategy
position_count = strategy.get_position_count()
print(f"Position count: {position_count}")
```

### Method 2: Check Config Dictionary

```python
# Access config directly
position_count = strategy.config.get('position_count')
print(f"Position count: {position_count}")
```

### Method 3: Check During Backtest

Add logging to your backtest script:

```python
from loguru import logger

logger.info(f"Strategy position_count: {strategy.get_position_count()}")
logger.info(f"Full config: {strategy.config}")

results = engine.run(strategy, price_data)
```

---

## Common Configuration Scenarios

### Scenario 1: Classic Dual Momentum (1 position)

```yaml
position_count: 1
```

- Holds only the top-ranked risky asset
- Rotates to safe asset when all risky assets fail momentum filter
- Concentrated exposure, high turnover

### Scenario 2: Diversified Multi-Asset (3-5 positions)

```yaml
position_count: 3
```

- Holds top 3 risky assets
- Better diversification
- Lower turnover
- Reduces concentration risk

### Scenario 3: Full Universe Allocation (10+ positions)

```yaml
position_count: 13  # Example for 13-asset universe
```

- Holds all passing assets (or as many as specified)
- Maximum diversification
- Lower turnover
- May dilute returns

---

## Relationship to Cash Allocation

**Key Formula:**

```python
# In engine.py (lines 705-708)
risk_share = included_count / desired_positions

# Where:
# - desired_positions = position_count from config
# - included_count = number of risky assets that passed momentum filter
```

**Example:**

| `position_count` | Assets Passing Filter | `risk_share` | Cash Allocation |
|------------------|----------------------|--------------|-----------------|
| 1 | 1 | 1/1 = 100% | 0% (assuming safe asset available) |
| 3 | 3 | 3/3 = 100% | ~0% + transaction costs |
| 3 | 2 | 2/3 = 67% | ~33% (unless safe asset fills gap) |
| 13 | 12 | 12/13 = 92% | **~8%** (matches your observation!) |

---

## Most Likely Explanation for Your 7.52% Cash

Based on your screenshots showing:
- Cash: 7.52%
- Risky assets: 92.48% (across 3 visible positions)

**Two possible scenarios:**

### Scenario A: Large Position Count

```yaml
position_count: 13  # (or 14, 27, etc.)
```

- You configured `position_count` to a large value (13+)
- Only 12 risky assets passed the momentum filter on Nov 2, 2023
- Result: 12/13 = 92.31% → after costs ≈ 92.48%
- Cash: 7.52%

### Scenario B: UI Default Not Noticed

If you used the **Streamlit frontend**, the UI defaults to:

```python
value=min(3, len(symbols) if symbols else 3)  # Line 167 in strategy_builder.py
```

But the actual allocation might be different based on:
- How many symbols you selected
- Whether you changed the default
- Template or preset you loaded

---

## How to Fix the Cash Allocation Issue

### Option 1: Set position_count = Actual Number of Assets

```yaml
position_count: 12  # Match the number that typically pass filters
```

### Option 2: Configure Safe Asset (Recommended)

```yaml
position_count: 13
safe_asset: AGG  # Fills remaining 7.52% with bonds instead of cash
```

### Option 3: Reduce position_count

```yaml
position_count: 3  # Only hold top 3 assets, rest in safe asset
```

---

## Quick Diagnostic Commands

Run this in your backtest script to see what's configured:

```python
print("="*60)
print("STRATEGY CONFIGURATION DIAGNOSTIC")
print("="*60)
print(f"position_count: {strategy.get_position_count()}")
print(f"safe_asset: {strategy.config.get('safe_asset')}")
print(f"lookback_period: {strategy.config.get('lookback_period')}")
print(f"absolute_threshold: {strategy.config.get('absolute_threshold')}")
print(f"Full config: {strategy.config}")
print("="*60)
```

---

## Summary

`position_count` can be set in **4 places** (in priority order):

1. **Direct code** (`config={'position_count': X}`) ← Highest priority
2. **Custom YAML file** (via ConfigManager)
3. **Strategy Registry** (STRATEGIES.yaml)
4. **UI input** (Streamlit frontend) ← Defaults to 3

**Default if not specified anywhere: `1`**

Your 7.52% cash allocation suggests `position_count` was set to **~13** somewhere in the configuration chain.

---

**Generated:** 2025-10-22  
**Based on:** Dual Momentum System v0.2.28+
