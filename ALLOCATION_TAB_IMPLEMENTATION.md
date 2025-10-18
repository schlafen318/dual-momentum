# Allocation Tab Implementation

## Overview

Added a comprehensive **Allocation** tab to the Backtest Results page that visualizes how the strategy allocates capital across different assets throughout the backtesting period.

## Features

### 1. Stacked Area Chart - Allocation Over Time
- **Visual representation** of portfolio allocation as percentages (0-100%)
- **Stacked area chart** showing how capital is distributed across assets and cash over time
- **Interactive tooltips** displaying exact allocation percentages at any point
- **Color-coded assets** with a legend for easy identification
- **Cash allocation** shown at the bottom of the stack (in gray)

### 2. Allocation Statistics
Two side-by-side tables providing key metrics:

#### Average Allocation per Asset
- Shows the mean allocation percentage for each asset across the entire backtest period
- Sorted from highest to lowest average allocation
- Helps identify which assets received the most consistent allocation

#### Allocation Range per Asset
- Displays minimum and maximum allocation percentages for each asset
- Useful for understanding allocation volatility and strategy behavior
- Shows the range of portfolio weights assigned to each position

### 3. Rebalancing Events Table
- **Interactive table** showing allocation at each rebalancing event
- Detects rebalancing by identifying significant changes in allocation (>1% threshold)
- Includes first and last dates of the backtest
- **Formatted percentages** for easy reading
- **Downloadable CSV** for further analysis

### 4. Allocation Heatmap
- **Color-coded visualization** showing allocation intensity over time
- **Y-axis**: Assets
- **X-axis**: Time (sampled to 50 points for performance)
- **Color scale**: Viridis colormap (dark = low allocation, bright = high allocation)
- Provides a quick visual overview of allocation patterns and changes

## Technical Implementation

### Files Modified
- `dual_momentum_system/frontend/pages/backtest_results.py`

### Changes Made

#### 1. Tab Structure Update
Added a 6th tab to the existing 5-tab structure:
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Overview",
    "💹 Charts",
    "📋 Trades",
    "📊 Rolling Metrics",
    "🎯 Allocation",  # NEW
    "💾 Export"
])
```

#### 2. New Functions Added

##### `render_allocation(results)`
Main rendering function that:
- Validates availability of position data
- Calls helper functions to calculate allocation
- Creates all visualizations (stacked area chart, statistics, tables, heatmap)
- Handles error cases gracefully with informative messages

##### `_calculate_allocation_over_time(results)`
Core calculation function that:
- Extracts position data from BacktestResult object
- Works with both vectorbt positions (from VectorizedBacktestEngine) and standard positions
- Handles different column naming conventions (vectorbt uses capitalized names)
- Calculates percentage allocation for each asset at each timestamp
- Returns DataFrame with Date column and one column per asset plus Cash

##### `_calculate_allocation_from_trades(results)`
Fallback calculation method that:
- Used when position data is unavailable or incomplete
- Reconstructs allocation from trade entry/exit timestamps
- Provides approximate allocation based on trade activity
- Less accurate but ensures functionality even with limited data

##### `_get_rebalancing_allocation(results, allocation_df)`
Helper function that:
- Identifies rebalancing events by detecting allocation changes >1%
- Extracts allocation snapshots at each rebalancing point
- Returns focused view of allocation at key decision points
- Useful for strategy analysis and verification

### 3. Dependencies
Added `numpy` import for array operations:
```python
import numpy as np
```

## Data Flow

1. **BacktestResult Object** → Contains positions, equity_curve, and trades
2. **Position Data Extraction** → Identifies active positions at each timestamp
3. **Allocation Calculation** → Converts position sizes to percentages of portfolio value
4. **Visualization** → Renders charts and tables using Plotly and Streamlit

## Compatibility

### VectorizedBacktestEngine
- Fully compatible with vectorbt's `positions.records_readable` format
- Handles vectorbt's capitalized column names (e.g., "Column", "Entry Index", "Exit Index")
- Maps vectorbt columns to standard naming convention

### Standard BacktestEngine
- Falls back to trade-based allocation calculation
- Works with limited position history
- Provides approximate allocation when detailed position data unavailable

## Usage

1. **Run a backtest** using either the Strategy Builder page or programmatically
2. **Navigate** to Backtest Results → Allocation tab
3. **View visualizations**:
   - Scroll down to see all charts and tables
   - Hover over charts for detailed information
   - Download allocation history as CSV for external analysis

## Error Handling

The implementation includes comprehensive error handling:
- **No position data**: Shows informative message explaining requirement
- **Calculation errors**: Falls back to alternative methods
- **Empty data**: Gracefully handles edge cases
- **Missing columns**: Adapts to different data formats

## Performance Considerations

- **Heatmap sampling**: Limits to 50 time points to maintain responsiveness
- **Efficient calculations**: Uses vectorized operations where possible
- **Lazy evaluation**: Only calculates data when tab is opened

## Future Enhancements

Potential improvements for future iterations:
1. **Sector allocation view** (if asset metadata includes sector information)
2. **Allocation drift tracking** (deviation from target allocations)
3. **Turnover analysis** (frequency and magnitude of allocation changes)
4. **Comparison mode** (compare allocations across multiple strategies)
5. **Export to Excel** with formatted worksheets
6. **Real-time allocation monitoring** for live trading

## Example Output

### Typical Allocation Pattern (Momentum Strategy)
- **Early period**: High cash allocation during warm-up
- **Active period**: 2-3 assets with significant allocations (33-50% each)
- **Rebalancing**: Clear shifts when momentum signals change
- **Cash buffer**: Typically 10-20% maintained for rebalancing

## Testing

To test the allocation tab:

```python
# Run a backtest example
cd /workspace/dual_momentum_system
python examples/vectorized_backtest_demo.py

# Or use the dashboard
streamlit run frontend/app.py
```

Then navigate to: **Strategy Builder** → Run Backtest → **Backtest Results** → **Allocation** tab

## Notes

- The allocation calculation assumes long-only strategies by default
- For short positions, the allocation would be shown as negative (not yet implemented)
- Cash allocation is calculated as the residual (100% - sum of asset allocations)
- Rebalancing detection uses a 1% threshold, which can be adjusted in `_get_rebalancing_allocation()`
