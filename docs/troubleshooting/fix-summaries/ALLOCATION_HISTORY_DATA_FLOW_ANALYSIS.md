# Allocation History Data Flow Analysis

## Executive Summary

This document provides a comprehensive analysis of how allocation history data is **generated**, **stored**, and **displayed** in the Dual Momentum System. The allocation tracking system captures portfolio composition at every timestep during backtesting and presents it through an interactive visualization dashboard.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Data Generation Phase](#data-generation-phase)
3. [Data Storage Phase](#data-storage-phase)
4. [Data Display Phase](#data-display-phase)
5. [Key Components](#key-components)
6. [Data Flow Diagram](#data-flow-diagram)
7. [Implementation Details](#implementation-details)
8. [Error Handling and Edge Cases](#error-handling-and-edge-cases)

---

## System Architecture Overview

The allocation history system consists of three main layers:

```
┌─────────────────────────────────────────────────────────┐
│                  BACKTESTING ENGINES                     │
│  (BacktestEngine / VectorizedBacktestEngine)            │
│                                                          │
│  → Generate position snapshots at every timestep        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│               BACKTEST RESULT OBJECT                     │
│              (BacktestResult dataclass)                  │
│                                                          │
│  → Store positions DataFrame with allocation data       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND DASHBOARD                       │
│         (backtest_results.py - Streamlit UI)            │
│                                                          │
│  → Extract, calculate, and visualize allocations        │
└─────────────────────────────────────────────────────────┘
```

---

## Data Generation Phase

### Overview

Allocation history is generated during the backtest execution by **recording position snapshots at every timestep**. This happens in both the standard `BacktestEngine` and the vectorized `VectorizedBacktestEngine`.

### Standard BacktestEngine

**File**: `dual_momentum_system/src/backtesting/engine.py`

#### Key Method: `_record_position_snapshot()`

**Location**: Lines 409-438

**Purpose**: Captures the portfolio state at each timestep during backtesting.

**Implementation**:

```python
def _record_position_snapshot(
    self,
    current_date: datetime,
    portfolio_value: float
) -> None:
    """
    Record a snapshot of current positions for allocation tracking.
    """
    snapshot = {
        'timestamp': current_date,
        'portfolio_value': portfolio_value,
        'cash': self.cash,
    }
    
    # Add position data for each symbol
    for symbol, position in self.positions.items():
        snapshot[f'{symbol}_quantity'] = position.quantity
        snapshot[f'{symbol}_price'] = position.current_price
        snapshot[f'{symbol}_value'] = position.quantity * position.current_price
    
    self.position_history.append(snapshot)
```

**When Called**: 
- During `BacktestEngine.run()` at **line 174**
- Invoked at **every single timestep** in the backtest loop (line 162)
- This ensures complete historical tracking of portfolio composition

**Data Structure**:
Each snapshot is a dictionary containing:
- `timestamp`: Current date/time
- `portfolio_value`: Total portfolio value at this timestep
- `cash`: Available cash balance
- For each active position:
  - `{symbol}_quantity`: Number of shares held
  - `{symbol}_price`: Current market price
  - `{symbol}_value`: Market value (quantity × price)

#### Key Method: `_create_positions_dataframe()`

**Location**: Lines 440-499

**Purpose**: Converts the list of position snapshots into a structured DataFrame with allocation percentages.

**Implementation Flow**:

1. **Convert to DataFrame**: 
   ```python
   positions_df = pd.DataFrame(self.position_history)
   ```

2. **Extract symbols** from column names ending in `_value`

3. **Calculate allocation percentages**:
   ```python
   for symbol in symbols:
       value = row.get(f'{symbol}_value', 0)
       record[f'{symbol}_pct'] = (value / portfolio_value * 100) if portfolio_value > 0 else 0
   
   record['cash_pct'] = (cash / portfolio_value * 100) if portfolio_value > 0 else 0
   ```

4. **Return structured DataFrame** with:
   - Index: `timestamp`
   - Columns:
     - `portfolio_value`, `cash`, `cash_pct`
     - For each symbol: `{symbol}_value`, `{symbol}_quantity`, `{symbol}_price`, `{symbol}_pct`

**Output Example**:

```
timestamp          portfolio_value  cash      cash_pct  AAPL_value  AAPL_pct  GOOGL_value  GOOGL_pct
2023-01-01         100000.00       50000.00   50.0      25000.00    25.0      25000.00     25.0
2023-01-02         101500.00       50000.00   49.3      26000.00    25.6      25500.00     25.1
...
```

### Vectorized BacktestEngine

**File**: `dual_momentum_system/src/backtesting/vectorized_engine.py`

**Location**: Lines 502-503

**Approach**: Uses `vectorbt`'s built-in position tracking:

```python
# Get positions from vectorbt portfolio
positions_df = portfolio.positions.records_readable
```

**Key Difference**: 
- VectorBT automatically tracks positions and provides them in a different format
- Uses capitalized column names: `'Column'`, `'Entry Index'`, `'Exit Index'`, `'Size'`
- Frontend code includes compatibility layer to handle both formats

---

## Data Storage Phase

### Overview

Position data is stored in-memory as part of the `BacktestResult` dataclass. There is **no persistent database** - data lives only during the session.

### BacktestResult Dataclass

**File**: `dual_momentum_system/src/core/types.py`

**Location**: Lines 248-301

**Structure**:

```python
@dataclass
class BacktestResult:
    """Results from a backtest run."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    returns: pd.Series              # Period returns
    positions: pd.DataFrame         # ← Allocation history stored here!
    trades: pd.DataFrame            # Completed trades
    metrics: Dict[str, float]       # Performance metrics
    equity_curve: pd.Series         # Portfolio value over time
    metadata: Dict[str, Any]        # Additional info
```

### Storage Flow in Standard Engine

**File**: `dual_momentum_system/src/backtesting/engine.py`

**Location**: Lines 776-869 (`_generate_results()` method)

**Process**:

1. **Generate positions DataFrame** (line 825):
   ```python
   positions_df = self._create_positions_dataframe()
   ```

2. **Log position data** for debugging (lines 827-848):
   ```python
   logger.info("=" * 60)
   logger.info("POSITION DATA SUMMARY")
   logger.info(f"Position history snapshots recorded: {len(self.position_history)}")
   logger.info(f"Positions DataFrame shape: {positions_df.shape}")
   ```

3. **Create BacktestResult** (lines 851-867):
   ```python
   result = BacktestResult(
       strategy_name=strategy_name,
       # ... other fields ...
       positions=positions_df,  # ← Stored here
       # ...
   )
   ```

4. **Return to caller** - stored in Streamlit session state

### Session State Storage

**File**: `dual_momentum_system/frontend/pages/strategy_builder.py`

The `BacktestResult` object is stored in Streamlit's session state:

```python
st.session_state.backtest_results = results
```

This makes the data available across all frontend pages during the user session.

---

## Data Display Phase

### Overview

The allocation visualization happens in the Streamlit dashboard's "Allocation" tab, which provides multiple interactive views of portfolio composition over time.

### Main Rendering Function

**File**: `dual_momentum_system/frontend/pages/backtest_results.py`

**Function**: `render_allocation(results)`

**Location**: Lines 779-966

### Display Flow

#### 1. Data Validation (Lines 788-806)

**Purpose**: Ensure position data exists and is not empty

**Implementation**:

```python
# Check if positions attribute exists
if not hasattr(results, 'positions'):
    st.warning("⚠️ Position data attribute is missing from backtest results.")
    return

# Check if DataFrame is empty (using proper pandas check)
if isinstance(results.positions, pd.DataFrame):
    if results.positions.empty:
        st.warning("⚠️ Position data DataFrame is empty (no rows).")
        return
```

**Important Fix**: 
- Original code used `len(results.positions) == 0` which was problematic
- Fixed to use `.empty` property for proper pandas DataFrame checking
- See `POSITION_DATA_FIX_SUMMARY.md` for details

#### 2. Allocation Calculation (Lines 808-813)

**Function Called**: `_calculate_allocation_over_time(results)`

**Location**: Lines 1012-1118

**Purpose**: Extract or calculate allocation percentages from position data

**Multi-Engine Compatibility**:

```python
# Check if this is standard engine format (has _pct columns)
pct_columns = [col for col in positions_df.columns if col.endswith('_pct')]

if len(pct_columns) > 0:
    # Standard BacktestEngine - already has percentages
    return _extract_allocation_from_position_history(positions_df)
else:
    # VectorBT or other format - needs calculation
    # ... custom extraction logic ...
```

**Helper Function**: `_extract_allocation_from_position_history()`

**Location**: Lines 968-1009

**Implementation**:

```python
def _extract_allocation_from_position_history(positions_df):
    """Extract allocation data from standard BacktestEngine position history."""
    
    # Extract percentage columns
    pct_columns = [col for col in positions_df.columns 
                   if col.endswith('_pct') and col != 'cash_pct']
    
    # Create allocation DataFrame
    allocation_dict = {'Date': positions_df.index}
    
    # Add cash allocation
    if 'cash_pct' in positions_df.columns:
        allocation_dict['Cash'] = positions_df['cash_pct'].values
    
    # Add each symbol's allocation
    for pct_col in pct_columns:
        symbol = pct_col.replace('_pct', '')
        allocation_dict[symbol] = positions_df[pct_col].values
    
    return pd.DataFrame(allocation_dict)
```

**Output Structure**:

```
Date           Cash    AAPL    GOOGL   MSFT
2023-01-01     50.0    25.0    25.0    0.0
2023-01-02     49.3    25.6    25.1    0.0
...
```

#### 3. Visualization Components

##### A. Stacked Area Chart (Lines 815-869)

**Purpose**: Show allocation percentages over time as a stacked area chart

**Technology**: Plotly with `stackgroup='one'`

**Implementation**:

```python
fig = go.Figure()

# Add cash layer (at bottom)
fig.add_trace(go.Scatter(
    x=allocation_df['Date'],
    y=allocation_df['Cash'],
    mode='lines',
    name='Cash',
    stackgroup='one',
    fillcolor='rgba(200, 200, 200, 0.5)',
    hovertemplate='<b>Cash</b><br>%{y:.1f}%<extra></extra>'
))

# Add asset layers
for symbol in symbols:
    fig.add_trace(go.Scatter(
        x=allocation_df['Date'],
        y=allocation_df[symbol],
        mode='lines',
        name=symbol,
        stackgroup='one',
        hovertemplate=f'<b>{symbol}</b><br>%{{y:.1f}}%<extra></extra>'
    ))

fig.update_layout(
    title="Portfolio Allocation by Asset",
    yaxis=dict(range=[0, 100])  # Always 0-100%
)
```

**Features**:
- Interactive hover tooltips showing exact percentages
- Color-coded assets with legend
- Always sums to 100% (portfolio is fully allocated)

##### B. Allocation Statistics (Lines 873-900)

**Purpose**: Display summary statistics in two tables

**Left Table - Average Allocation**:
```python
avg_allocation = allocation_df[symbols].mean().sort_values(ascending=False)
```

**Right Table - Allocation Range**:
```python
for symbol in symbols:
    min_val = allocation_df[symbol].min()
    max_val = allocation_df[symbol].max()
```

##### C. Rebalancing Events Table (Lines 903-928)

**Purpose**: Show allocation at key rebalancing points

**Function**: `_get_rebalancing_allocation(results, allocation_df)`

**Location**: Lines 1180-1225

**Logic**:

```python
def _get_rebalancing_allocation(results, allocation_df):
    """Extract allocation data at rebalancing events."""
    
    rebalance_dates = []
    threshold = 1.0  # 1% change threshold
    
    # Detect significant allocation changes
    for i in range(1, len(allocation_df)):
        symbols = [col for col in allocation_df.columns if col not in ['Date', 'Cash']]
        max_change = 0
        
        for symbol in symbols:
            change = abs(allocation_df[symbol].iloc[i] - allocation_df[symbol].iloc[i-1])
            max_change = max(max_change, change)
        
        if max_change > threshold:
            rebalance_dates.append(i)
    
    # Include first and last dates
    if 0 not in rebalance_dates:
        rebalance_dates.insert(0, 0)
    if len(allocation_df) - 1 not in rebalance_dates:
        rebalance_dates.append(len(allocation_df) - 1)
    
    return allocation_df.iloc[rebalance_dates]
```

**Features**:
- Detects rebalancing when any allocation changes by >1%
- Includes start and end dates
- Downloadable as CSV

##### D. Allocation Heatmap (Lines 932-963)

**Purpose**: Visualize allocation intensity over time

**Technology**: Plotly heatmap with Viridis colorscale

**Sampling Strategy**:
```python
# Sample to 50 points for performance
sample_size = min(50, len(allocation_df))
sample_indices = np.linspace(0, len(allocation_df) - 1, sample_size, dtype=int)
sampled_df = allocation_df.iloc[sample_indices]
```

**Implementation**:

```python
fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,  # Assets × Time
    x=dates_formatted,       # X-axis: dates
    y=symbols,               # Y-axis: asset symbols
    colorscale='Viridis',
    hovertemplate='Asset: %{y}<br>Date: %{x}<br>Allocation: %{z:.1f}%<extra></extra>',
    colorbar=dict(title="Allocation (%)")
))
```

**Features**:
- Color intensity represents allocation percentage
- Sampled to maintain performance with large datasets
- Interactive hover showing exact values

---

## Key Components

### 1. BacktestEngine

**Responsibility**: Generate position snapshots during backtesting

**Key Attributes**:
- `self.position_history: List[Dict[str, Any]]` - Stores snapshots
- `self.positions: Dict[str, Position]` - Current positions
- `self.cash: float` - Current cash balance

**Key Methods**:
- `run()` - Main backtest loop
- `_record_position_snapshot()` - Capture state at each timestep
- `_create_positions_dataframe()` - Convert to structured DataFrame
- `_generate_results()` - Package into BacktestResult

### 2. VectorizedBacktestEngine

**Responsibility**: High-performance backtesting using vectorbt

**Key Difference**: 
- Leverages vectorbt's native position tracking
- Returns positions in vectorbt format with capitalized columns
- Frontend includes compatibility layer for both formats

**Key Methods**:
- `run_backtest()` - Execute vectorized backtest
- `_extract_results()` - Convert vectorbt portfolio to BacktestResult

### 3. BacktestResult

**Responsibility**: Immutable container for backtest results

**Key Attributes**:
- `positions: pd.DataFrame` - Complete allocation history
- `equity_curve: pd.Series` - Portfolio value over time
- `trades: pd.DataFrame` - Trade history
- `metrics: Dict[str, float]` - Performance statistics

### 4. Frontend Allocation Tab

**Responsibility**: Extract, calculate, and visualize allocation data

**File**: `dual_momentum_system/frontend/pages/backtest_results.py`

**Key Functions**:
- `render_allocation()` - Main rendering function
- `_calculate_allocation_over_time()` - Extract/calculate allocations
- `_extract_allocation_from_position_history()` - Parse standard format
- `_calculate_allocation_from_trades()` - Fallback for limited data
- `_get_rebalancing_allocation()` - Detect rebalancing events

---

## Data Flow Diagram

```
BACKTEST EXECUTION
==================

1. BacktestEngine.run() starts
   ↓
2. For each timestep in date_index:
   │
   ├─→ Update position prices
   │   (_update_positions)
   │
   ├─→ Calculate portfolio value
   │   (_calculate_portfolio_value)
   │
   ├─→ 📸 RECORD POSITION SNAPSHOT  ← KEY STEP
   │   (_record_position_snapshot)
   │   │
   │   └─→ Append to position_history list:
   │       {
   │         'timestamp': current_date,
   │         'portfolio_value': value,
   │         'cash': cash_balance,
   │         'AAPL_quantity': qty,
   │         'AAPL_price': price,
   │         'AAPL_value': qty * price,
   │         ... (for each position)
   │       }
   │
   └─→ Check if should rebalance
       ├─→ Generate signals
       └─→ Execute trades

3. Backtest complete
   ↓
4. Convert position_history to DataFrame
   (_create_positions_dataframe)
   │
   └─→ Add percentage columns:
       - {symbol}_pct = value / portfolio_value * 100
       - cash_pct = cash / portfolio_value * 100
   ↓
5. Create BacktestResult object
   - positions = positions_df
   ↓
6. Store in session state
   st.session_state.backtest_results = result


DISPLAY PHASE
=============

1. User navigates to Allocation tab
   ↓
2. render_allocation(results) called
   ↓
3. Validate position data exists
   ├─→ Check hasattr(results, 'positions')
   └─→ Check not positions.empty
   ↓
4. Calculate allocation over time
   (_calculate_allocation_over_time)
   │
   ├─→ Detect format (standard vs vectorbt)
   │
   ├─→ If standard format (has _pct columns):
   │   └─→ _extract_allocation_from_position_history()
   │       - Extract {symbol}_pct columns
   │       - Create clean allocation DataFrame
   │
   └─→ If vectorbt format:
       └─→ Parse positions.records_readable
           - Map Column → symbol
           - Calculate allocations from position sizes
   ↓
5. Render visualizations:
   │
   ├─→ Stacked Area Chart (Plotly)
   │   - Shows allocation % over time
   │   - Interactive hover tooltips
   │
   ├─→ Statistics Tables
   │   - Average allocation per asset
   │   - Min/Max range per asset
   │
   ├─→ Rebalancing Events Table
   │   (_get_rebalancing_allocation)
   │   - Detect allocation changes >1%
   │   - Show allocation at key dates
   │   - Downloadable CSV
   │
   └─→ Allocation Heatmap
       - Color-coded allocation intensity
       - Sampled to 50 points for performance
```

---

## Implementation Details

### Frequency of Snapshot Recording

**Every timestep** during backtesting:
```python
# In BacktestEngine.run(), line 162-174:
for i, current_date in enumerate(date_index):
    # ... update positions ...
    
    # Record snapshot EVERY iteration
    self._record_position_snapshot(current_date, portfolio_value)
```

**Why every timestep?**
- Captures complete allocation history
- Allows accurate visualization of portfolio drift
- Enables precise rebalancing detection
- Required for accurate statistics (avg, min, max)

### Memory Considerations

**Storage Per Snapshot**:
- Base: 3 fields (timestamp, portfolio_value, cash)
- Per position: 3 fields (quantity, price, value)
- Example with 5 assets: 3 + (5 × 3) = 18 values per snapshot

**Typical Backtest**:
- 252 trading days/year × 5 years = 1,260 snapshots
- 5 assets: 1,260 × 18 = 22,680 values (~180 KB)
- Very manageable for in-memory storage

### DataFrame Structure Evolution

**Raw Snapshot** (in position_history list):
```python
{
    'timestamp': Timestamp('2023-01-01'),
    'portfolio_value': 100000.0,
    'cash': 50000.0,
    'AAPL_quantity': 100,
    'AAPL_price': 150.0,
    'AAPL_value': 15000.0,
    'GOOGL_quantity': 50,
    'GOOGL_price': 700.0,
    'GOOGL_value': 35000.0
}
```

**Positions DataFrame** (after _create_positions_dataframe):
```
                    portfolio_value  cash    cash_pct  AAPL_value  AAPL_quantity  AAPL_price  AAPL_pct  GOOGL_value  GOOGL_quantity  GOOGL_price  GOOGL_pct
timestamp                                                                                                                                                         
2023-01-01         100000.0         50000.0  50.0      15000.0     100            150.0       15.0      35000.0      50              700.0        35.0
```

**Allocation DataFrame** (for display):
```
Date           Cash    AAPL    GOOGL
2023-01-01     50.0    15.0    35.0
2023-01-02     48.5    16.2    35.3
```

### Multi-Engine Compatibility

The frontend handles both engine types through format detection:

```python
# Detect format by checking for _pct columns
pct_columns = [col for col in positions_df.columns if col.endswith('_pct')]

if len(pct_columns) > 0:
    # Standard BacktestEngine format
    allocation_df = _extract_allocation_from_position_history(positions_df)
else:
    # VectorBT or other format
    # Map column names and calculate allocations
    col_mapping = {
        'Column': 'symbol',
        'Entry Index': 'entry_idx',
        'Exit Index': 'exit_idx',
        'Size': 'quantity'
    }
    # ... custom calculation logic ...
```

---

## Error Handling and Edge Cases

### 1. Empty Position Data

**Problem**: Position data might be missing or empty

**Solution**: Multi-level validation

```python
# Check 1: Attribute exists
if not hasattr(results, 'positions'):
    st.warning("⚠️ Position data attribute is missing")
    return

# Check 2: DataFrame not empty (proper pandas check)
if isinstance(results.positions, pd.DataFrame):
    if results.positions.empty:
        st.warning("⚠️ Position data DataFrame is empty")
        st.markdown("""
        This may occur if:
        - The backtest period was too short
        - No trading signals were generated
        - All trades were rejected due to insufficient capital
        """)
        return
```

**Historical Bug**: 
- Original code used `len(positions) == 0` 
- This fails for DataFrames (always returns False even when empty)
- Fixed to use `.empty` property
- See `POSITION_DATA_FIX_SUMMARY.md`

### 2. Insufficient Data for Visualization

**Problem**: Allocation calculation might fail

**Solution**: Fallback mechanisms

```python
allocation_df = _calculate_allocation_over_time(results)

if allocation_df is None or len(allocation_df) == 0:
    st.info("Unable to calculate allocation data from available position history.")
    return
```

### 3. All Cash Portfolio (No Positions)

**Scenario**: Strategy holds 100% cash (no active positions)

**Handling**: 
- Valid scenario, not an error
- Displays 100% cash allocation
- Still shows allocation chart and statistics

```python
# Cash is calculated as residual
allocation_dict['Cash'][i] = max(0, 100 - total_allocated)
```

### 4. VectorBT Format Compatibility

**Problem**: VectorBT uses different column names

**Solution**: Column mapping and fallback

```python
# Map VectorBT column names to standard format
col_mapping = {
    'Column': 'symbol',
    'Entry Timestamp': 'entry_timestamp',
    'Exit Timestamp': 'exit_timestamp',
    'Size': 'quantity',
    # ...
}

# Check for required columns
required_cols = set()
for col in positions_df.columns:
    col_lower = col.lower()
    if 'column' in col_lower or 'symbol' in col_lower:
        col_mapping['symbol'] = col
        required_cols.add('symbol')
```

### 5. Rebalancing Detection Edge Cases

**Challenge**: Detecting meaningful rebalancing events vs noise

**Solution**: Threshold-based detection

```python
threshold = 1.0  # 1% change threshold

for i in range(1, len(allocation_df)):
    max_change = 0
    for symbol in symbols:
        change = abs(allocation_df[symbol].iloc[i] - allocation_df[symbol].iloc[i-1])
        max_change = max(max_change, change)
    
    if max_change > threshold:
        rebalance_dates.append(i)
```

**Tunable Parameter**: 
- Default: 1% threshold
- Can be adjusted in `_get_rebalancing_allocation()`
- Higher threshold = fewer detected rebalances
- Lower threshold = more sensitive detection

### 6. Performance with Large Datasets

**Challenge**: Heatmap can be slow with many timesteps

**Solution**: Intelligent sampling

```python
# Sample to 50 points for performance
sample_size = min(50, len(allocation_df))
sample_indices = np.linspace(0, len(allocation_df) - 1, sample_size, dtype=int)
sampled_df = allocation_df.iloc[sample_indices]
```

**Trade-off**:
- Maintains interactivity
- Preserves overall pattern
- Loses some granular detail
- User can download full CSV for complete data

### 7. Trade-Based Fallback

**Scenario**: Position data unavailable but trades exist

**Solution**: `_calculate_allocation_from_trades()`

**Location**: Lines 1121-1177

**Approach**:
```python
# Track positions based on entry/exit timestamps
for _, trade in trades_df.iterrows():
    entry_time = trade['entry_timestamp']
    exit_time = trade['exit_timestamp']
    
    # Find active date range
    active_mask = (dates >= entry_time) & (dates < exit_time)
    
    # Assign equal weight (approximation)
    for i in np.where(active_mask)[0]:
        allocation_dict[symbol][i] = 100.0 / len(symbols)
```

**Limitations**:
- Less accurate than position snapshots
- Assumes equal weighting
- No cash allocation tracking
- Used only as last resort

---

## Summary

### Key Takeaways

1. **Generation**: 
   - Position snapshots recorded at **every timestep** during backtesting
   - Captures complete portfolio state (cash + all positions)
   - Stored in `position_history` list

2. **Storage**:
   - Converted to structured DataFrame with allocation percentages
   - Stored in `BacktestResult.positions` attribute
   - Held in Streamlit session state (no persistent database)
   - Efficient memory usage (~180 KB for typical 5-year backtest)

3. **Display**:
   - Interactive Streamlit dashboard with multiple views
   - Stacked area chart, statistics tables, rebalancing events, heatmap
   - Compatible with both standard and vectorized engines
   - Download capability for further analysis

### Data Flow Summary

```
Backtest Loop → position_history (list of dicts)
                ↓
Convert & Calculate → positions_df (structured DataFrame with _pct columns)
                     ↓
Store in Result → BacktestResult.positions
                  ↓
Session State → st.session_state.backtest_results
                ↓
Extract & Render → allocation_df (clean Date + symbol columns)
                   ↓
Visualizations → Charts, tables, heatmap, CSV export
```

### File Locations Reference

| Component | File | Key Lines |
|-----------|------|-----------|
| Snapshot Recording | `src/backtesting/engine.py` | 409-438 |
| DataFrame Creation | `src/backtesting/engine.py` | 440-499 |
| Result Generation | `src/backtesting/engine.py` | 776-869 |
| VectorBT Extraction | `src/backtesting/vectorized_engine.py` | 432-526 |
| BacktestResult Type | `src/core/types.py` | 248-301 |
| Allocation Tab | `frontend/pages/backtest_results.py` | 779-966 |
| Allocation Calculation | `frontend/pages/backtest_results.py` | 1012-1118 |
| Rebalancing Detection | `frontend/pages/backtest_results.py` | 1180-1225 |

---

## Related Documentation

- `ALLOCATION_TAB_IMPLEMENTATION.md` - Feature overview and usage
- `POSITION_DATA_FIX_SUMMARY.md` - DataFrame empty check bug fix
- `ARCHITECTURE.md` - Overall system architecture

---

**Analysis Complete**: 2025-10-19

This comprehensive analysis covers the complete lifecycle of allocation history data from generation through storage to display, including implementation details, error handling, and edge cases.
