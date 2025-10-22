"""
Home page for the Streamlit dashboard.

Provides overview and quick start guide.
"""

import streamlit as st
from frontend.utils.styling import render_page_header, render_info_box


def render():
    """Render the home page."""
    
    render_page_header(
        "Welcome to Dual Momentum Backtesting Dashboard",
        "Professional platform for momentum strategy development and analysis",
        "🏠"
    )
    
    # Introduction
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🛠️ Strategy Builder</h3>
            <p>Design and configure momentum strategies with dynamic parameter controls for multiple asset classes.</p>
            <ul>
                <li>5 Asset classes supported</li>
                <li>Customizable parameters</li>
                <li>Real-time validation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>📊 Results Analysis</h3>
            <p>Comprehensive performance metrics and interactive visualizations of your backtest results.</p>
            <ul>
                <li>Interactive charts</li>
                <li>Detailed metrics</li>
                <li>Trade analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <h3>🔄 Strategy Comparison</h3>
            <p>Compare multiple strategies side-by-side with overlayed performance metrics.</p>
            <ul>
                <li>Multiple strategies</li>
                <li>Risk/return analysis</li>
                <li>Correlation matrix</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick start guide
    st.markdown("## 🚀 Quick Start Guide")
    
    with st.expander("📖 Step 1: Configure Your Strategy", expanded=True):
        st.markdown("""
        Navigate to the **Strategy Builder** page to:
        1. Select your preferred momentum strategy (Dual Momentum, Absolute Momentum, etc.)
        2. Choose an asset class (Equity, Crypto, Commodity, Bond, or FX)
        3. Define your asset universe or select a predefined one
        4. Adjust strategy parameters (lookback period, rebalancing frequency, etc.)
        5. Set initial capital and trading costs
        """)
    
    with st.expander("📈 Step 2: Run Backtest"):
        st.markdown("""
        After configuring your strategy:
        1. Select the date range for historical testing
        2. Review your configuration summary
        3. Click **Run Backtest** to execute
        4. Results will appear automatically in the **Backtest Results** page
        """)
    
    with st.expander("🔍 Step 3: Analyze Results"):
        st.markdown("""
        The **Backtest Results** page provides:
        - **Summary Metrics**: Total return, Sharpe ratio, max drawdown, win rate
        - **Equity Curve**: Interactive chart showing portfolio value over time
        - **Drawdown Chart**: Visualize periods of losses
        - **Trade Analysis**: Detailed table of all executed trades
        - **Rolling Metrics**: Dynamic performance metrics over time
        - **Export Options**: Download results as CSV or JSON
        """)
    
    with st.expander("🔄 Step 4: Compare Strategies (Optional)"):
        st.markdown("""
        To compare multiple strategies:
        1. Run multiple backtests with different configurations
        2. Add each result to comparison using the **Add to Comparison** button
        3. Navigate to **Compare Strategies** page
        4. View side-by-side metrics, overlayed charts, and correlation analysis
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features overview
    st.markdown("## ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Asset Class Support
        - **Equities**: Stocks, ETFs with split/dividend handling
        - **Cryptocurrencies**: 24/7 trading, fractional shares
        - **Commodities**: Futures contracts with expiration tracking
        - **Bonds**: Fixed income with duration analysis
        - **FX**: Currency pairs with pip calculations
        
        ### Strategy Capabilities
        - Dual Momentum (absolute + relative)
        - Absolute Momentum (trend following)
        - Custom parameter optimization
        - Multiple asset support
        - Flexible rebalancing schedules
        """)
    
    with col2:
        st.markdown("""
        ### Analytics & Reporting
        - Comprehensive performance metrics
        - Interactive Plotly charts
        - Rolling window analysis
        - Monte Carlo simulations (coming soon)
        - Risk-adjusted returns
        
        ### Data Management
        - Asset universe builder
        - Portfolio templates
        - Export/import configurations
        - Historical data caching
        - Real-time validation
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Performance metrics explanation
    st.markdown("## 📚 Understanding Performance Metrics")
    
    with st.expander("📊 Core Metrics Explained"):
        st.markdown("""
        **Total Return**: Cumulative percentage gain/loss over the backtest period
        
        **Annualized Return**: Return normalized to a yearly basis for comparison
        
        **Sharpe Ratio**: Risk-adjusted return metric (return per unit of volatility)
        - > 1.0: Good
        - > 2.0: Very good
        - > 3.0: Excellent
        
        **Max Drawdown**: Largest peak-to-trough decline during the period
        
        **Win Rate**: Percentage of profitable trades
        
        **Sortino Ratio**: Similar to Sharpe but only penalizes downside volatility
        
        **Calmar Ratio**: Annualized return divided by maximum drawdown
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tips and best practices
    render_info_box(
        "💡 **Pro Tip**: Start with a predefined asset universe and default parameters, "
        "then gradually adjust based on your analysis. Use the Compare Strategies feature "
        "to evaluate the impact of parameter changes.",
        "info"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # System requirements
    with st.expander("⚙️ System Requirements & Notes"):
        st.markdown("""
        **Data Requirements:**
        - Historical price data is fetched from Yahoo Finance (for equities)
        - Minimum 1 year of history recommended for meaningful momentum calculations
        - Data quality impacts backtest accuracy
        
        **Performance Considerations:**
        - Larger universes and longer periods increase computation time
        - Results are cached for faster subsequent analysis
        - Complex strategies may take 1-2 minutes to complete
        
        **Known Limitations:**
        - Simulated execution assumes perfect fills at close prices
        - Does not account for market impact on large orders
        - Transaction costs are simplified (fixed commission + slippage)
        - Does not model dividend reinvestment in detail
        """)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Call to action
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="cta-box" style='text-align: center; padding: 2rem; background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%); border-radius: 10px;'>
            <h2 style='color: white !important; margin-bottom: 1rem;'>Ready to Get Started?</h2>
            <p style='color: rgba(255,255,255,0.95) !important; font-size: 1.1rem;'>
                Navigate to the Strategy Builder to create your first backtest!
            </p>
        </div>
        """, unsafe_allow_html=True)
