"""
Backtest Results page for the Streamlit dashboard.

Displays comprehensive performance metrics, charts, and trade analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

from frontend.utils.styling import (
    render_page_header, render_metric_card, render_info_box, render_section_divider
)
from frontend.utils.state import add_to_comparison
from datetime import timedelta


def render():
    """Render the backtest results page."""
    
    render_page_header(
        "Backtest Results",
        "Comprehensive analysis of your strategy performance",
        "📊"
    )
    
    # Check if results exist
    if 'backtest_results' not in st.session_state or st.session_state.backtest_results is None:
        render_no_results()
        return
    
    results = st.session_state.backtest_results
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Overview",
        "💹 Charts",
        "📋 Trades",
        "📊 Rolling Metrics",
        "🎯 Allocation",
        "⚡ Quick Tune",
        "💾 Export"
    ])
    
    with tab1:
        render_overview(results)
    
    with tab2:
        render_charts(results)
    
    with tab3:
        render_trades(results)
    
    with tab4:
        render_rolling_metrics(results)
    
    with tab5:
        render_allocation(results)
    
    with tab6:
        render_quick_tune(results)
    
    with tab7:
        render_export_options(results)


def render_no_results():
    """Render message when no backtest results exist."""
    
    st.markdown("""
    <div class="info-box">
        <h3>ℹ️ No Backtest Results Available</h3>
        <p>You haven't run any backtests yet. Get started by:</p>
        <ol>
            <li>Navigate to the <strong>Strategy Builder</strong> page</li>
            <li>Configure your strategy parameters</li>
            <li>Click <strong>Run Backtest</strong></li>
        </ol>
        <p>Your results will automatically appear here once the backtest completes.</p>
    </div>
    """, unsafe_allow_html=True)


def render_benchmark_comparison(results, metrics, benchmark_symbol):
    """Render benchmark comparison metrics."""
    
    st.markdown(f"#### 📈 Benchmark Comparison vs {benchmark_symbol}")
    
    # Check if benchmark metrics exist
    has_alpha = 'alpha' in metrics
    
    if not has_alpha:
        st.info("Benchmark comparison metrics not available. This may be due to insufficient data overlap.")
        return
    
    # Top-level comparison metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        alpha = metrics.get('alpha', 0) * 100
        color = "normal" if alpha >= 0 else "inverse"
        st.metric(
            "Alpha (Annual)",
            f"{alpha:.2f}%",
            delta="Excess return" if alpha >= 0 else "Underperformance",
            delta_color=color
        )
    
    with col2:
        beta = metrics.get('beta', 0)
        st.metric(
            "Beta",
            f"{beta:.2f}",
            delta="Market sensitivity"
        )
    
    with col3:
        info_ratio = metrics.get('information_ratio', 0)
        st.metric(
            "Information Ratio",
            f"{info_ratio:.2f}",
            delta="Risk-adj. alpha"
        )
    
    with col4:
        correlation = metrics.get('benchmark_correlation', 0)
        st.metric(
            "Correlation",
            f"{correlation:.2f}",
            delta="vs benchmark"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detailed benchmark metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Performance vs Benchmark")
        benchmark_df = pd.DataFrame({
            'Metric': [
                'Active Return (Ann.)',
                'Excess Return (Cum.)',
                'Tracking Error',
                'Up Capture Ratio',
                'Down Capture Ratio'
            ],
            'Value': [
                f"{metrics.get('active_return', 0)*100:.2f}%",
                f"{metrics.get('excess_return', 0)*100:.2f}%",
                f"{metrics.get('tracking_error', 0)*100:.2f}%",
                f"{metrics.get('up_capture', 0)*100:.1f}%",
                f"{metrics.get('down_capture', 0)*100:.1f}%"
            ]
        })
        st.dataframe(benchmark_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("##### Interpretation Guide")
        st.markdown("""
        - **Alpha**: Excess return vs benchmark (positive is better)
        - **Beta**: Market sensitivity (1.0 = matches benchmark)
        - **Info Ratio**: Risk-adjusted outperformance (>0.5 is good)
        - **Up Capture**: % of benchmark gains captured (>100% is better)
        - **Down Capture**: % of benchmark losses captured (<100% is better)
        """, unsafe_allow_html=True)


def render_overview(results):
    """Render performance overview with summary metrics."""
    
    st.markdown("### 📊 Performance Summary")
    
    # Check if benchmark data exists
    has_benchmark = (
        'benchmark_symbol' in st.session_state and 
        st.session_state.benchmark_symbol and
        'benchmark_data' in st.session_state and
        st.session_state.benchmark_data is not None
    )
    
    # Extract metrics
    metrics = results.metrics
    
    # Top-level metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_return = metrics.get('total_return', 0) * 100
        color = "positive" if total_return > 0 else "negative"
        st.metric(
            "Total Return",
            f"{total_return:.2f}%",
            delta=f"{metrics.get('annualized_return', 0)*100:.2f}% ann."
        )
    
    with col2:
        sharpe = metrics.get('sharpe_ratio', 0)
        st.metric(
            "Sharpe Ratio",
            f"{sharpe:.2f}",
            delta="Risk-adjusted"
        )
    
    with col3:
        max_dd = metrics.get('max_drawdown', 0) * 100
        st.metric(
            "Max Drawdown",
            f"{max_dd:.2f}%",
            delta="Peak to trough",
            delta_color="inverse"
        )
    
    with col4:
        win_rate = results.win_rate * 100 if hasattr(results, 'win_rate') else \
                   metrics.get('win_rate', 0) * 100
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta=f"{results.num_trades if hasattr(results, 'num_trades') else metrics.get('num_trades', 0)} trades"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detailed metrics table
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Return Metrics")
        metrics_df = pd.DataFrame({
            'Metric': [
                'Total Return',
                'Annualized Return',
                'CAGR',
                'Best Month',
                'Worst Month',
                'Positive Months'
            ],
            'Value': [
                f"{metrics.get('total_return', 0)*100:.2f}%",
                f"{metrics.get('annualized_return', 0)*100:.2f}%",
                f"{metrics.get('cagr', 0)*100:.2f}%",
                f"{metrics.get('best_month', 0)*100:.2f}%",
                f"{metrics.get('worst_month', 0)*100:.2f}%",
                f"{metrics.get('positive_months', 0):.0f}%"
            ]
        })
        st.dataframe(metrics_df, hide_index=True, width='stretch')
    
    with col2:
        st.markdown("#### ⚖️ Risk Metrics")
        risk_df = pd.DataFrame({
            'Metric': [
                'Volatility (Ann.)',
                'Sharpe Ratio',
                'Sortino Ratio',
                'Calmar Ratio',
                'Max Drawdown',
                'Avg Drawdown'
            ],
            'Value': [
                f"{metrics.get('volatility', 0)*100:.2f}%",
                f"{metrics.get('sharpe_ratio', 0):.2f}",
                f"{metrics.get('sortino_ratio', 0):.2f}",
                f"{metrics.get('calmar_ratio', 0):.2f}",
                f"{metrics.get('max_drawdown', 0)*100:.2f}%",
                f"{metrics.get('avg_drawdown', 0)*100:.2f}%"
            ]
        })
        st.dataframe(risk_df, hide_index=True, width='stretch')
    
    render_section_divider()
    
    # Benchmark comparison section
    if has_benchmark:
        render_benchmark_comparison(results, metrics, st.session_state.benchmark_symbol)
        render_section_divider()
    
    # Trading statistics
    st.markdown("#### 📊 Trading Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", f"{metrics.get('num_trades', 0):.0f}")
    
    with col2:
        st.metric("Winning Trades", f"{metrics.get('winning_trades', 0):.0f}")
    
    with col3:
        st.metric("Losing Trades", f"{metrics.get('losing_trades', 0):.0f}")
    
    with col4:
        st.metric("Avg Trade", f"{metrics.get('avg_trade_pnl', 0)*100:.2f}%")
    
    # Action buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        strategy_name = f"{st.session_state.get('strategy_type', 'Strategy')} - {datetime.now().strftime('%H:%M:%S')}"
        if st.button("➕ Add to Comparison", use_container_width=True):
            add_to_comparison(results, strategy_name)
            st.success(f"Added to comparison list!")
    
    with col2:
        if st.button("🎯 Tune Parameters", use_container_width=True, type="primary"):
            # Pre-populate tuning configuration from current backtest
            _prepare_tuning_from_backtest()
            st.session_state.navigate_to = "🎯 Hyperparameter Tuning"
            st.rerun()
    
    with col3:
        if st.button("🔄 Run New Backtest", use_container_width=True):
            st.session_state.navigate_to = "🛠️ Strategy Builder"
            st.rerun()
    
    with col4:
        if st.button("📥 Download Report", use_container_width=True):
            st.info("See Export tab for download options")


def render_charts(results):
    """Render interactive performance charts."""
    
    st.markdown("### 📈 Performance Charts")
    
    # Check if benchmark data exists
    has_benchmark = (
        'benchmark_symbol' in st.session_state and 
        st.session_state.benchmark_symbol and
        'benchmark_data' in st.session_state and
        st.session_state.benchmark_data is not None
    )
    
    # Equity curve
    st.markdown("#### Portfolio Value Over Time")
    
    if hasattr(results, 'equity_curve'):
        fig = go.Figure()
        
        equity_df = results.equity_curve.reset_index()
        equity_df.columns = ['Date', 'Value']
        
        fig.add_trace(go.Scatter(
            x=equity_df['Date'],
            y=equity_df['Value'],
            mode='lines',
            name='Strategy',
            line=dict(color='#1f77b4', width=2),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))
        
        # Add benchmark if available
        if hasattr(results, 'benchmark_curve') and results.benchmark_curve is not None:
            try:
                # Use the indexed benchmark curve from results (already properly aligned and indexed)
                benchmark_curve = results.benchmark_curve
                
                # Convert to DataFrame for plotting
                benchmark_df = benchmark_curve.reset_index()
                benchmark_df.columns = ['Date', 'Value']
                
                # Align with strategy dates
                benchmark_aligned = benchmark_curve.reindex(equity_df['Date']).ffill()
                
                fig.add_trace(go.Scatter(
                    x=equity_df['Date'],
                    y=benchmark_aligned.values,
                    mode='lines',
                    name=f'Benchmark ({st.session_state.benchmark_symbol})',
                    line=dict(color='#ff7f0e', width=2, dash='dash')
                ))
            except Exception as e:
                pass  # Silently skip if benchmark data can't be plotted
        
        # Add initial capital line
        initial_capital = results.initial_capital
        fig.add_hline(
            y=initial_capital,
            line_dash="dot",
            line_color="gray",
            annotation_text="Initial Capital",
            annotation_position="right"
        )
        
        fig.update_layout(
            title="Equity Curve - Strategy vs Benchmark",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Returns comparison chart
    if hasattr(results, 'benchmark_curve') and results.benchmark_curve is not None:
        st.markdown("#### Cumulative Returns Comparison")
        
        try:
            strategy_returns = results.returns
            benchmark_curve = results.benchmark_curve
            benchmark_returns = benchmark_curve.pct_change().dropna()
            
            # Align returns
            strategy_returns_aligned, benchmark_returns_aligned = strategy_returns.align(
                benchmark_returns, join='inner'
            )
            
            # Calculate cumulative returns
            strategy_cum_returns = (1 + strategy_returns_aligned).cumprod() - 1
            benchmark_cum_returns = (1 + benchmark_returns_aligned).cumprod() - 1
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=strategy_cum_returns.index,
                y=strategy_cum_returns.values * 100,
                mode='lines',
                name='Strategy',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=benchmark_cum_returns.index,
                y=benchmark_cum_returns.values * 100,
                mode='lines',
                name=f'Benchmark ({st.session_state.benchmark_symbol})',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            
            fig.add_hline(y=0, line_dash="dot", line_color="gray")
            
            fig.update_layout(
                title="Cumulative Returns - Strategy vs Benchmark",
                xaxis_title="Date",
                yaxis_title="Cumulative Return (%)",
                hovermode='x unified',
                height=350,
                showlegend=True
            )
            
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.warning(f"Could not generate returns comparison chart: {str(e)}")
    
    # Drawdown chart
    st.markdown("#### Drawdown Analysis")
    
    if hasattr(results, 'equity_curve'):
        # Calculate strategy drawdown
        equity = results.equity_curve
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max * 100
        
        fig = go.Figure()
        
        drawdown_df = drawdown.reset_index()
        drawdown_df.columns = ['Date', 'Drawdown']
        
        fig.add_trace(go.Scatter(
            x=drawdown_df['Date'],
            y=drawdown_df['Drawdown'],
            mode='lines',
            name='Strategy Drawdown',
            line=dict(color='#d62728', width=2),
            fill='tozeroy',
            fillcolor='rgba(214, 39, 40, 0.3)'
        ))
        
        # Add benchmark drawdown if available
        if hasattr(results, 'benchmark_curve') and results.benchmark_curve is not None:
            try:
                benchmark_curve = results.benchmark_curve
                benchmark_running_max = benchmark_curve.cummax()
                benchmark_drawdown = (benchmark_curve - benchmark_running_max) / benchmark_running_max * 100
                
                # Align with strategy dates
                benchmark_drawdown_aligned = benchmark_drawdown.reindex(drawdown_df['Date']).ffill()
                
                fig.add_trace(go.Scatter(
                    x=drawdown_df['Date'],
                    y=benchmark_drawdown_aligned.values,
                    mode='lines',
                    name=f'Benchmark ({st.session_state.benchmark_symbol}) Drawdown',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 127, 14, 0.2)'
                ))
            except Exception as e:
                pass  # Silently skip if benchmark drawdown can't be plotted
        
        fig.update_layout(
            title="Portfolio Drawdown - Strategy vs Benchmark",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig, width='stretch')
    
    render_section_divider()
    
    # Monthly returns heatmap
    st.markdown("#### Monthly Returns Heatmap")
    
    if hasattr(results, 'returns'):
        try:
            # Convert returns to monthly (use 'ME' for month-end instead of deprecated 'M')
            monthly_returns = results.returns.resample('ME').apply(lambda x: (1 + x).prod() - 1 if len(x) > 0 else 0)
            
            # Create pivot table for heatmap
            monthly_returns_df = pd.DataFrame({
                'Year': monthly_returns.index.year,
                'Month': monthly_returns.index.month,
                'Return': monthly_returns.values * 100
            })
            
            pivot = monthly_returns_df.pivot(index='Month', columns='Year', values='Return')
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                colorscale='RdYlGn',
                zmid=0,
                text=pivot.values,
                texttemplate='%{text:.1f}%',
                textfont={"size": 10},
                colorbar=dict(title="Return (%)")
            ))
            
            fig.update_layout(
                title="Monthly Returns by Year",
                xaxis_title="Year",
                yaxis_title="Month",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
        except:
            st.info("Insufficient data for monthly returns heatmap")
    
    # Distribution of returns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Returns Distribution")
        
        if hasattr(results, 'returns'):
            returns_pct = results.returns * 100
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=returns_pct,
                nbinsx=50,
                name='Returns',
                marker_color='#1f77b4'
            ))
            
            fig.update_layout(
                title="Distribution of Returns",
                xaxis_title="Return (%)",
                yaxis_title="Frequency",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("#### Trade P&L Distribution")
        
        if hasattr(results, 'trades') and len(results.trades) > 0:
            pnl_pct = results.trades['pnl_pct']
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=pnl_pct,
                nbinsx=30,
                name='Trade P&L',
                marker_color='#2ca02c'
            ))
            
            fig.update_layout(
                title="Distribution of Trade Returns",
                xaxis_title="Return (%)",
                yaxis_title="Frequency",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, width='stretch')


def render_trades(results):
    """Render detailed trade analysis."""
    
    st.markdown("### 📋 Trade History")
    
    if not hasattr(results, 'trades') or len(results.trades) == 0:
        render_info_box("No trades executed during this backtest period.", "info")
        return
    
    trades_df = results.trades.copy()
    
    # Format columns for display
    display_df = trades_df.copy()
    
    # Format dates - handle different column name conventions
    timestamp_cols = [
        ('entry_timestamp', 'entry_timestamp'),
        ('exit_timestamp', 'exit_timestamp'),
        ('Entry Timestamp', 'Entry Timestamp'),
        ('Exit Timestamp', 'Exit Timestamp')
    ]
    
    for col, _ in timestamp_cols:
        if col in display_df.columns:
            try:
                display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d')
            except Exception:
                pass  # Keep original format if conversion fails
    
    # Format currency columns
    for col in ['entry_price', 'exit_price', 'pnl']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
    
    # Format percentage
    if 'pnl_pct' in display_df.columns:
        display_df['pnl_pct'] = display_df['pnl_pct'].apply(lambda x: f"{x:.2f}%")
    
    # Filter and search
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_symbol = st.text_input("🔍 Search by symbol", "")
        if search_symbol:
            display_df = display_df[display_df['symbol'].str.contains(search_symbol, case=False)]
    
    with col2:
        trade_filter = st.selectbox(
            "Filter trades",
            ["All", "Winners", "Losers"]
        )
        
        if trade_filter == "Winners":
            display_df = display_df[trades_df['pnl'] > 0]
        elif trade_filter == "Losers":
            display_df = display_df[trades_df['pnl'] < 0]
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Entry Date", "P&L", "Symbol"]
        )
    
    # Display trades table
    st.dataframe(
        display_df,
        width='stretch',
        height=400
    )
    
    # Trade statistics
    render_section_divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean()
        st.metric("Avg Win", f"{avg_win:.2f}%")
    
    with col2:
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean()
        st.metric("Avg Loss", f"{avg_loss:.2f}%")
    
    with col3:
        # Calculate average trade duration - handle different column name conventions
        avg_duration_days = 0
        if 'exit_timestamp' in trades_df.columns and 'entry_timestamp' in trades_df.columns:
            avg_duration = (trades_df['exit_timestamp'] - trades_df['entry_timestamp']).mean()
            avg_duration_days = avg_duration.days if pd.notna(avg_duration) else 0
        elif 'Exit Timestamp' in trades_df.columns and 'Entry Timestamp' in trades_df.columns:
            avg_duration = (trades_df['Exit Timestamp'] - trades_df['Entry Timestamp']).mean()
            avg_duration_days = avg_duration.days if pd.notna(avg_duration) else 0
        elif 'duration' in trades_df.columns:
            # Duration column might already be calculated
            duration_col = trades_df['duration']
            if pd.api.types.is_timedelta64_dtype(duration_col):
                avg_duration_days = int(duration_col.mean().total_seconds() / 86400)
            else:
                avg_duration_days = int(duration_col.mean())
        elif 'Duration' in trades_df.columns:
            # VectorBT format
            duration_col = trades_df['Duration']
            if pd.api.types.is_timedelta64_dtype(duration_col):
                avg_duration_days = int(duration_col.mean().total_seconds() / 86400)
            else:
                avg_duration_days = int(duration_col.mean())
        
        st.metric("Avg Duration", f"{avg_duration_days} days")
    
    with col4:
        profit_factor = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                           trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0
        st.metric("Profit Factor", f"{profit_factor:.2f}")
    
    # Download trades
    st.markdown("<br>", unsafe_allow_html=True)
    
    csv = trades_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Trades CSV",
        data=csv,
        file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        width='stretch'
    )


def render_rolling_metrics(results):
    """Render rolling performance metrics."""
    
    st.markdown("### 📊 Rolling Performance Metrics")
    
    if not hasattr(results, 'returns'):
        render_info_box("Rolling metrics not available for this backtest.", "info")
        return
    
    # Window selection
    window = st.slider(
        "Rolling Window (days)",
        min_value=20,
        max_value=252,
        value=60,
        step=10
    )
    
    returns = results.returns
    
    # Calculate rolling metrics
    rolling_sharpe = (returns.rolling(window).mean() / returns.rolling(window).std()) * (252 ** 0.5)
    rolling_vol = returns.rolling(window).std() * (252 ** 0.5) * 100
    
    # Rolling Sharpe
    st.markdown("#### Rolling Sharpe Ratio")
    
    fig = go.Figure()
    
    sharpe_df = rolling_sharpe.reset_index()
    sharpe_df.columns = ['Date', 'Sharpe']
    
    fig.add_trace(go.Scatter(
        x=sharpe_df['Date'],
        y=sharpe_df['Sharpe'],
        mode='lines',
        name='Rolling Sharpe',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title=f"{window}-Day Rolling Sharpe Ratio",
        xaxis_title="Date",
        yaxis_title="Sharpe Ratio",
        hovermode='x unified',
        height=300
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Rolling Volatility
    st.markdown("#### Rolling Volatility")
    
    fig = go.Figure()
    
    vol_df = rolling_vol.reset_index()
    vol_df.columns = ['Date', 'Volatility']
    
    fig.add_trace(go.Scatter(
        x=vol_df['Date'],
        y=vol_df['Volatility'],
        mode='lines',
        name='Rolling Volatility',
        line=dict(color='#ff7f0e', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 127, 14, 0.1)'
    ))
    
    fig.update_layout(
        title=f"{window}-Day Rolling Volatility",
        xaxis_title="Date",
        yaxis_title="Annualized Volatility (%)",
        hovermode='x unified',
        height=300
    )
    
    st.plotly_chart(fig, width='stretch')


def render_allocation(results):
    """Render allocation analysis showing how capital was allocated over time."""
    
    st.markdown("### 🎯 Portfolio Allocation Over Time")
    
    st.markdown("""
    Visualize how your strategy allocated capital across different assets throughout the backtesting period.
    """)
    
    # Check if we have positions data
    if not hasattr(results, 'positions'):
        st.warning("⚠️ Position data attribute is missing from backtest results. This may indicate an issue with the backtesting engine.")
        st.info("Allocation tracking requires position history to be captured during the backtest.")
        return
    
    # Check if positions DataFrame is empty
    if isinstance(results.positions, pd.DataFrame):
        if results.positions.empty:
            st.warning("⚠️ Position data DataFrame is empty (no rows). This may occur if:")
            st.markdown("""
            - The backtest period was too short
            - No trading signals were generated
            - All trades were rejected due to insufficient capital
            """)
            return
    elif len(results.positions) == 0:
        st.warning("⚠️ Position data is empty.")
        return
    
    # Calculate allocation over time
    allocation_df = _calculate_allocation_over_time(results)
    
    if allocation_df is None or len(allocation_df) == 0:
        st.info("Unable to calculate allocation data from available position history.")
        return
    
    # Stacked area chart showing allocation percentages
    st.markdown("#### 📊 Allocation Over Time (Percentage)")
    
    fig = go.Figure()
    
    # Get all symbols from the allocation dataframe
    symbols = [col for col in allocation_df.columns if col not in ['Date', 'Cash']]
    
    # Add cash allocation first (at the bottom)
    if 'Cash' in allocation_df.columns:
        fig.add_trace(go.Scatter(
            x=allocation_df['Date'],
            y=allocation_df['Cash'],
            mode='lines',
            name='Cash',
            stackgroup='one',
            fillcolor='rgba(200, 200, 200, 0.5)',
            line=dict(width=0.5, color='rgb(150, 150, 150)'),
            hovertemplate='<b>Cash</b><br>%{y:.1f}%<extra></extra>'
        ))
    
    # Define a color palette for assets
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set2
    
    # Add each asset's allocation
    for i, symbol in enumerate(symbols):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=allocation_df['Date'],
            y=allocation_df[symbol],
            mode='lines',
            name=symbol,
            stackgroup='one',
            line=dict(width=0.5),
            hovertemplate=f'<b>{symbol}</b><br>%{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        title="Portfolio Allocation by Asset",
        xaxis_title="Date",
        yaxis_title="Allocation (%)",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    render_section_divider()
    
    # Allocation statistics
    st.markdown("#### 📈 Allocation Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Average Allocation per Asset**")
        avg_allocation = allocation_df[symbols].mean().sort_values(ascending=False)
        avg_df = pd.DataFrame({
            'Asset': avg_allocation.index,
            'Avg Allocation (%)': avg_allocation.values
        })
        avg_df['Avg Allocation (%)'] = avg_df['Avg Allocation (%)'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(avg_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("**Allocation Range per Asset**")
        range_data = []
        for symbol in symbols:
            min_val = allocation_df[symbol].min()
            max_val = allocation_df[symbol].max()
            range_data.append({
                'Asset': symbol,
                'Min (%)': f"{min_val:.2f}%",
                'Max (%)': f"{max_val:.2f}%"
            })
        range_df = pd.DataFrame(range_data)
        st.dataframe(range_df, hide_index=True, use_container_width=True)
    
    render_section_divider()
    
    # Rebalancing events
    st.markdown("#### 🔄 Allocation at Rebalancing Events")
    
    rebalance_allocation = _get_rebalancing_allocation(results, allocation_df)
    
    if rebalance_allocation is not None and len(rebalance_allocation) > 0:
        # Display as interactive table
        st.dataframe(
            rebalance_allocation.style.format({
                col: '{:.2f}%' for col in rebalance_allocation.columns if col != 'Date'
            }),
            use_container_width=True,
            height=400
        )
        
        # Download button
        csv = rebalance_allocation.to_csv(index=False)
        st.download_button(
            label="📥 Download Allocation History (CSV)",
            data=csv,
            file_name=f"allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Rebalancing event details not available.")
    
    render_section_divider()
    
    # Allocation heatmap
    st.markdown("#### 🗺️ Allocation Heatmap")
    
    if len(symbols) > 1:
        # Create heatmap showing allocation changes over time
        # Sample the data to avoid too many time points
        sample_size = min(50, len(allocation_df))
        sample_indices = np.linspace(0, len(allocation_df) - 1, sample_size, dtype=int)
        sampled_df = allocation_df.iloc[sample_indices]
        
        # Prepare data for heatmap
        heatmap_data = sampled_df[symbols].T
        dates_formatted = sampled_df['Date'].dt.strftime('%Y-%m-%d').tolist()
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=dates_formatted,
            y=symbols,
            colorscale='Viridis',
            hovertemplate='Asset: %{y}<br>Date: %{x}<br>Allocation: %{z:.1f}%<extra></extra>',
            colorbar=dict(title="Allocation (%)")
        ))
        
        fig.update_layout(
            title="Allocation Heatmap Over Time",
            xaxis_title="Date",
            yaxis_title="Asset",
            height=max(300, len(symbols) * 40),
            xaxis={'side': 'bottom'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Heatmap requires multiple assets to display.")


def _extract_allocation_from_position_history(positions_df):
    """
    Extract allocation data from standard BacktestEngine position history.
    
    Args:
        positions_df: DataFrame with position history (has _pct columns)
    
    Returns:
        DataFrame with dates and allocation percentages for each asset
    """
    try:
        # Extract percentage columns (exclude cash and portfolio itself)
        pct_columns = [col for col in positions_df.columns 
                      if col.endswith('_pct') 
                      and col not in ['cash_pct', 'portfolio_pct']]
        
        # Create allocation DataFrame
        allocation_dict = {'Date': positions_df.index}
        
        # Add cash allocation
        if 'cash_pct' in positions_df.columns:
            allocation_dict['Cash'] = positions_df['cash_pct'].values
        else:
            allocation_dict['Cash'] = np.zeros(len(positions_df))
        
        # Add each symbol's allocation (backtested assets only)
        for pct_col in pct_columns:
            symbol = pct_col.replace('_pct', '')
            allocation_dict[symbol] = positions_df[pct_col].values
        
        allocation_df = pd.DataFrame(allocation_dict)
        
        if allocation_df.empty:
            st.warning("⚠️ Allocation DataFrame is empty after extraction")
            return None
        
        return allocation_df
    
    except Exception as e:
        st.error(f"Error extracting allocation from position history: {str(e)}")
        import traceback
        with st.expander("Show error details"):
            st.code(traceback.format_exc())
        return None


def _calculate_allocation_over_time(results):
    """
    Calculate portfolio allocation percentages over time.
    
    Args:
        results: BacktestResult object
    
    Returns:
        DataFrame with dates and allocation percentages for each asset
    """
    try:
        # Get equity curve for total portfolio value
        equity_curve = results.equity_curve
        
        # Check if we have positions data
        positions_df = results.positions
        
        if positions_df is None:
            return None
        
        # Check if DataFrame is empty
        if isinstance(positions_df, pd.DataFrame) and positions_df.empty:
            return None
        elif not isinstance(positions_df, pd.DataFrame) and len(positions_df) == 0:
            return None
        
        # Check if this is the new standard engine format (has _pct columns)
        pct_columns = [col for col in positions_df.columns if col.endswith('_pct') and col != 'cash_pct']
        
        if len(pct_columns) > 0:
            # New format from standard BacktestEngine - already has percentages calculated
            return _extract_allocation_from_position_history(positions_df)
        
        # VectorBT positions have different column names
        # Try to identify the relevant columns
        required_cols = set()
        col_mapping = {}
        
        # Map common column name variations
        for col in positions_df.columns:
            col_lower = col.lower()
            if 'column' in col_lower or 'symbol' in col_lower:
                col_mapping['symbol'] = col
                required_cols.add('symbol')
            elif 'entry' in col_lower and 'idx' in col_lower:
                col_mapping['entry_idx'] = col
                required_cols.add('entry_idx')
            elif 'exit' in col_lower and 'idx' in col_lower:
                col_mapping['exit_idx'] = col
                required_cols.add('exit_idx')
            elif 'size' in col_lower:
                col_mapping['size'] = col
                required_cols.add('size')
        
        # If we don't have the required columns, try to construct allocation from equity and trades
        if len(required_cols) < 3:
            return _calculate_allocation_from_trades(results)
        
        # Create a time series of allocations
        dates = equity_curve.index
        allocation_dict = {'Date': dates}
        
        # Initialize allocation tracking
        symbols = positions_df[col_mapping['symbol']].unique() if 'symbol' in col_mapping else []
        for symbol in symbols:
            allocation_dict[symbol] = np.zeros(len(dates))
        allocation_dict['Cash'] = np.zeros(len(dates))
        
        # Iterate through time and calculate allocation at each point
        for i, date in enumerate(dates):
            portfolio_value = equity_curve.iloc[i]
            
            # Find active positions at this date
            asset_values = {}
            
            for _, pos in positions_df.iterrows():
                symbol = pos[col_mapping['symbol']]
                entry_idx = pos[col_mapping.get('entry_idx', 'Entry Index')]
                exit_idx = pos[col_mapping.get('exit_idx', 'Exit Index')]
                size = abs(pos[col_mapping.get('size', 'Size')])
                
                # Check if position is active at this date
                if entry_idx <= i < exit_idx:
                    # Estimate position value (size * current price)
                    # Since we don't have price here, use equity proportions
                    if symbol not in asset_values:
                        asset_values[symbol] = 0
                    asset_values[symbol] += size
            
            # Calculate percentages
            total_asset_value = sum(asset_values.values())
            if portfolio_value > 0:
                for symbol, value in asset_values.items():
                    allocation_dict[symbol][i] = (value / total_asset_value * 100) if total_asset_value > 0 else 0
                
                # Cash is the remainder
                total_allocated = sum(allocation_dict[symbol][i] for symbol in symbols if symbol in allocation_dict)
                allocation_dict['Cash'][i] = max(0, 100 - total_allocated)
        
        # Convert to DataFrame
        allocation_df = pd.DataFrame(allocation_dict)
        
        return allocation_df
    
    except Exception as e:
        st.error(f"Error calculating allocation: {str(e)}")
        return _calculate_allocation_from_trades(results)


def _calculate_allocation_from_trades(results):
    """
    Alternative method to calculate allocation from trades and equity curve.
    
    Args:
        results: BacktestResult object
    
    Returns:
        DataFrame with allocation over time
    """
    try:
        if not hasattr(results, 'trades') or len(results.trades) == 0:
            return None
        
        trades_df = results.trades
        equity_curve = results.equity_curve
        
        # Create allocation tracking
        dates = equity_curve.index
        allocation_dict = {'Date': dates}
        
        # Get all symbols from trades
        symbols = trades_df['symbol'].unique() if 'symbol' in trades_df.columns else []
        
        for symbol in symbols:
            allocation_dict[symbol] = np.zeros(len(dates))
        allocation_dict['Cash'] = np.full(len(dates), 100.0)
        
        # Track positions based on entry and exit
        for _, trade in trades_df.iterrows():
            symbol = trade['symbol']
            entry_time = trade['entry_timestamp'] if 'entry_timestamp' in trade else None
            exit_time = trade['exit_timestamp'] if 'exit_timestamp' in trade else None
            
            if entry_time is None or exit_time is None:
                continue
            
            # Find date indices
            entry_mask = dates >= entry_time
            exit_mask = dates < exit_time
            active_mask = entry_mask & exit_mask
            
            # For simplicity, assume equal weight among active positions
            # This is a rough approximation
            for i in np.where(active_mask)[0]:
                allocation_dict[symbol][i] = 100.0 / len(symbols)
        
        # Recalculate cash
        for i in range(len(dates)):
            total_invested = sum(allocation_dict[symbol][i] for symbol in symbols)
            allocation_dict['Cash'][i] = max(0, 100 - total_invested)
        
        return pd.DataFrame(allocation_dict)
    
    except Exception as e:
        st.error(f"Error calculating allocation from trades: {str(e)}")
        return None


def _get_rebalancing_allocation(results, allocation_df):
    """
    Extract allocation data at rebalancing events.
    
    Args:
        results: BacktestResult object
        allocation_df: DataFrame with allocation over time
    
    Returns:
        DataFrame with allocation at each rebalancing event
    """
    try:
        if allocation_df is None or len(allocation_df) == 0:
            return None
        
        # Identify rebalancing events by detecting changes in allocation
        # A rebalancing event is when allocation changes significantly
        
        rebalance_dates = []
        threshold = 1.0  # 1% change threshold
        
        for i in range(1, len(allocation_df)):
            # Check if any allocation changed significantly
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
        
        # Extract allocation at these dates
        rebalance_allocation = allocation_df.iloc[rebalance_dates].reset_index(drop=True)
        
        return rebalance_allocation
    
    except Exception as e:
        st.error(f"Error extracting rebalancing allocation: {str(e)}")
        return None


def _prepare_tuning_from_backtest():
    """
    Prepare hyperparameter tuning configuration from current backtest settings.
    
    This function extracts the current backtest configuration and pre-populates
    the tuning page with sensible defaults based on the current setup.
    """
    # Get current backtest parameters
    backtest_params = st.session_state.get('last_backtest_params', {})
    
    # Mark that tuning was initiated from backtest results
    st.session_state.tuning_from_backtest = True
    
    # Extract and set tuning configuration
    if 'start_date' in backtest_params:
        st.session_state.tune_start_date = backtest_params['start_date']
    if 'end_date' in backtest_params:
        st.session_state.tune_end_date = backtest_params['end_date']
    
    # Set capital and transaction costs
    st.session_state.tune_initial_capital = backtest_params.get('initial_capital', 100000.0)
    st.session_state.tune_commission = backtest_params.get('commission', 0.001)
    st.session_state.tune_slippage = backtest_params.get('slippage', 0.0005)
    
    # Set benchmark
    st.session_state.tune_benchmark = backtest_params.get('benchmark_symbol', 'SPY')
    
    # Set asset universe
    if 'universe' in backtest_params:
        st.session_state.tune_universe = backtest_params['universe']
    elif 'symbols' in backtest_params:
        st.session_state.tune_universe = backtest_params['symbols']
    
    # Set safe asset
    st.session_state.tune_safe_asset = backtest_params.get('safe_asset', 'AGG')
    
    # Set default optimization settings
    st.session_state.tune_method = "Random Search"
    st.session_state.tune_metric = "sharpe_ratio"
    st.session_state.tune_higher_is_better = True
    st.session_state.tune_n_trials = 50
    st.session_state.tune_random_seed = 42
    
    # Set default parameter space based on current strategy config
    strategy_config = backtest_params.get('strategy_config', {})
    current_lookback = strategy_config.get('lookback_period', 252)
    current_position_count = strategy_config.get('position_count', 1)
    current_threshold = strategy_config.get('absolute_threshold', 0.0)
    
    # Create parameter space with ranges around current values
    st.session_state.tune_param_space = [
        {
            'name': 'lookback_period',
            'type': 'int',
            'values': _generate_lookback_values(current_lookback)
        },
        {
            'name': 'position_count',
            'type': 'int',
            'values': [1, 2, 3, 4] if current_position_count <= 4 else [1, 2, 3, 4, 5]
        },
        {
            'name': 'absolute_threshold',
            'type': 'float',
            'values': [-0.02, -0.01, 0.0, 0.01, 0.02, 0.05]
        },
    ]
    
    # Store a message to display in tuning page
    st.session_state.tuning_message = (
        "📊 **Tuning configuration pre-populated from your backtest results!** "
        "The parameter ranges are centered around your current strategy settings. "
        "Review the configuration below and click 'Start Optimization' when ready."
    )


def _generate_lookback_values(current_value: int) -> list:
    """
    Generate lookback period values centered around current value.
    
    Args:
        current_value: Current lookback period
        
    Returns:
        List of lookback values to test
    """
    # Common lookback periods (in trading days)
    common_periods = [21, 42, 63, 126, 189, 252, 315, 378, 441, 504]
    
    # Find closest common periods
    values = []
    for period in common_periods:
        if abs(period - current_value) <= 126:  # Within ~6 months
            values.append(period)
    
    # Ensure we have at least 4-5 values
    if len(values) < 4:
        # Add current value and neighbors
        values = sorted(set([
            max(21, current_value - 126),
            max(21, current_value - 63),
            current_value,
            current_value + 63,
            current_value + 126
        ]))
    
    return sorted(set(values))


def render_quick_tune(results):
    """Render quick parameter tuning interface for easy adjustments and re-runs."""
    
    st.markdown("### ⚡ Quick Parameter Tuning")
    
    st.markdown("""
    Quickly adjust strategy parameters and re-run the backtest to see how changes affect performance.
    This is ideal for iterative testing and parameter sensitivity analysis.
    """)
    
    # Get current parameters from last backtest
    last_params = st.session_state.get('last_backtest_params', {})
    strategy_config = last_params.get('strategy_config', {})
    
    if not last_params:
        st.warning("⚠️ No backtest configuration found. Please run a backtest from the Strategy Builder first.")
        return
    
    st.markdown("---")
    
    # Current vs New comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Current Parameters")
        
        current_lookback = strategy_config.get('lookback_period', 252)
        current_position_count = strategy_config.get('position_count', 1)
        current_threshold = strategy_config.get('absolute_threshold', 0.0)
        current_rebalance = strategy_config.get('rebalance_frequency', 'monthly')
        current_volatility = strategy_config.get('use_volatility_adjustment', False)
        
        st.info(f"""
        - **Lookback Period:** {current_lookback} days
        - **Position Count:** {current_position_count}
        - **Absolute Threshold:** {current_threshold:.2%}
        - **Rebalance Frequency:** {current_rebalance.title()}
        - **Volatility Adjustment:** {'Yes' if current_volatility else 'No'}
        """)
        
        # Show current performance
        st.markdown("##### Current Performance")
        metrics = results.metrics
        perf_col1, perf_col2 = st.columns(2)
        with perf_col1:
            st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
        with perf_col2:
            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
            st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.1f}%")
    
    with col2:
        st.markdown("#### ⚙️ Adjust Parameters")
        
        # Parameter adjustment controls
        new_lookback = st.slider(
            "Lookback Period (days)",
            min_value=21,
            max_value=504,
            value=current_lookback,
            step=21,
            help="Number of days to calculate momentum"
        )
        
        new_position_count = st.number_input(
            "Number of Positions",
            min_value=1,
            max_value=10,
            value=current_position_count,
            help="How many top-ranked assets to hold"
        )
        
        new_threshold = st.slider(
            "Absolute Momentum Threshold",
            min_value=-0.20,
            max_value=0.20,
            value=float(current_threshold),
            step=0.01,
            format="%.2f",
            help="Minimum momentum required to enter position"
        )
        
        new_rebalance = st.selectbox(
            "Rebalance Frequency",
            ["daily", "weekly", "monthly", "quarterly"],
            index=["daily", "weekly", "monthly", "quarterly"].index(current_rebalance.lower()),
            help="How often to recalculate positions"
        )
        
        new_volatility = st.checkbox(
            "Use Volatility Adjustment",
            value=current_volatility,
            help="Adjust position sizes based on asset volatility"
        )
    
    # Check if parameters have changed
    params_changed = (
        new_lookback != current_lookback or
        new_position_count != current_position_count or
        abs(new_threshold - current_threshold) > 0.001 or
        new_rebalance != current_rebalance.lower() or
        new_volatility != current_volatility
    )
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if params_changed:
            st.success("✅ Parameters changed! Click 'Re-run Backtest' to see the impact.")
        else:
            st.info("ℹ️ Adjust parameters above to enable re-running.")
    
    with col2:
        if st.button("🔄 Reset to Current", use_container_width=True, disabled=not params_changed):
            st.rerun()
    
    with col3:
        if st.button("🚀 Re-run Backtest", use_container_width=True, type="primary", disabled=not params_changed):
            # Update configuration and trigger re-run
            _rerun_with_new_params(
                last_params,
                {
                    'lookback_period': new_lookback,
                    'position_count': new_position_count,
                    'absolute_threshold': new_threshold,
                    'rebalance_frequency': new_rebalance,
                    'use_volatility_adjustment': new_volatility
                }
            )
    
    # Parameter comparison table
    if params_changed:
        st.markdown("---")
        st.markdown("#### 📊 Parameter Changes")
        
        changes = []
        if new_lookback != current_lookback:
            changes.append({
                'Parameter': 'Lookback Period',
                'Current': f"{current_lookback} days",
                'New': f"{new_lookback} days",
                'Change': f"{new_lookback - current_lookback:+d} days"
            })
        if new_position_count != current_position_count:
            changes.append({
                'Parameter': 'Position Count',
                'Current': str(current_position_count),
                'New': str(new_position_count),
                'Change': f"{new_position_count - current_position_count:+d}"
            })
        if abs(new_threshold - current_threshold) > 0.001:
            changes.append({
                'Parameter': 'Absolute Threshold',
                'Current': f"{current_threshold:.2%}",
                'New': f"{new_threshold:.2%}",
                'Change': f"{(new_threshold - current_threshold):.2%}"
            })
        if new_rebalance != current_rebalance.lower():
            changes.append({
                'Parameter': 'Rebalance Frequency',
                'Current': current_rebalance.title(),
                'New': new_rebalance.title(),
                'Change': '→'
            })
        if new_volatility != current_volatility:
            changes.append({
                'Parameter': 'Volatility Adjustment',
                'Current': 'Yes' if current_volatility else 'No',
                'New': 'Yes' if new_volatility else 'No',
                'Change': '→'
            })
        
        if changes:
            changes_df = pd.DataFrame(changes)
            st.dataframe(changes_df, use_container_width=True, hide_index=True)


def _rerun_with_new_params(base_params: dict, new_strategy_params: dict):
    """
    Re-run backtest with new parameters.
    
    Args:
        base_params: Base backtest configuration
        new_strategy_params: New strategy parameters to apply
    """
    with st.spinner("🔄 Re-running backtest with new parameters..."):
        try:
            # Import required modules
            from src.backtesting.engine import BacktestEngine
            from src.strategies.dual_momentum import DualMomentumStrategy
            from src.data_sources.multi_source import MultiSourceDataProvider
            
            # Update strategy config
            updated_config = {**base_params.get('strategy_config', {}), **new_strategy_params}
            
            # Create strategy
            strategy = DualMomentumStrategy(updated_config)
            
            # Create backtest engine
            engine = BacktestEngine(
                initial_capital=base_params.get('initial_capital', 100000),
                commission=base_params.get('commission', 0.001),
                slippage=base_params.get('slippage', 0.0005)
            )
            
            # Get price data (try to use cached data if available)
            price_data = st.session_state.get('cached_price_data', {})
            
            if not price_data:
                # Need to fetch fresh data
                data_provider = MultiSourceDataProvider()
                symbols = base_params.get('universe', base_params.get('symbols', []))
                
                for symbol in symbols:
                    try:
                        data = data_provider.fetch_data(
                            symbol,
                            start_date=base_params.get('start_date'),
                            end_date=base_params.get('end_date')
                        )
                        price_data[symbol] = data
                    except Exception as e:
                        st.warning(f"Could not load data for {symbol}: {e}")
                
                # Cache the data
                st.session_state.cached_price_data = price_data
            
            # Get benchmark data if available
            benchmark_data = st.session_state.get('benchmark_data')
            
            # Run backtest
            results = engine.run(
                strategy=strategy,
                price_data=price_data,
                start_date=pd.to_datetime(base_params.get('start_date')),
                end_date=pd.to_datetime(base_params.get('end_date')),
                benchmark_data=benchmark_data
            )
            
            # Update session state
            st.session_state.backtest_results = results
            updated_params = base_params.copy()
            updated_params['strategy_config'] = updated_config
            updated_params['timestamp'] = datetime.now()
            st.session_state.last_backtest_params = updated_params
            
            st.success("✅ Backtest completed! Results updated above.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error running backtest: {str(e)}")
            import traceback
            with st.expander("Show error details"):
                st.code(traceback.format_exc())


def render_export_options(results):
    """Render export and download options."""
    
    st.markdown("### 💾 Export Options")
    
    st.markdown("""
    Download your backtest results in various formats for further analysis or reporting.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Data Exports")
        
        # Export trades
        if hasattr(results, 'trades') and len(results.trades) > 0:
            trades_csv = results.trades.to_csv(index=False)
            st.download_button(
                label="📥 Download Trades (CSV)",
                data=trades_csv,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )
        
        # Export equity curve
        if hasattr(results, 'equity_curve'):
            equity_csv = results.equity_curve.to_csv()
            st.download_button(
                label="📈 Download Equity Curve (CSV)",
                data=equity_csv,
                file_name=f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )
        
        # Export positions
        if hasattr(results, 'positions') and len(results.positions) > 0:
            positions_csv = results.positions.to_csv(index=False)
            st.download_button(
                label="💼 Download Positions (CSV)",
                data=positions_csv,
                file_name=f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width='stretch'
            )
    
    with col2:
        st.markdown("#### 📄 Reports")
        
        # Export metrics as JSON
        metrics_json = json.dumps(results.metrics, indent=2, default=str)
        st.download_button(
            label="📋 Download Metrics (JSON)",
            data=metrics_json,
            file_name=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width='stretch'
        )
        
        # Full report
        report_data = {
            'strategy': st.session_state.get('last_backtest_params', {}),
            'metrics': results.metrics,
            'summary': {
                'total_return': results.total_return,
                'num_trades': results.num_trades,
                'win_rate': results.win_rate
            }
        }
        
        # Add benchmark info if available
        if st.session_state.get('benchmark_symbol'):
            report_data['benchmark'] = {
                'symbol': st.session_state.benchmark_symbol,
                'alpha': results.metrics.get('alpha', 0),
                'beta': results.metrics.get('beta', 0),
                'information_ratio': results.metrics.get('information_ratio', 0),
                'tracking_error': results.metrics.get('tracking_error', 0)
            }
        
        st.download_button(
            label="📑 Download Full Report (JSON)",
            data=json.dumps(report_data, indent=2, default=str),
            file_name=f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width='stretch'
        )
    
    render_section_divider()
    
    # Configuration export
    st.markdown("#### ⚙️ Strategy Configuration")
    
    if 'last_backtest_params' in st.session_state:
        config = st.session_state.last_backtest_params
        config_json = json.dumps(config, indent=2, default=str)
        
        st.code(config_json, language='json')
        
        st.download_button(
            label="📥 Download Configuration",
            data=config_json,
            file_name=f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            width='stretch'
        )
