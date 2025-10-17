# Dual Momentum Backtesting Dashboard

Professional, multi-page Streamlit dashboard for interactive backtesting of momentum trading strategies.

## Features

### 📊 **Strategy Builder**
- Dynamic parameter configuration
- Asset class selector (Equity, Crypto, Commodity, Bond, FX)
- Asset universe builder with predefined templates
- Date range selection
- Capital and trading cost inputs
- Advanced risk management options
- Real-time validation and configuration summary

### 📈 **Backtest Results**
- Comprehensive performance metrics
  - Return metrics (Total, Annualized, CAGR)
  - Risk metrics (Sharpe, Sortino, Calmar, Max Drawdown)
  - Trading statistics (Win rate, number of trades)
- Interactive visualizations
  - Equity curve with annotations
  - Drawdown analysis
  - Monthly returns heatmap
  - Distribution plots
- Detailed trade history with filtering and search
- Rolling performance metrics
- Multiple export formats (CSV, JSON)

### 🔄 **Compare Strategies**
- Side-by-side metrics comparison
- Overlayed equity curves
- Risk vs Return scatter plot
- Correlation matrix analysis
- Efficiency scoring and recommendations

### 🗂️ **Asset Universe Manager**
- Create and edit custom asset universes
- Import/Export functionality (JSON, CSV)
- Quick templates for common universes
- Validation and preview

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the dual momentum framework is installed:
```bash
cd /workspace/dual_momentum_system
pip install -e .
```

## Running the Dashboard

From the `dual_momentum_system` directory:

```bash
streamlit run frontend/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

## Project Structure

```
frontend/
├── app.py                 # Main application entry point
├── pages/                 # Page modules
│   ├── home.py           # Home page with guide
│   ├── strategy_builder.py    # Strategy configuration
│   ├── backtest_results.py    # Results visualization
│   ├── compare_strategies.py  # Strategy comparison
│   └── asset_universe_manager.py  # Universe management
├── utils/                 # Utility modules
│   ├── styling.py        # CSS and styling functions
│   └── state.py          # Session state management
└── requirements.txt       # Dashboard dependencies
```

## Usage Guide

### 1. Configure Strategy

1. Navigate to **Strategy Builder**
2. Select strategy type (Dual Momentum or Absolute Momentum)
3. Choose asset class
4. Select or create an asset universe
5. Adjust strategy parameters:
   - Lookback period
   - Rebalancing frequency
   - Number of positions
   - Absolute momentum threshold
6. Set backtest period and capital
7. Click **Run Backtest**

### 2. View Results

Results automatically appear in **Backtest Results** page:
- Overview tab: Summary metrics and statistics
- Charts tab: Interactive visualizations
- Trades tab: Detailed trade history
- Rolling Metrics tab: Dynamic performance over time
- Export tab: Download results in various formats

### 3. Compare Strategies

1. Run multiple backtests with different configurations
2. Click **Add to Comparison** for each result
3. Navigate to **Compare Strategies**
4. View side-by-side comparisons:
   - Metrics table
   - Overlayed equity curves
   - Risk/return scatter plot
   - Correlation analysis

### 4. Manage Universes

In **Asset Universe Manager**:
- View existing universes
- Create new custom universes
- Edit or delete universes
- Import from JSON/CSV
- Export for backup or sharing
- Use quick templates

## Customization

### Adding Custom Styling

Modify `frontend/utils/styling.py` to customize colors, fonts, and layout.

### Extending Functionality

- Add new pages by creating files in `frontend/pages/`
- Extend state management in `frontend/utils/state.py`
- Add new asset classes in `src/asset_classes/`
- Create new strategies in `src/strategies/`

## Data Sources

The dashboard currently uses:
- **Sample data generation** for demonstration
- **Yahoo Finance** (via framework) for equity data
- Custom data can be integrated through data source plugins

## Performance Considerations

- Results are cached in session state
- Large universes (>20 assets) may take 30-60 seconds
- Longer periods (>5 years) increase computation time
- Use "Run Backtest" button only once per configuration

## Troubleshooting

### Dashboard won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

### Backtest fails
- Verify symbols are valid for selected asset class
- Check date range has sufficient history
- Ensure universe has at least one asset

### Charts not displaying
- Update Plotly: `pip install --upgrade plotly`
- Clear browser cache
- Try a different browser

## Support

For issues or questions:
- Check the framework documentation
- Review example configurations
- Open an issue on GitHub

## License

Part of the Dual Momentum Framework
© 2025
