"""
Strategy Builder page for the Streamlit dashboard.

Allows users to configure and launch backtests with dynamic parameter controls.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from frontend.utils.styling import (
    render_page_header, render_info_box, render_section_divider
)
from frontend.utils.state import add_to_comparison

# Import framework components
from src.strategies import DualMomentumStrategy
from src.strategies.absolute_momentum import AbsoluteMomentumStrategy
from src.asset_classes import (
    EquityAsset, CryptoAsset, CommodityAsset, BondAsset, FXAsset
)
from src.backtesting.engine import BacktestEngine
from src.backtesting.performance import PerformanceCalculator
from src.core.types import PriceData, AssetMetadata
from src.core import get_plugin_manager


def render():
    """Render the strategy builder page."""
    
    render_page_header(
        "Strategy Builder",
        "Configure and launch momentum strategy backtests",
        "🛠️"
    )
    
    # Main configuration area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_strategy_configuration()
    
    with col2:
        render_configuration_summary()
    
    render_section_divider()
    
    # Advanced options
    with st.expander("⚙️ Advanced Options", expanded=False):
        render_advanced_options()
    
    # Run backtest section
    st.markdown("<br>", unsafe_allow_html=True)
    render_backtest_controls()


def render_strategy_configuration():
    """Render the main strategy configuration section."""
    
    st.markdown("### 📋 Strategy Configuration")
    
    # Strategy selection
    strategy_type = st.selectbox(
        "Strategy Type",
        ["Dual Momentum", "Absolute Momentum"],
        help="Dual Momentum combines trend strength with relative ranking. "
             "Absolute Momentum only checks if assets are in an uptrend."
    )
    st.session_state.strategy_type = strategy_type
    
    # Asset class selection
    asset_class = st.selectbox(
        "Asset Class",
        ["Equity", "Crypto", "Commodity", "Bond", "FX"],
        help="Choose the type of assets you want to trade"
    )
    st.session_state.asset_class = asset_class
    
    # Asset universe selection
    st.markdown("#### 🌐 Asset Universe")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        universe_options = list(st.session_state.asset_universes.keys())
        # Filter by asset class
        filtered_universes = [
            u for u in universe_options
            if st.session_state.asset_universes[u]['asset_class'].lower() == asset_class.lower()
        ]
        
        if not filtered_universes:
            filtered_universes = ["Custom"]
        
        selected_universe = st.selectbox(
            "Select Universe",
            filtered_universes + ["Custom"],
            help="Choose a predefined asset universe or create a custom one"
        )
    
    with col2:
        if st.button("📂 Manage", width='stretch'):
            st.info("Navigate to Asset Universe Manager to create/edit universes")
    
    # Asset symbols input
    if selected_universe == "Custom":
        symbols_input = st.text_area(
            "Asset Symbols (one per line or comma-separated)",
            value="",
            height=100,
            help="Enter asset symbols for your universe"
        )
        symbols = [s.strip() for s in symbols_input.replace(',', '\n').split('\n') if s.strip()]
    else:
        universe_data = st.session_state.asset_universes[selected_universe]
        symbols = universe_data['symbols']
        st.multiselect(
            "Assets in Universe",
            symbols,
            default=symbols,
            disabled=True,
            help=universe_data.get('description', '')
        )
    
    st.session_state.selected_symbols = symbols
    
    # Strategy parameters
    render_section_divider()
    st.markdown("#### ⚙️ Strategy Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lookback_period = st.number_input(
            "Lookback Period (days)",
            min_value=20,
            max_value=500,
            value=252,
            step=10,
            help="Number of days to calculate momentum. Default 252 (1 year trading days)"
        )
        st.session_state.lookback_period = lookback_period
    
    with col2:
        rebalance_freq = st.selectbox(
            "Rebalance Frequency",
            ["Daily", "Weekly", "Monthly", "Quarterly"],
            index=2,
            help="How often to recalculate positions and rebalance portfolio"
        )
        st.session_state.rebalance_freq = rebalance_freq.lower()
    
    with col3:
        position_count = st.number_input(
            "Number of Positions",
            min_value=1,
            max_value=len(symbols) if symbols else 10,
            value=min(3, len(symbols) if symbols else 3),
            help="How many top-ranked assets to hold simultaneously"
        )
        st.session_state.position_count = position_count
    
    # Additional parameters
    col1, col2 = st.columns(2)
    
    with col1:
        absolute_threshold = st.slider(
            "Absolute Momentum Threshold",
            min_value=-0.5,
            max_value=0.5,
            value=0.0,
            step=0.01,
            format="%.2f",
            help="Minimum momentum required to enter position. Negative values allow short positions."
        )
        st.session_state.absolute_threshold = absolute_threshold
    
    with col2:
        use_volatility = st.checkbox(
            "Use Volatility Adjustment",
            value=False,
            help="Adjust position sizes based on asset volatility (inverse volatility weighting)"
        )
        st.session_state.use_volatility = use_volatility
    
    # Safe asset for absolute momentum
    if strategy_type == "Dual Momentum":
        safe_asset = st.text_input(
            "Safe Asset Symbol (optional)",
            value="",
            placeholder="Default: None (cash)",
            help="Asset to hold when momentum is negative. Common choices: AGG (aggregate bonds), SHY (short-term bonds), BIL (T-bills). If empty, portfolio holds cash during defensive periods."
        )
        st.session_state.safe_asset = safe_asset if safe_asset else None
        
        # Display default information
        if not safe_asset:
            st.caption("💡 Default: **Cash** (no safe asset ticker) - Recommended: **AGG** for bond allocation during downturns")
    
    # Benchmark selection
    render_section_divider()
    st.markdown("#### 📊 Benchmark Comparison")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        benchmark_symbol = st.text_input(
            "Benchmark Symbol (optional)",
            value="SPY",
            help="Benchmark for performance comparison (e.g., 'SPY' for S&P 500, 'BTC-USD' for Bitcoin)"
        )
        st.session_state.benchmark_symbol = benchmark_symbol if benchmark_symbol else None
    
    with col2:
        if benchmark_symbol:
            st.info(f"Will compare against {benchmark_symbol}")
    
    # Date range selection
    render_section_divider()
    st.markdown("#### 📅 Backtest Period")
    
    col1, col2 = st.columns(2)
    
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365*3)  # 3 years
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            max_value=default_end,
            help="Beginning of backtest period"
        )
        st.session_state.start_date = start_date
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=default_end,
            min_value=start_date,
            help="End of backtest period"
        )
        st.session_state.end_date = end_date
    
    # Calculate duration
    duration_days = (end_date - start_date).days
    duration_years = duration_days / 365.25
    st.caption(f"📊 Backtest duration: {duration_days} days ({duration_years:.1f} years)")
    
    # Capital and costs
    render_section_divider()
    st.markdown("#### 💰 Capital & Trading Costs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=10000.0,
            format="%.0f",
            help="Starting portfolio value"
        )
        st.session_state.initial_capital = initial_capital
    
    with col2:
        commission = st.number_input(
            "Commission (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.2f",
            help="Commission as percentage of trade value"
        ) / 100
        st.session_state.commission = commission
    
    with col3:
        slippage = st.number_input(
            "Slippage (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.05,
            step=0.01,
            format="%.2f",
            help="Expected slippage as percentage of trade value"
        ) / 100
        st.session_state.slippage = slippage


def render_configuration_summary():
    """Render configuration summary panel."""
    
    st.markdown("### 📝 Configuration Summary")
    
    st.markdown(f"""
    <div class="card">
        <h4>Strategy Details</h4>
        <ul style="list-style: none; padding-left: 0;">
            <li>📊 <strong>Type:</strong> {st.session_state.get('strategy_type', 'Not set')}</li>
            <li>🏷️ <strong>Asset Class:</strong> {st.session_state.get('asset_class', 'Not set')}</li>
            <li>🌐 <strong>Universe Size:</strong> {len(st.session_state.get('selected_symbols', []))} assets</li>
            <li>📈 <strong>Positions:</strong> {st.session_state.get('position_count', 0)}</li>
            <li>🔄 <strong>Rebalance:</strong> {st.session_state.get('rebalance_freq', 'Not set').title()}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    benchmark = st.session_state.get('benchmark_symbol')
    safe_asset = st.session_state.get('safe_asset')
    safe_asset_display = safe_asset if safe_asset else 'Cash'
    st.markdown(f"""
    <div class="card">
        <h4>Parameters</h4>
        <ul style="list-style: none; padding-left: 0;">
            <li>📏 <strong>Lookback:</strong> {st.session_state.get('lookback_period', 0)} days</li>
            <li>🎯 <strong>Threshold:</strong> {st.session_state.get('absolute_threshold', 0):.2f}</li>
            <li>📊 <strong>Vol. Adj.:</strong> {'Yes' if st.session_state.get('use_volatility', False) else 'No'}</li>
            <li>🛡️ <strong>Safe Asset:</strong> {safe_asset_display}</li>
            <li>📈 <strong>Benchmark:</strong> {benchmark if benchmark else 'None'}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="card">
        <h4>Backtest Setup</h4>
        <ul style="list-style: none; padding-left: 0;">
            <li>💰 <strong>Capital:</strong> ${st.session_state.get('initial_capital', 0):,.0f}</li>
            <li>💵 <strong>Commission:</strong> {st.session_state.get('commission', 0)*100:.2f}%</li>
            <li>📉 <strong>Slippage:</strong> {st.session_state.get('slippage', 0)*100:.2f}%</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Validation warnings
    symbols = st.session_state.get('selected_symbols', [])
    if len(symbols) == 0:
        render_info_box("⚠️ No assets selected. Please add symbols to your universe.", "warning")
    elif len(symbols) < st.session_state.get('position_count', 1):
        render_info_box(
            f"⚠️ Position count ({st.session_state.get('position_count')}) exceeds "
            f"universe size ({len(symbols)}). It will be reduced automatically.",
            "warning"
        )


def render_advanced_options():
    """Render advanced configuration options."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Risk Management")
        
        max_position_size = st.slider(
            "Max Position Size (%)",
            min_value=10,
            max_value=100,
            value=100,
            step=5,
            help="Maximum percentage of portfolio in single position"
        )
        st.session_state.max_position_size = max_position_size / 100
        
        stop_loss = st.number_input(
            "Stop Loss (%)",
            min_value=0.0,
            max_value=50.0,
            value=0.0,
            step=1.0,
            help="Exit position if it loses this percentage (0 = disabled)"
        )
        st.session_state.stop_loss = stop_loss / 100 if stop_loss > 0 else None
    
    with col2:
        st.markdown("#### Data & Execution")
        
        use_adjusted = st.checkbox(
            "Use Adjusted Prices",
            value=True,
            help="Use dividend and split-adjusted prices (recommended)"
        )
        st.session_state.use_adjusted = use_adjusted
        
        execution_delay = st.number_input(
            "Execution Delay (days)",
            min_value=0,
            max_value=5,
            value=1,
            help="Days between signal and execution (models real-world delay)"
        )
        st.session_state.execution_delay = execution_delay


def render_backtest_controls():
    """Render backtest execution controls."""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 🚀 Ready to Run Backtest?")
        st.caption("Review your configuration above, then click the button to start.")
    
    with col2:
        if st.button("▶️ Run Backtest", type="primary", width='stretch'):
            run_backtest()
    
    with col3:
        if st.button("💾 Save Config", width='stretch'):
            save_configuration()


def run_backtest():
    """Execute the backtest with current configuration."""
    
    # Validation
    symbols = st.session_state.get('selected_symbols', [])
    if len(symbols) == 0:
        st.error("❌ Please select at least one asset symbol")
        return
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    warnings_container = st.container()
    warnings = []
    
    try:
        status_text.text("🔄 Initializing data source...")
        progress_bar.progress(10)
        
        # Initialize multi-source data provider with automatic failover
        from src.data_sources import get_default_data_source
        import os
        
        # Get API keys from environment or Streamlit secrets if available
        api_config = {}
        
        # Try to get from Streamlit secrets (safe handling)
        try:
            if hasattr(st, 'secrets') and st.secrets:
                if 'ALPHAVANTAGE_API_KEY' in st.secrets:
                    api_config['alphavantage_api_key'] = st.secrets['ALPHAVANTAGE_API_KEY']
                if 'TWELVEDATA_API_KEY' in st.secrets:
                    api_config['twelvedata_api_key'] = st.secrets['TWELVEDATA_API_KEY']
        except (FileNotFoundError, RuntimeError):
            # Secrets file not found or empty - this is fine, we'll use env vars or just Yahoo
            pass
        
        # Also check environment variables (these take precedence)
        if 'ALPHAVANTAGE_API_KEY' in os.environ:
            api_config['alphavantage_api_key'] = os.environ['ALPHAVANTAGE_API_KEY']
        if 'TWELVEDATA_API_KEY' in os.environ:
            api_config['twelvedata_api_key'] = os.environ['TWELVEDATA_API_KEY']
        
        # Create multi-source provider (Yahoo + optional alternatives)
        data_source = get_default_data_source(api_config)
        
        # Get asset class
        asset_class_str = st.session_state.get('asset_class', 'equity').lower()
        asset_class_map = {
            'equity': EquityAsset,
            'crypto': CryptoAsset,
            'commodity': CommodityAsset,
            'bond': BondAsset,
            'fx': FXAsset
        }
        AssetClass = asset_class_map.get(asset_class_str, EquityAsset)
        asset_instance = AssetClass()
        
        # Fetch REAL data for all symbols
        status_text.text("📊 Fetching real market data...")
        progress_bar.progress(20)
        
        price_data_dict = fetch_real_data(
            symbols,
            st.session_state.start_date,
            st.session_state.end_date,
            data_source,
            asset_instance,
            status_text
        )
        
        if not price_data_dict:
            st.error("❌ Failed to fetch data for any symbols. Please check symbols and try again.")
            return
        
        progress_bar.progress(40)
        
        # Fetch benchmark data if specified
        benchmark_symbol = st.session_state.get('benchmark_symbol')
        benchmark_data = None
        if benchmark_symbol:
            status_text.text(f"📊 Fetching benchmark data ({benchmark_symbol})...")
            benchmark_dict = fetch_real_data(
                [benchmark_symbol],
                st.session_state.start_date,
                st.session_state.end_date,
                data_source,
                asset_instance,
                status_text
            )
            if benchmark_dict:
                benchmark_data = benchmark_dict[benchmark_symbol]
            else:
                warnings.append(f"⚠️ Could not fetch benchmark data for {benchmark_symbol}")
        
        progress_bar.progress(50)
        
        # Initialize strategy configuration
        status_text.text("⚙️ Configuring strategy...")
        
        strategy_config = {
            'lookback_period': st.session_state.get('lookback_period', 252),
            'rebalance_frequency': st.session_state.get('rebalance_freq', 'monthly'),
            'position_count': min(
                st.session_state.get('position_count', 1),
                len(price_data_dict)
            ),
            'absolute_threshold': st.session_state.get('absolute_threshold', 0.0),
            'use_volatility_adjustment': st.session_state.get('use_volatility', False),
        }
        
        # Handle safe asset - try to fetch real data, fallback to cash
        safe_asset = st.session_state.get('safe_asset')
        if safe_asset:
            if safe_asset not in price_data_dict:
                status_text.text(f"🛡️ Attempting to fetch safe asset data ({safe_asset})...")
                safe_asset_dict = fetch_real_data(
                    [safe_asset],
                    st.session_state.start_date,
                    st.session_state.end_date,
                    data_source,
                    asset_instance,
                    status_text
                )
                
                if safe_asset_dict and safe_asset in safe_asset_dict:
                    price_data_dict[safe_asset] = safe_asset_dict[safe_asset]
                    warnings.append(f"✓ Safe asset '{safe_asset}' data fetched successfully")
                else:
                    # Could not fetch safe asset data - use cash instead
                    warnings.append(
                        f"⚠️ WARNING: Could not fetch real data for safe asset '{safe_asset}'.\n"
                        f"   The strategy will use CASH during defensive periods instead of {safe_asset}."
                    )
                    safe_asset = None  # Use cash
            
            # Set safe asset in config (None = cash)
            strategy_config['safe_asset'] = safe_asset
        
        # Show warnings before starting backtest
        if warnings:
            with warnings_container:
                st.warning("\n\n".join(warnings))
        
        progress_bar.progress(60)
        
        # Create strategy instance
        if st.session_state.strategy_type == "Dual Momentum":
            strategy = DualMomentumStrategy(strategy_config)
        else:
            strategy = AbsoluteMomentumStrategy(strategy_config)
        
        # Initialize backtest engine
        status_text.text("🚀 Running backtest...")
        progress_bar.progress(70)
        
        engine = BacktestEngine(
            initial_capital=st.session_state.get('initial_capital', 100000),
            commission=st.session_state.get('commission', 0.001),
            slippage=st.session_state.get('slippage', 0.0005)
        )
        
        # Run backtest
        results = engine.run(
            strategy=strategy,
            price_data=price_data_dict,
            benchmark_data=benchmark_data
        )
        
        # Calculate additional metrics
        status_text.text("📈 Calculating performance metrics...")
        progress_bar.progress(90)
        
        analyzer = PerformanceCalculator()
        detailed_metrics = analyzer.calculate_metrics(results.returns, results.equity_curve)
        
        # Store results
        progress_bar.progress(100)
        status_text.text("✅ Backtest complete!")
        
        st.session_state.backtest_results = results
        st.session_state.benchmark_data = benchmark_data
        st.session_state.benchmark_symbol = benchmark_symbol
        st.session_state.last_backtest_params = {
            'strategy_type': st.session_state.strategy_type,
            'symbols': symbols,
            'benchmark': benchmark_symbol,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Success message
        st.success("✅ Backtest completed successfully! Navigate to Backtest Results to view analysis.")
        
        # Option to add to comparison
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Results", width='stretch'):
                st.session_state.navigate_to = "📊 Backtest Results"
                st.rerun()
        with col2:
            if st.button("➕ Add to Comparison", width='stretch'):
                strategy_name = f"{st.session_state.strategy_type} - {datetime.now().strftime('%H:%M:%S')}"
                add_to_comparison(results, strategy_name)
                st.success(f"Added '{strategy_name}' to comparison!")
        
    except Exception as e:
        st.error(f"❌ Backtest failed: {str(e)}")
        import traceback
        with st.expander("Show error details"):
            st.code(traceback.format_exc())
    finally:
        progress_bar.empty()
        status_text.empty()


def fetch_real_data(
    symbols: List[str],
    start_date,
    end_date,
    data_source,
    asset_instance,
    status_text=None
) -> Dict[str, PriceData]:
    """
    Fetch REAL market data from Yahoo Finance.
    
    Args:
        symbols: List of symbols to fetch
        start_date: Start date
        end_date: End date
        data_source: Multi-source data provider with automatic failover
        asset_instance: Asset class instance for normalization
        status_text: Optional Streamlit text element for progress updates
    
    Returns:
        Dictionary of symbol -> PriceData with real market data
    """
    from loguru import logger
    
    batch_start = time.time()
    logger.info(f"[FRONTEND FETCH] Starting data fetch for {len(symbols)} symbols")
    logger.info(f"[FRONTEND FETCH] Symbols: {', '.join(symbols)}")
    logger.info(f"[FRONTEND FETCH] Date range: {start_date} to {end_date}")
    logger.info(f"[FRONTEND FETCH] Data source type: {type(data_source).__name__}")
    logger.info(f"[FRONTEND FETCH] Asset class: {type(asset_instance).__name__}")
    
    price_data_dict = {}
    failed_symbols = []
    fetch_times = []
    
    for i, symbol in enumerate(symbols):
        symbol_start = time.time()
        try:
            if status_text:
                status_text.text(f"📊 Fetching {symbol}... ({i+1}/{len(symbols)})")
            
            logger.info(f"[FRONTEND FETCH] Processing symbol {i+1}/{len(symbols)}: {symbol}")
            
            # Fetch real data from Yahoo Finance
            fetch_start = time.time()
            raw_data = data_source.fetch_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe='1d'
            )
            fetch_duration = time.time() - fetch_start
            
            if not raw_data.empty:
                logger.info(f"[FRONTEND FETCH] {symbol}: Received {len(raw_data)} rows in {fetch_duration:.2f}s")
                logger.debug(f"[FRONTEND FETCH] {symbol}: Columns={list(raw_data.columns)}, Date range={raw_data.index[0]} to {raw_data.index[-1]}")
                
                # Normalize data using asset class
                normalize_start = time.time()
                normalized = asset_instance.normalize_data(raw_data, symbol)
                normalize_duration = time.time() - normalize_start
                
                logger.debug(f"[FRONTEND FETCH] {symbol}: Normalized in {normalize_duration:.2f}s")
                price_data_dict[symbol] = normalized
                
                symbol_total = time.time() - symbol_start
                fetch_times.append(symbol_total)
                logger.info(f"[FRONTEND SUCCESS] {symbol}: Complete in {symbol_total:.2f}s (fetch: {fetch_duration:.2f}s, normalize: {normalize_duration:.2f}s)")
            else:
                logger.warning(f"[FRONTEND FAILED] {symbol}: Empty data returned after {fetch_duration:.2f}s")
                failed_symbols.append(symbol)
            
            # Add small delay between requests to avoid rate limiting
            # (except after the last symbol)
            if i < len(symbols) - 1:
                logger.debug(f"[FRONTEND DELAY] Waiting 0.5s before next symbol")
                time.sleep(0.5)
                
        except ConnectionError as e:
            symbol_duration = time.time() - symbol_start
            error_msg = str(e)[:200]
            logger.error(f"[FRONTEND CONNECTION ERROR] {symbol}: {error_msg} (after {symbol_duration:.2f}s)")
            failed_symbols.append(symbol)
            if status_text:
                status_text.text(f"⚠️ Failed to fetch {symbol}: Connection error")
            # Add delay even on error to avoid hammering the API
            if i < len(symbols) - 1:
                time.sleep(0.5)
                
        except ValueError as e:
            symbol_duration = time.time() - symbol_start
            error_msg = str(e)
            logger.error(f"[FRONTEND VALIDATION ERROR] {symbol}: {error_msg} (after {symbol_duration:.2f}s)")
            failed_symbols.append(symbol)
            if status_text:
                status_text.text(f"⚠️ Failed to fetch {symbol}: {error_msg}")
            if i < len(symbols) - 1:
                time.sleep(0.5)
                
        except Exception as e:
            symbol_duration = time.time() - symbol_start
            error_type = type(e).__name__
            error_msg = str(e)[:200]
            logger.error(f"[FRONTEND ERROR] {symbol}: {error_type}: {error_msg} (after {symbol_duration:.2f}s)")
            logger.exception(f"[FRONTEND ERROR] Full traceback for {symbol}:")
            failed_symbols.append(symbol)
            if status_text:
                status_text.text(f"⚠️ Failed to fetch {symbol}: {error_type}")
            # Add delay even on error to avoid hammering the API
            if i < len(symbols) - 1:
                time.sleep(0.5)
    
    batch_duration = time.time() - batch_start
    success_rate = (len(price_data_dict) / len(symbols) * 100) if symbols else 0
    
    logger.info(f"[FRONTEND COMPLETE] Fetched {len(price_data_dict)}/{len(symbols)} symbols ({success_rate:.1f}%) in {batch_duration:.2f}s")
    
    if fetch_times:
        avg_time = sum(fetch_times) / len(fetch_times)
        logger.info(f"[FRONTEND STATS] Average time per symbol: {avg_time:.2f}s, Min: {min(fetch_times):.2f}s, Max: {max(fetch_times):.2f}s")
    
    # Show summary
    if failed_symbols:
        logger.warning(f"[FRONTEND FAILED SUMMARY] Failed symbols: {', '.join(failed_symbols)}")
        st.warning(
            f"⚠️ Could not fetch data for: {', '.join(failed_symbols)}\n"
            f"These symbols will be excluded from the backtest."
        )
    
    return price_data_dict


def save_configuration():
    """Save current configuration for later use."""
    
    config = {
        'strategy_type': st.session_state.get('strategy_type'),
        'asset_class': st.session_state.get('asset_class'),
        'symbols': st.session_state.get('selected_symbols', []),
        'lookback_period': st.session_state.get('lookback_period'),
        'rebalance_freq': st.session_state.get('rebalance_freq'),
        'position_count': st.session_state.get('position_count'),
        'absolute_threshold': st.session_state.get('absolute_threshold'),
        'use_volatility': st.session_state.get('use_volatility'),
        'initial_capital': st.session_state.get('initial_capital'),
        'commission': st.session_state.get('commission'),
        'slippage': st.session_state.get('slippage'),
        'benchmark_symbol': st.session_state.get('benchmark_symbol'),
    }
    
    st.session_state.current_strategy_config = config
    st.success("✅ Configuration saved to session!")
    
    # Option to download
    import json
    config_json = json.dumps(config, indent=2, default=str)
    st.download_button(
        label="📥 Download Configuration",
        data=config_json,
        file_name=f"strategy_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
