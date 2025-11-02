# Multi-Strategy Asset Class Implementation

## Summary
Added "Multi-Strategy" as a new asset class option in the Strategy Builder, allowing users to backtest portfolios with mixed asset classes (equities, bonds, commodities, REITs, etc.) in a single portfolio.

## Changes Made

### 1. Strategy Builder (`dual_momentum_system/frontend/page_modules/strategy_builder.py`)

#### Added "Multi-Strategy" to Asset Class Options (Line 81-86)
```python
asset_class = st.selectbox(
    "Asset Class",
    ["Equity", "Crypto", "Commodity", "Bond", "FX", "Multi-Strategy"],
    help="Choose the type of assets you want to trade. Multi-Strategy allows backtesting portfolios with mixed asset classes."
)
```

#### Updated Universe Filtering Logic (Line 94-106)
- For "Multi-Strategy" selection, the system now shows:
  - All universes marked as `multi_asset` in the YAML configuration
  - Falls back to showing all universes if no `multi_asset` universes exist
- Other asset classes continue to filter by exact match

```python
if asset_class.lower() == "multi-strategy":
    filtered_universes = [
        u for u in universe_options
        if st.session_state.asset_universes[u]['asset_class'].lower() in ['multi_asset', 'multi-strategy']
    ] or universe_options  # Show all if no multi_asset universes exist
else:
    filtered_universes = [
        u for u in universe_options
        if st.session_state.asset_universes[u]['asset_class'].lower() == asset_class.lower()
    ]
```

#### Updated Asset Class Mapping (Line 470-478)
- Added `'multi-strategy': EquityAsset` to the asset class map
- EquityAsset is used for data normalization as it's flexible enough to handle mixed assets

```python
asset_class_map = {
    'equity': EquityAsset,
    'crypto': CryptoAsset,
    'commodity': CommodityAsset,
    'bond': BondAsset,
    'fx': FXAsset,
    'multi-strategy': EquityAsset  # Use EquityAsset for multi-asset normalization
}
```

### 2. Asset Universe Manager (`dual_momentum_system/frontend/page_modules/asset_universe_manager.py`)

#### Added "multi_asset" to Asset Class Selection (Line 173-177)
```python
asset_class = st.selectbox(
    "Asset Class *",
    ["equity", "crypto", "commodity", "bond", "fx", "multi_asset"],
    help="Type of assets in this universe. Use 'multi_asset' for portfolios with mixed asset classes."
)
```

#### Added Multi-Asset Quick Templates (Line 438-449)
Two new quick templates for multi-asset portfolios:

1. **Multi-Asset Balanced** (Line 438-443)
   - Balanced portfolio across stocks, bonds, commodities, and REITs
   - Symbols: SPY, QQQ, AGG, TLT, GLD, DBC, VNQ, IWM
   - Benchmark: SPY

2. **Multi-Asset Aggressive** (Line 444-449)
   - Growth-oriented multi-asset portfolio with higher equity allocation
   - Symbols: SPY, QQQ, VGK, EEM, GLD, TLT, DBC, USO
   - Benchmark: SPY

### 3. Existing Multi-Asset Support

The backend infrastructure already supports multi-asset portfolios:
- `universe_loader.py` validates `multi_asset` as a valid asset class (Line 30)
- `ASSET_UNIVERSES.yaml` includes several pre-built multi-asset universes:
  - `gem_extended`: Global Equity Momentum - Extended
  - `multi_asset_balanced`: Balanced portfolio (40% equities, 40% bonds, 20% alternatives)
  - `multi_asset_aggressive`: Aggressive growth (70% equities, 20% bonds, 10% alternatives)
  - `multi_asset_conservative`: Conservative portfolio (30% equities, 60% bonds, 10% alternatives)
  - `factor_momentum`: Multi-asset momentum factor exposure
  - `global_income`: Diversified income across asset classes
  - `all_weather`: Risk-parity inspired portfolio

## Usage

### In Strategy Builder
1. Navigate to the Strategy Builder page
2. Select **"Multi-Strategy"** from the Asset Class dropdown
3. Choose from available multi-asset universes:
   - Global Equity Momentum - Extended
   - Multi-Asset Balanced
   - Multi-Asset Aggressive Growth
   - Multi-Asset Conservative
   - All-Weather Portfolio
   - Global Income Portfolio
   - Factor - Momentum
   - Or create a Custom multi-asset universe
4. Configure strategy parameters as usual
5. Run backtest

### In Asset Universe Manager
1. Navigate to Asset Universe Manager
2. When creating a new universe, select **"multi_asset"** as the Asset Class
3. Add symbols from different asset classes (e.g., SPY, AGG, GLD)
4. Use quick templates:
   - Multi-Asset Balanced
   - Multi-Asset Aggressive

## Benefits

1. **Diversification**: Backtest portfolios that combine stocks, bonds, commodities, and other asset classes
2. **Cross-Asset Momentum**: Apply momentum strategies across different asset classes
3. **Risk Parity**: Test all-weather and risk-parity inspired strategies
4. **Tactical Asset Allocation**: Dynamically allocate between asset classes based on momentum signals
5. **Real-World Portfolios**: Model realistic multi-asset portfolios used by institutional investors

## Example Use Cases

1. **Classic 60/40 with Momentum**: Apply momentum to rotate between stocks and bonds
2. **All-Weather Strategy**: Balanced portfolio across equities, bonds, gold, and commodities
3. **Risk-On/Risk-Off**: Rotate between growth assets (stocks) and defensive assets (bonds, gold)
4. **Inflation Hedge**: Include commodities and gold alongside equities
5. **Global Tactical Asset Allocation**: Momentum-based rotation across global assets

## Technical Notes

- **Data Normalization**: EquityAsset is used for normalizing price data across all asset types, as it provides flexible data handling
- **Backward Compatibility**: All existing asset class functionality remains unchanged
- **YAML Configuration**: Multi-asset universes can be defined in `config/ASSET_UNIVERSES.yaml` with `asset_class: multi_asset`
- **Universe Validation**: The `universe_loader.py` already validated `multi_asset` as a valid asset class before this update

## Testing Recommendations

1. Test backtesting a multi-asset universe (e.g., "Multi-Asset Balanced")
2. Verify that data is fetched correctly for mixed asset types
3. Confirm that momentum calculations work across different asset classes
4. Check that rebalancing logic handles mixed asset portfolios correctly
5. Validate that performance metrics are calculated accurately

## Future Enhancements

Potential improvements for future development:
1. Asset-specific normalization: Use appropriate asset class handlers for each symbol
2. Asset class weighting: Allow users to specify target allocations per asset class
3. Cross-asset correlation analysis: Display correlation matrices in results
4. Risk parity optimization: Implement true risk-parity weighting
5. Multi-strategy blending: Combine different momentum strategies for different asset classes
