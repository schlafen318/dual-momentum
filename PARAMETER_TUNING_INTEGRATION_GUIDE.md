# Parameter Tuning Integration Guide

## Overview

The parameter tuning functionality has been seamlessly integrated into the backtesting workflow, allowing users to easily fine-tune strategy parameters after viewing backtest results. This creates a smooth iterative optimization process.

## Key Features

### 1. **Quick Tune Tab in Backtest Results**
- **Location**: Backtest Results page → "⚡ Quick Tune" tab
- **Purpose**: Instantly adjust parameters and re-run backtests without leaving the results page
- **Features**:
  - Side-by-side comparison of current vs. adjusted parameters
  - Real-time parameter change tracking
  - One-click re-run with new parameters
  - Uses cached data for fast iteration

### 2. **Integrated Hyperparameter Tuning Button**
- **Location**: Backtest Results page → "📈 Overview" tab
- **Button**: "🎯 Tune Parameters" (highlighted as primary action)
- **Functionality**:
  - Pre-populates tuning configuration from current backtest
  - Auto-fills date range, capital, transaction costs
  - Sets parameter ranges around current values
  - Preserves asset universe and safe asset settings

### 3. **Apply Optimized Parameters**
- **Location**: Hyperparameter Tuning page → "📊 Results" tab
- **Actions Available**:
  - **"📊 View in Results Page"**: Immediately view the best backtest results
  - **"🔄 Re-run with Best Params"**: Apply parameters to Strategy Builder for customization
- **Smart Integration**:
  - Best parameters are automatically stored in session state
  - Strategy Builder shows a banner with optimized parameters
  - One-click apply or dismiss functionality

### 4. **Strategy Builder Pre-fill**
- **Location**: Strategy Builder page (when navigating from tuning)
- **Features**:
  - Shows optimized parameters banner at the top
  - Displays optimization score and method used
  - Expandable view of all parameters
  - Apply or dismiss options

## Workflow Examples

### Workflow 1: Quick Iterative Testing
```
1. Run backtest → View results
2. Click "⚡ Quick Tune" tab
3. Adjust parameters (e.g., change lookback from 252 to 189 days)
4. Click "🚀 Re-run Backtest"
5. Compare results immediately
6. Repeat until satisfied
```

### Workflow 2: Comprehensive Optimization
```
1. Run backtest → View results
2. Click "🎯 Tune Parameters" button
3. Review pre-populated configuration
4. (Optional) Adjust parameter ranges or optimization settings
5. Click "🚀 Start Optimization"
6. View results in "📊 Results" tab
7. Click "📊 View in Results Page" to see best backtest
8. Compare with original strategy using "➕ Add to Comparison"
```

### Workflow 3: Export and Reuse
```
1. Complete optimization
2. Download best parameters as JSON
3. Share or archive for future use
4. Import parameters in future backtests
```

## Implementation Details

### Session State Variables

The integration uses the following session state variables:

#### For Quick Tune:
- `backtest_results`: Current backtest results object
- `last_backtest_params`: Full configuration of last backtest
- `cached_price_data`: Price data cache for fast re-runs

#### For Hyperparameter Tuning:
- `tuning_from_backtest`: Flag indicating navigation from backtest
- `tuning_message`: Informational message for user
- `tune_*`: All tuning configuration variables (start_date, end_date, etc.)
- `tune_param_space`: Parameter space configuration

#### For Strategy Builder:
- `apply_tuned_params`: Optimized parameters to apply
- `tuned_params_source`: Metadata about optimization (score, method)

### Parameter Pre-population Logic

When navigating from backtest results to tuning:

1. **Date Range**: Copied exactly from current backtest
2. **Capital & Costs**: Preserved from current settings
3. **Asset Universe**: Maintained (symbols and safe asset)
4. **Parameter Ranges**: Generated intelligently:
   - Lookback: ±6 months around current value
   - Position count: 1 to max(4, current+1)
   - Threshold: Common values including current

### Data Caching

The Quick Tune feature caches price data in session state to enable:
- Fast parameter iterations (no data re-fetching)
- Reduced API calls
- Improved user experience

Cache is cleared when:
- User starts new backtest with different symbols
- User navigates away from results
- Session expires

## User Experience Enhancements

### 1. Visual Feedback
- **Success messages** when parameters are applied
- **Info banners** showing optimization results
- **Color-coded buttons** (primary for main actions)
- **Parameter change tables** showing before/after

### 2. Smart Defaults
- Optimization method: Random Search (good balance)
- Number of trials: 50 (reasonable for most cases)
- Metric: Sharpe Ratio (industry standard)
- Parameter ranges: Centered on current values

### 3. Safety Features
- **Validation**: Parameters are validated before re-running
- **Error handling**: Clear error messages with details
- **State preservation**: Original results remain accessible
- **Comparison**: Easy to compare old vs. new results

## API Reference

### Helper Functions

#### `_prepare_tuning_from_backtest()`
Extracts configuration from current backtest and populates tuning session state.

**Called when**: User clicks "🎯 Tune Parameters" button

**Sets**:
- Date range and capital settings
- Asset universe and safe asset
- Default optimization configuration
- Smart parameter ranges

#### `_generate_lookback_values(current_value: int) -> list`
Generates sensible lookback period values around the current value.

**Args**:
- `current_value`: Current lookback period in days

**Returns**:
- List of 4-6 lookback values to test

**Logic**:
- Uses common periods (21, 63, 126, 252, etc.)
- Includes values within ±6 months of current
- Ensures minimum of 4 values

#### `_apply_tuned_parameters(params: Dict[str, Any])`
Applies optimized parameters to strategy builder session state.

**Args**:
- `params`: Dictionary of parameter names and values

**Updates**:
- `lookback_period`
- `position_count`
- `absolute_threshold`
- `use_volatility`
- `rebalance_freq`

#### `_rerun_with_new_params(base_params: dict, new_strategy_params: dict)`
Re-runs backtest with adjusted parameters in Quick Tune.

**Args**:
- `base_params`: Original backtest configuration
- `new_strategy_params`: New strategy parameters

**Process**:
1. Merges new parameters with base config
2. Creates strategy and engine instances
3. Uses cached or fetches fresh price data
4. Runs backtest with benchmark if available
5. Updates session state with new results

## Tips for Users

### For Best Results:
1. **Start with Quick Tune** for small adjustments
2. **Use full optimization** for comprehensive search
3. **Compare strategies** using the comparison feature
4. **Document your findings** by exporting results

### Parameter Tuning Strategies:
1. **Lookback Period**: Try 3-18 months (63-378 days)
2. **Position Count**: Test 1-5 positions depending on universe size
3. **Threshold**: Range from -2% to +5% depending on risk tolerance
4. **Rebalancing**: Monthly is often optimal (balance of cost vs. responsiveness)

### Optimization Tips:
1. **Grid Search**: Use when parameter space is small (<100 combinations)
2. **Random Search**: Good default, works for any size
3. **Bayesian**: Best for large spaces (>100 combinations)
4. **Trials**: 50-100 trials usually sufficient
5. **Metric**: Sharpe for risk-adjusted, Calmar for drawdown focus

## Troubleshooting

### Issue: Quick Tune re-run is slow
**Solution**: Ensure price data is being cached. Check session state for `cached_price_data`.

### Issue: Parameters not applying in Strategy Builder
**Solution**: Verify `apply_tuned_params` is set in session state before navigation.

### Issue: Optimization fails with error
**Solution**: Check that:
- Parameter ranges are valid (min < max)
- Asset symbols are correct
- Date range has sufficient data
- At least 1 parameter is defined

### Issue: Tuning configuration not pre-populated
**Solution**: Ensure a backtest was run recently and `last_backtest_params` exists in session state.

## Advanced Usage

### Custom Parameter Spaces

Users can define custom parameter spaces in the tuning configuration:

```python
# Example: Add custom parameter
st.session_state.tune_param_space.append({
    'name': 'custom_param',
    'type': 'float',
    'values': [0.1, 0.5, 1.0, 2.0]
})
```

### Automated Optimization

For power users, the hyperparameter tuner can be used programmatically:

```python
from src.backtesting import HyperparameterTuner, ParameterSpace

tuner = HyperparameterTuner(
    strategy_class=DualMomentumStrategy,
    backtest_engine=engine,
    price_data=price_data,
    base_config=config
)

param_space = [
    ParameterSpace('lookback_period', 'int', values=[126, 189, 252]),
    ParameterSpace('position_count', 'int', values=[1, 2, 3])
]

results = tuner.random_search(
    param_space=param_space,
    n_trials=100,
    metric='sharpe_ratio'
)
```

## Future Enhancements

Potential improvements for future versions:

1. **Walk-forward optimization**: Split data into train/test periods
2. **Multi-objective optimization**: Optimize multiple metrics simultaneously
3. **Parameter importance analysis**: Show which parameters matter most
4. **Saved optimization templates**: Quick-start with common configurations
5. **A/B testing framework**: Compare multiple parameter sets systematically
6. **Real-time optimization progress**: Show live optimization charts
7. **Parameter sensitivity charts**: Visualize impact of each parameter
8. **Optimization history**: Track all optimization runs for comparison

## Conclusion

The integrated parameter tuning workflow significantly improves the user experience by:

- **Reducing friction** between backtesting and optimization
- **Enabling rapid iteration** with Quick Tune
- **Preserving context** through smart pre-population
- **Providing clear pathways** for applying optimizations

This creates a professional, efficient workflow for strategy development and optimization.
