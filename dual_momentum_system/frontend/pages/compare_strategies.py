"""
Compare Strategies page for the Streamlit dashboard.

Allows side-by-side comparison of multiple backtest results.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils.styling import (
    render_page_header, render_info_box, render_section_divider
)
from frontend.utils.state import clear_comparison


def render():
    """Render the compare strategies page."""
    
    render_page_header(
        "Compare Strategies",
        "Side-by-side analysis of multiple strategy configurations",
        "🔄"
    )
    
    # Check if comparison results exist
    if 'comparison_results' not in st.session_state or len(st.session_state.comparison_results) == 0:
        render_no_comparisons()
        return
    
    # Comparison controls
    render_comparison_controls()
    
    render_section_divider()
    
    # Tabs for different comparisons
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Metrics Comparison",
        "📈 Equity Curves",
        "⚖️ Risk/Return",
        "🔗 Correlation"
    ])
    
    with tab1:
        render_metrics_comparison()
    
    with tab2:
        render_equity_comparison()
    
    with tab3:
        render_risk_return_analysis()
    
    with tab4:
        render_correlation_analysis()


def render_no_comparisons():
    """Render message when no comparisons exist."""
    
    st.markdown("""
    <div class="info-box">
        <h3>ℹ️ No Strategies to Compare</h3>
        <p>You haven't added any strategies for comparison yet. To compare strategies:</p>
        <ol>
            <li>Run a backtest in the <strong>Strategy Builder</strong></li>
            <li>In the <strong>Backtest Results</strong> page, click <strong>Add to Comparison</strong></li>
            <li>Repeat for different strategy configurations</li>
            <li>Return here to see side-by-side comparisons</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def render_comparison_controls():
    """Render controls for managing comparisons."""
    
    st.markdown("### 🎛️ Comparison Controls")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**{len(st.session_state.comparison_results)} strategies** in comparison")
    
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_comparison()
            st.rerun()
    
    with col3:
        if st.button("➕ Add Current", use_container_width=True):
            if 'backtest_results' in st.session_state and st.session_state.backtest_results:
                from datetime import datetime
                from frontend.utils.state import add_to_comparison
                name = f"Strategy {len(st.session_state.comparison_results) + 1}"
                add_to_comparison(st.session_state.backtest_results, name)
                st.success(f"Added {name} to comparison")
                st.rerun()
            else:
                st.warning("No backtest results to add")
    
    # Strategy selector
    strategy_names = [r['name'] for r in st.session_state.comparison_results]
    selected_strategies = st.multiselect(
        "Select strategies to compare",
        strategy_names,
        default=strategy_names[:4] if len(strategy_names) > 4 else strategy_names,
        help="Choose up to 4 strategies for comparison"
    )
    
    st.session_state.selected_for_comparison = selected_strategies


def render_metrics_comparison():
    """Render side-by-side metrics comparison."""
    
    st.markdown("### 📊 Performance Metrics Comparison")
    
    selected = st.session_state.get('selected_for_comparison', [])
    if not selected:
        render_info_box("Select at least one strategy to compare", "info")
        return
    
    # Gather results
    comparison_data = []
    for result_dict in st.session_state.comparison_results:
        if result_dict['name'] in selected:
            result = result_dict['result']
            metrics = result.metrics
            
            comparison_data.append({
                'Strategy': result_dict['name'],
                'Total Return': f"{metrics.get('total_return', 0)*100:.2f}%",
                'Ann. Return': f"{metrics.get('annualized_return', 0)*100:.2f}%",
                'Sharpe Ratio': f"{metrics.get('sharpe_ratio', 0):.2f}",
                'Sortino Ratio': f"{metrics.get('sortino_ratio', 0):.2f}",
                'Max Drawdown': f"{metrics.get('max_drawdown', 0)*100:.2f}%",
                'Volatility': f"{metrics.get('volatility', 0)*100:.2f}%",
                'Calmar Ratio': f"{metrics.get('calmar_ratio', 0):.2f}",
                'Win Rate': f"{metrics.get('win_rate', 0)*100:.1f}%",
                'Num Trades': f"{metrics.get('num_trades', 0):.0f}"
            })
    
    if not comparison_data:
        render_info_box("No data available for selected strategies", "warning")
        return
    
    # Display as table
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    render_section_divider()
    
    # Visual comparison of key metrics
    st.markdown("### 📊 Visual Metrics Comparison")
    
    # Create metrics for visualization
    metrics_for_viz = []
    for result_dict in st.session_state.comparison_results:
        if result_dict['name'] in selected:
            result = result_dict['result']
            metrics = result.metrics
            
            metrics_for_viz.append({
                'Strategy': result_dict['name'],
                'Total Return (%)': metrics.get('total_return', 0) * 100,
                'Sharpe Ratio': metrics.get('sharpe_ratio', 0),
                'Max Drawdown (%)': metrics.get('max_drawdown', 0) * 100,
                'Win Rate (%)': metrics.get('win_rate', 0) * 100
            })
    
    viz_df = pd.DataFrame(metrics_for_viz)
    
    # Create subplots
    col1, col2 = st.columns(2)
    
    with col1:
        # Total Return comparison
        fig = px.bar(
            viz_df,
            x='Strategy',
            y='Total Return (%)',
            title='Total Return Comparison',
            color='Total Return (%)',
            color_continuous_scale='RdYlGn',
            text='Total Return (%)'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Sharpe Ratio comparison
        fig = px.bar(
            viz_df,
            x='Strategy',
            y='Sharpe Ratio',
            title='Sharpe Ratio Comparison',
            color='Sharpe Ratio',
            color_continuous_scale='Blues',
            text='Sharpe Ratio'
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Max Drawdown comparison (negative values)
        fig = px.bar(
            viz_df,
            x='Strategy',
            y='Max Drawdown (%)',
            title='Maximum Drawdown Comparison',
            color='Max Drawdown (%)',
            color_continuous_scale='Reds_r',
            text='Max Drawdown (%)'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        # Win Rate comparison
        fig = px.bar(
            viz_df,
            x='Strategy',
            y='Win Rate (%)',
            title='Win Rate Comparison',
            color='Win Rate (%)',
            color_continuous_scale='Greens',
            text='Win Rate (%)'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def render_equity_comparison():
    """Render overlayed equity curves."""
    
    st.markdown("### 📈 Equity Curves Comparison")
    
    selected = st.session_state.get('selected_for_comparison', [])
    if not selected:
        render_info_box("Select at least one strategy to compare", "info")
        return
    
    # Normalize option
    normalize = st.checkbox(
        "Normalize to 100",
        value=True,
        help="Start all equity curves at 100 for easier comparison"
    )
    
    # Create overlayed chart
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for idx, result_dict in enumerate(st.session_state.comparison_results):
        if result_dict['name'] in selected:
            result = result_dict['result']
            
            if hasattr(result, 'equity_curve'):
                equity = result.equity_curve.copy()
                
                if normalize:
                    equity = (equity / equity.iloc[0]) * 100
                
                equity_df = equity.reset_index()
                equity_df.columns = ['Date', 'Value']
                
                fig.add_trace(go.Scatter(
                    x=equity_df['Date'],
                    y=equity_df['Value'],
                    mode='lines',
                    name=result_dict['name'],
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))
    
    fig.update_layout(
        title="Overlayed Equity Curves",
        xaxis_title="Date",
        yaxis_title="Portfolio Value" + (" (Normalized)" if normalize else " ($)"),
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Drawdown comparison
    render_section_divider()
    st.markdown("### 📉 Drawdown Comparison")
    
    fig = go.Figure()
    
    for idx, result_dict in enumerate(st.session_state.comparison_results):
        if result_dict['name'] in selected:
            result = result_dict['result']
            
            if hasattr(result, 'equity_curve'):
                equity = result.equity_curve
                running_max = equity.cummax()
                drawdown = (equity - running_max) / running_max * 100
                
                dd_df = drawdown.reset_index()
                dd_df.columns = ['Date', 'Drawdown']
                
                fig.add_trace(go.Scatter(
                    x=dd_df['Date'],
                    y=dd_df['Drawdown'],
                    mode='lines',
                    name=result_dict['name'],
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))
    
    fig.update_layout(
        title="Drawdown Comparison",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_return_analysis():
    """Render risk/return scatter plot and analysis."""
    
    st.markdown("### ⚖️ Risk vs Return Analysis")
    
    selected = st.session_state.get('selected_for_comparison', [])
    if not selected:
        render_info_box("Select at least one strategy to compare", "info")
        return
    
    # Gather risk/return data
    risk_return_data = []
    for result_dict in st.session_state.comparison_results:
        if result_dict['name'] in selected:
            result = result_dict['result']
            metrics = result.metrics
            
            risk_return_data.append({
                'Strategy': result_dict['name'],
                'Return': metrics.get('annualized_return', 0) * 100,
                'Risk': metrics.get('volatility', 0) * 100,
                'Sharpe': metrics.get('sharpe_ratio', 0),
                'Max DD': abs(metrics.get('max_drawdown', 0) * 100)
            })
    
    df = pd.DataFrame(risk_return_data)
    
    # Risk/Return scatter plot
    fig = px.scatter(
        df,
        x='Risk',
        y='Return',
        size='Max DD',
        color='Sharpe',
        text='Strategy',
        title='Risk vs Return (Size = Max Drawdown, Color = Sharpe Ratio)',
        labels={
            'Risk': 'Annualized Volatility (%)',
            'Return': 'Annualized Return (%)'
        },
        color_continuous_scale='RdYlGn',
        size_max=50
    )
    
    fig.update_traces(textposition='top center')
    fig.update_layout(height=500)
    
    st.plotly_chart(fig, use_container_width=True)
    
    render_section_divider()
    
    # Efficiency metrics
    st.markdown("### 📊 Risk-Adjusted Performance")
    
    # Calculate efficient frontier-like ranking
    df['Risk_Rank'] = df['Risk'].rank()
    df['Return_Rank'] = df['Return'].rank(ascending=False)
    df['Sharpe_Rank'] = df['Sharpe'].rank(ascending=False)
    df['Efficiency_Score'] = (df['Return_Rank'] + df['Sharpe_Rank']) / 2
    
    display_df = df[['Strategy', 'Return', 'Risk', 'Sharpe', 'Max DD']].sort_values('Sharpe', ascending=False)
    display_df['Return'] = display_df['Return'].apply(lambda x: f"{x:.2f}%")
    display_df['Risk'] = display_df['Risk'].apply(lambda x: f"{x:.2f}%")
    display_df['Sharpe'] = display_df['Sharpe'].apply(lambda x: f"{x:.2f}")
    display_df['Max DD'] = display_df['Max DD'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Best strategy recommendation
    best_sharpe = df.loc[df['Sharpe'].idxmax(), 'Strategy']
    best_return = df.loc[df['Return'].idxmax(), 'Strategy']
    lowest_risk = df.loc[df['Risk'].idxmin(), 'Strategy']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="card" style="background: #e8f5e9;">
            <h4>🏆 Best Risk-Adjusted</h4>
            <p style="font-size: 1.2rem; font-weight: bold; color: #2ca02c;">
                {best_sharpe}
            </p>
            <small>Highest Sharpe Ratio</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="card" style="background: #e3f2fd;">
            <h4>📈 Highest Return</h4>
            <p style="font-size: 1.2rem; font-weight: bold; color: #1f77b4;">
                {best_return}
            </p>
            <small>Maximum Annualized Return</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="card" style="background: #fff3e0;">
            <h4>🛡️ Lowest Risk</h4>
            <p style="font-size: 1.2rem; font-weight: bold; color: #ff9800;">
                {lowest_risk}
            </p>
            <small>Minimum Volatility</small>
        </div>
        """, unsafe_allow_html=True)


def render_correlation_analysis():
    """Render correlation matrix and analysis."""
    
    st.markdown("### 🔗 Returns Correlation Analysis")
    
    selected = st.session_state.get('selected_for_comparison', [])
    if len(selected) < 2:
        render_info_box("Select at least 2 strategies to analyze correlations", "info")
        return
    
    # Gather returns data
    returns_dict = {}
    for result_dict in st.session_state.comparison_results:
        if result_dict['name'] in selected:
            result = result_dict['result']
            if hasattr(result, 'returns'):
                returns_dict[result_dict['name']] = result.returns
    
    if len(returns_dict) < 2:
        render_info_box("Insufficient returns data for correlation analysis", "warning")
        return
    
    # Create returns dataframe
    returns_df = pd.DataFrame(returns_dict)
    
    # Calculate correlation matrix
    corr_matrix = returns_df.corr()
    
    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu_r',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 12},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Strategy Returns Correlation Matrix",
        height=500,
        xaxis=dict(side='bottom')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    render_section_divider()
    
    # Correlation insights
    st.markdown("### 💡 Correlation Insights")
    
    # Find highest and lowest correlations
    corr_values = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_values.append({
                'Pair': f"{corr_matrix.columns[i]} vs {corr_matrix.columns[j]}",
                'Correlation': corr_matrix.iloc[i, j]
            })
    
    if corr_values:
        corr_df = pd.DataFrame(corr_values).sort_values('Correlation', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Highest Correlations")
            high_corr = corr_df.head(3)
            for _, row in high_corr.iterrows():
                st.markdown(f"- **{row['Pair']}**: {row['Correlation']:.3f}")
            
            st.caption("Strategies with high correlation move together")
        
        with col2:
            st.markdown("#### Lowest Correlations")
            low_corr = corr_df.tail(3)
            for _, row in low_corr.iterrows():
                st.markdown(f"- **{row['Pair']}**: {row['Correlation']:.3f}")
            
            st.caption("Strategies with low correlation provide diversification")
    
    # Diversification potential
    avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
    
    if avg_corr < 0.5:
        diversification_msg = "✅ Good diversification potential (low average correlation)"
        box_type = "success"
    elif avg_corr < 0.7:
        diversification_msg = "⚠️ Moderate diversification potential"
        box_type = "warning"
    else:
        diversification_msg = "❌ Limited diversification potential (high correlation)"
        box_type = "error"
    
    render_info_box(
        f"{diversification_msg} - Average correlation: {avg_corr:.3f}",
        box_type
    )
