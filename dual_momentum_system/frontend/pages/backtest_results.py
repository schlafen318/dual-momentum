"""
Backtest Results page for the Streamlit dashboard.

Displays comprehensive performance metrics, charts, and trade analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

from frontend.utils.styling import (
    render_page_header, render_metric_card, render_info_box, render_section_divider
)
from frontend.utils.state import add_to_comparison


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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "💹 Charts",
        "📋 Trades",
        "📊 Rolling Metrics",
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
    col1, col2, col3 = st.columns(3)
    
    with col1:
        strategy_name = f"{st.session_state.get('strategy_type', 'Strategy')} - {datetime.now().strftime('%H:%M:%S')}"
        if st.button("➕ Add to Comparison", width='stretch'):
            add_to_comparison(results, strategy_name)
            st.success(f"Added to comparison list!")
    
    with col2:
        if st.button("🔄 Run New Backtest", width='stretch'):
            st.info("Navigate to Strategy Builder to configure a new backtest")
    
    with col3:
        if st.button("📥 Download Report", width='stretch'):
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
        if has_benchmark:
            try:
                benchmark_data = st.session_state.benchmark_data
                benchmark_prices = benchmark_data.data['close']
                
                # Normalize benchmark to start at same value as portfolio
                initial_capital = results.initial_capital
                benchmark_normalized = benchmark_prices / benchmark_prices.iloc[0] * initial_capital
                
                # Align with strategy dates
                benchmark_aligned = benchmark_normalized.reindex(equity_df['Date']).fillna(method='ffill')
                
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
    if has_benchmark:
        st.markdown("#### Cumulative Returns Comparison")
        
        try:
            strategy_returns = results.returns
            benchmark_data = st.session_state.benchmark_data
            benchmark_prices = benchmark_data.data['close']
            benchmark_returns = benchmark_prices.pct_change().dropna()
            
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
        # Calculate drawdown
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
            name='Drawdown',
            line=dict(color='#d62728', width=2),
            fill='tozeroy',
            fillcolor='rgba(214, 39, 40, 0.3)'
        ))
        
        fig.update_layout(
            title="Portfolio Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    
    render_section_divider()
    
    # Monthly returns heatmap
    st.markdown("#### Monthly Returns Heatmap")
    
    if hasattr(results, 'returns'):
        try:
            # Convert returns to monthly
            monthly_returns = results.returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            
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
