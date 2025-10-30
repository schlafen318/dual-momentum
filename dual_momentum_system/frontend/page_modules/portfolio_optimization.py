"""
Portfolio Optimization page for the dashboard.

Provides interface for comparing multiple portfolio construction methods
beyond mean-variance optimization.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.portfolio_optimization import (
    compare_portfolio_methods,
    get_available_methods,
    get_method_description,
)
from src.data_sources import get_default_data_source


def render():
    """Render the portfolio optimization page."""
    
    st.title("💼 Portfolio Optimization")
    
    # Check if we have pre-populated data from Strategy Builder
    if st.session_state.get('selected_symbols') and not st.session_state.get('_portfolio_opt_initialized'):
        st.info("""
        ✨ **Assets loaded from Strategy Builder!**
        
        Your selected assets and parameters have been automatically populated from the Strategy Builder page.
        Review the configuration below and adjust if needed.
        """)
        st.session_state._portfolio_opt_initialized = True
    
    st.markdown("""
    Compare **7 portfolio construction methods** to find the optimal allocation for your assets.
    
    **Methods Available:**
    - Equal Weight, Inverse Volatility, Minimum Variance
    - Maximum Sharpe, Risk Parity, Maximum Diversification
    - Hierarchical Risk Parity (HRP)
    """)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "⚙️ Configuration",
        "🚀 Run Optimization",
        "📊 Results"
    ])
    
    with tab1:
        render_configuration_tab()
    
    with tab2:
        render_optimization_tab()
    
    with tab3:
        render_results_tab()


def render_configuration_tab():
    """Render the configuration tab."""
    
    st.header("Portfolio Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Asset Selection")
        
        # Check if we have symbols from Strategy Builder
        strategy_builder_symbols = st.session_state.get('selected_symbols', [])
        has_imported_symbols = len(strategy_builder_symbols) > 0
        
        # Asset universe selection
        if has_imported_symbols:
            universe_options = ["From Strategy Builder", "Default (Multi-Asset)", "Custom"]
            default_option = "From Strategy Builder"
            default_value = '\n'.join(strategy_builder_symbols)
        else:
            universe_options = ["Default (Multi-Asset)", "Custom"]
            default_option = "Default (Multi-Asset)"
            default_value = "SPY\nAGG\nGLD\nTLT"
        
        universe_option = st.radio(
            "Select Universe",
            universe_options,
            index=0 if has_imported_symbols else 0,
            horizontal=True
        )
        
        if universe_option == "From Strategy Builder":
            # Show imported symbols in a text area (editable)
            universe_input = st.text_area(
                "Assets from Strategy Builder (edit if needed)",
                value=default_value,
                height=150,
                help="These assets were imported from Strategy Builder"
            )
            symbols = [s.strip().upper() for s in universe_input.replace(',', '\n').split('\n') if s.strip()]
            
            # Show info about import
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"✓ Imported {len(strategy_builder_symbols)} assets from Strategy Builder")
            with col_b:
                if st.button("🔄 Refresh from Strategy Builder", help="Reload symbols from Strategy Builder"):
                    st.rerun()
        
        elif universe_option == "Custom":
            universe_input = st.text_area(
                "Enter symbols (one per line or comma-separated)",
                value="SPY\nAGG\nGLD\nTLT",
                height=150,
                help="Enter ticker symbols"
            )
            # Parse symbols
            symbols = [s.strip().upper() for s in universe_input.replace(',', '\n').split('\n') if s.strip()]
        else:  # Default
            symbols = ['SPY', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD']
        
        st.session_state.portfolio_opt_symbols = symbols
        
        # Display selected symbols
        st.success(f"Selected {len(symbols)} assets: {', '.join(symbols)}")
        
        # Date range
        st.markdown("---")
        st.subheader("Date Range")
        
        # Check for dates from Strategy Builder
        strategy_builder_start = st.session_state.get('start_date')
        strategy_builder_end = st.session_state.get('end_date')
        
        end_date = datetime.now().date()
        
        # Use Strategy Builder dates if available, otherwise default to 3 years
        if strategy_builder_start and strategy_builder_end:
            # Convert to date if datetime
            if isinstance(strategy_builder_start, datetime):
                strategy_builder_start = strategy_builder_start.date()
            if isinstance(strategy_builder_end, datetime):
                strategy_builder_end = strategy_builder_end.date()
            default_start = strategy_builder_start
            default_end = strategy_builder_end
            
            if has_imported_symbols:
                st.caption(f"📅 Using date range from Strategy Builder: {default_start} to {default_end}")
        else:
            default_start = end_date - timedelta(days=3*365)  # 3 years
            default_end = end_date
        
        date_range = st.date_input(
            "Historical Period",
            value=(default_start, default_end),
            help="Longer periods produce more robust estimates"
        )
        
        if len(date_range) == 2:
            st.session_state.portfolio_opt_start_date = date_range[0]
            st.session_state.portfolio_opt_end_date = date_range[1]
            
            duration_years = (date_range[1] - date_range[0]).days / 365.25
            st.caption(f"📊 Analysis period: {duration_years:.1f} years")
    
    with col2:
        st.subheader("Optimization Settings")
        
        # Method selection
        st.markdown("**Select Methods to Compare**")
        
        all_methods = get_available_methods()
        
        # Create two columns for checkboxes
        col_a, col_b = st.columns(2)
        
        selected_methods = []
        
        with col_a:
            if st.checkbox("Equal Weight", value=True):
                selected_methods.append('equal_weight')
            if st.checkbox("Inverse Volatility", value=True):
                selected_methods.append('inverse_volatility')
            if st.checkbox("Minimum Variance", value=True):
                selected_methods.append('minimum_variance')
            if st.checkbox("Maximum Sharpe", value=True):
                selected_methods.append('maximum_sharpe')
        
        with col_b:
            if st.checkbox("Risk Parity", value=True):
                selected_methods.append('risk_parity')
            if st.checkbox("Max Diversification", value=True):
                selected_methods.append('maximum_diversification')
            if st.checkbox("HRP", value=True):
                selected_methods.append('hierarchical_risk_parity')
        
        st.session_state.portfolio_opt_methods = selected_methods
        
        if not selected_methods:
            st.warning("⚠️ Please select at least one method")
        else:
            st.info(f"✓ Selected {len(selected_methods)} method(s)")
        
        # Constraints
        st.markdown("---")
        st.markdown("**Portfolio Constraints**")
        
        col_min, col_max = st.columns(2)
        
        with col_min:
            min_weight = st.number_input(
                "Min Weight (%)",
                min_value=0.0,
                max_value=50.0,
                value=0.0,
                step=1.0,
                help="Minimum allocation per asset"
            ) / 100
        
        with col_max:
            max_weight = st.number_input(
                "Max Weight (%)",
                min_value=10.0,
                max_value=100.0,
                value=50.0,
                step=5.0,
                help="Maximum allocation per asset"
            ) / 100
        
        st.session_state.portfolio_opt_min_weight = min_weight
        st.session_state.portfolio_opt_max_weight = max_weight
        
        # Risk-free rate
        risk_free_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Annual risk-free rate for Sharpe ratio calculation"
        ) / 100
        
        st.session_state.portfolio_opt_risk_free_rate = risk_free_rate


def render_optimization_tab():
    """Render the optimization execution tab."""
    
    st.header("Run Portfolio Optimization")
    
    # Check if configuration is complete
    if 'portfolio_opt_symbols' not in st.session_state or not st.session_state.portfolio_opt_symbols:
        st.warning("⚠️ Please configure assets in the Configuration tab first.")
        return
    
    if 'portfolio_opt_methods' not in st.session_state or not st.session_state.portfolio_opt_methods:
        st.warning("⚠️ Please select at least one optimization method in the Configuration tab.")
        return
    
    # Display configuration summary
    st.subheader("Configuration Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Assets", len(st.session_state.portfolio_opt_symbols))
        symbols_str = ', '.join(st.session_state.portfolio_opt_symbols[:3])
        if len(st.session_state.portfolio_opt_symbols) > 3:
            symbols_str += f", +{len(st.session_state.portfolio_opt_symbols)-3} more"
        st.caption(symbols_str)
    
    with col2:
        st.metric("Methods", len(st.session_state.portfolio_opt_methods))
        st.caption("Comparison methods")
    
    with col3:
        start_date = st.session_state.get('portfolio_opt_start_date', 'N/A')
        end_date = st.session_state.get('portfolio_opt_end_date', 'N/A')
        if start_date != 'N/A' and end_date != 'N/A':
            duration = (end_date - start_date).days / 365.25
            st.metric("Period", f"{duration:.1f} years")
        else:
            st.metric("Period", "Not set")
    
    st.markdown("---")
    
    # Method descriptions
    with st.expander("📖 View Method Descriptions"):
        for method in st.session_state.portfolio_opt_methods:
            st.markdown(f"**{method.replace('_', ' ').title()}**")
            st.write(get_method_description(method))
            st.markdown("")
    
    st.markdown("---")
    
    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            run_optimization()


def run_optimization():
    """Execute the portfolio optimization."""
    
    try:
        with st.spinner("Running portfolio optimization... This may take a minute."):
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Loading price data...")
            progress_bar.progress(10)
            
            # Get configuration
            symbols = st.session_state.portfolio_opt_symbols
            start_date = st.session_state.portfolio_opt_start_date
            end_date = st.session_state.portfolio_opt_end_date
            methods = st.session_state.portfolio_opt_methods
            min_weight = st.session_state.portfolio_opt_min_weight
            max_weight = st.session_state.portfolio_opt_max_weight
            risk_free_rate = st.session_state.portfolio_opt_risk_free_rate
            
            # Load data
            data_provider = get_default_data_source()
            
            price_data = {}
            for i, symbol in enumerate(symbols):
                try:
                    data = data_provider.fetch_data(
                        symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    # data is already a DataFrame, no .data attribute needed
                    if data is not None and not data.empty:
                        price_data[symbol] = data
                    else:
                        st.warning(f"Could not load data for {symbol}: Empty data returned")
                    progress = 10 + int(30 * (i + 1) / len(symbols))
                    progress_bar.progress(progress)
                except Exception as e:
                    st.warning(f"Could not load data for {symbol}: {e}")
                    import traceback
                    st.caption(f"Debug info: {traceback.format_exc()}")
            
            if not price_data:
                st.error("❌ No price data loaded. Please check your symbols and date range.")
                return
            
            status_text.text(f"Loaded data for {len(price_data)} assets")
            progress_bar.progress(40)
            
            # Calculate returns
            status_text.text("Calculating returns...")
            returns_df = pd.DataFrame({
                symbol: data['close'].pct_change()
                for symbol, data in price_data.items()
            }).dropna()
            
            progress_bar.progress(50)
            
            # Run optimization
            status_text.text(f"Running {len(methods)} optimization method(s)...")
            
            comparison = compare_portfolio_methods(
                returns=returns_df,
                methods=methods,
                min_weight=min_weight,
                max_weight=max_weight,
                risk_free_rate=risk_free_rate,
                verbose=False,
            )
            
            progress_bar.progress(90)
            
            # Store results
            st.session_state.portfolio_opt_comparison = comparison
            st.session_state.portfolio_opt_returns = returns_df
            st.session_state.portfolio_opt_completed = True
            
            progress_bar.progress(100)
            status_text.text("Optimization complete!")
            
            st.success("✅ Portfolio optimization completed successfully!")
            st.balloons()
            
            # Auto-navigate to results
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error during optimization: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_results_tab():
    """Render the results tab."""
    
    st.header("Optimization Results")
    
    if 'portfolio_opt_comparison' not in st.session_state or not st.session_state.portfolio_opt_completed:
        st.info("No optimization results yet. Configure and run optimization first.")
        return
    
    comparison = st.session_state.portfolio_opt_comparison
    
    # Summary metrics
    st.subheader("🏆 Best Methods")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Best Sharpe Ratio**")
        best_sharpe_method = comparison.best_sharpe_method.replace('_', ' ').title()
        best_sharpe_score = comparison.results[comparison.best_sharpe_method].sharpe_ratio
        st.success(f"**{best_sharpe_method}**")
        st.metric("Sharpe Ratio", f"{best_sharpe_score:.4f}")
    
    with col2:
        st.markdown("**Best Diversification**")
        best_div_method = comparison.best_diversification_method.replace('_', ' ').title()
        best_div_score = comparison.results[comparison.best_diversification_method].diversification_ratio
        st.success(f"**{best_div_method}**")
        st.metric("Diversification Ratio", f"{best_div_score:.4f}")
    
    with col3:
        st.markdown("**Lowest Volatility**")
        low_vol_method = comparison.lowest_volatility_method.replace('_', ' ').title()
        low_vol_score = comparison.results[comparison.lowest_volatility_method].expected_volatility
        st.success(f"**{low_vol_method}**")
        # expected_volatility is already annualized from base.py
        st.metric("Volatility", f"{low_vol_score*100:.2f}% (annual)")
    
    st.markdown("---")
    
    # Comparison table
    st.subheader("📊 Method Comparison")
    
    # Format comparison metrics for display
    display_df = comparison.comparison_metrics.copy()
    
    # Convert to percentage (values are already annualized from base.py)
    if 'expected_return' in display_df.columns:
        display_df['annual_return'] = display_df['expected_return'] * 100  # Already annualized, just convert to %
    if 'expected_volatility' in display_df.columns:
        display_df['annual_volatility'] = display_df['expected_volatility'] * 100  # Already annualized, just convert to %
    
    # Select and order columns
    display_cols = ['method']
    if 'annual_return' in display_df.columns:
        display_cols.append('annual_return')
    if 'annual_volatility' in display_df.columns:
        display_cols.append('annual_volatility')
    if 'sharpe_ratio' in display_df.columns:
        display_cols.append('sharpe_ratio')
    if 'diversification_ratio' in display_df.columns:
        display_cols.append('diversification_ratio')
    
    display_df = display_df[display_cols]
    
    # Rename columns
    display_df.columns = ['Method', 'Annual Return (%)', 'Annual Volatility (%)', 
                          'Sharpe Ratio', 'Diversification Ratio']
    
    # Format numbers
    display_df['Annual Return (%)'] = display_df['Annual Return (%)'].map('{:.2f}'.format)
    display_df['Annual Volatility (%)'] = display_df['Annual Volatility (%)'].map('{:.2f}'.format)
    display_df['Sharpe Ratio'] = display_df['Sharpe Ratio'].map('{:.4f}'.format)
    display_df['Diversification Ratio'] = display_df['Diversification Ratio'].map('{:.4f}'.format)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Portfolio weights
    st.subheader("💼 Portfolio Weights")
    
    weights_df = comparison.get_weights_df()
    
    # Display as percentages
    weights_display = (weights_df * 100).round(2)
    
    st.dataframe(weights_display, use_container_width=True)
    
    st.markdown("---")
    
    # Visualizations
    st.subheader("📈 Visual Analysis")
    
    # Tabs for different visualizations
    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
        "Sharpe Comparison",
        "Weights Heatmap",
        "Risk-Return",
        "Weight Distribution"
    ])
    
    with viz_tab1:
        plot_sharpe_comparison(comparison)
    
    with viz_tab2:
        plot_weights_heatmap(comparison)
    
    with viz_tab3:
        plot_risk_return(comparison)
    
    with viz_tab4:
        plot_weight_distribution(comparison)
    
    st.markdown("---")
    
    # Detailed method results
    st.subheader("🔍 Detailed Results by Method")
    
    method_to_view = st.selectbox(
        "Select Method",
        options=list(comparison.results.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if method_to_view:
        result = comparison.results[method_to_view]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Performance Metrics**")
            # Values are already annualized from base.py, just convert to percentage
            st.metric("Expected Return", f"{result.expected_return*100:.2f}% (annual)")
            st.metric("Expected Volatility", f"{result.expected_volatility*100:.2f}% (annual)")
            st.metric("Sharpe Ratio", f"{result.sharpe_ratio:.4f}")
            st.metric("Diversification Ratio", f"{result.diversification_ratio:.4f}")
        
        with col2:
            st.markdown("**Portfolio Weights**")
            weights_series = pd.Series(result.weights)
            weights_pct = (weights_series * 100).round(2)
            for asset, weight in weights_pct.items():
                st.write(f"{asset}: {weight:.2f}%")
        
        # Risk contributions (if available)
        if result.risk_contributions:
            st.markdown("**Risk Contributions**")
            risk_contrib_df = pd.DataFrame({
                'Asset': list(result.risk_contributions.keys()),
                'Risk Contribution (%)': [v * 100 for v in result.risk_contributions.values()]
            })
            
            fig = go.Figure(data=[
                go.Bar(
                    x=risk_contrib_df['Asset'],
                    y=risk_contrib_df['Risk Contribution (%)'],
                    marker_color='steelblue'
                )
            ])
            
            fig.update_layout(
                title=f"Risk Contributions - {method_to_view.replace('_', ' ').title()}",
                xaxis_title="Asset",
                yaxis_title="Risk Contribution (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Download results
    st.subheader("💾 Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download comparison CSV
        csv_comparison = comparison.comparison_metrics.to_csv(index=False)
        st.download_button(
            label="📥 Comparison CSV",
            data=csv_comparison,
            file_name=f"portfolio_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Download weights CSV
        csv_weights = comparison.get_weights_df().to_csv()
        st.download_button(
            label="📥 Weights CSV",
            data=csv_weights,
            file_name=f"portfolio_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Download summary JSON
        summary = comparison.get_summary()
        json_summary = json.dumps(summary, indent=2)
        st.download_button(
            label="📥 Summary JSON",
            data=json_summary,
            file_name=f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def plot_sharpe_comparison(comparison):
    """Plot Sharpe ratio comparison."""
    
    comparison_df = comparison.comparison_metrics
    
    fig = go.Figure()
    
    # Highlight best method
    colors = ['green' if method == comparison.best_sharpe_method.replace('_', ' ').title() 
              else 'steelblue' for method in comparison_df['method']]
    
    fig.add_trace(go.Bar(
        x=comparison_df['method'],
        y=comparison_df['sharpe_ratio'],
        marker_color=colors,
        text=comparison_df['sharpe_ratio'].round(4),
        textposition='outside',
    ))
    
    fig.update_layout(
        title="Sharpe Ratio by Optimization Method",
        xaxis_title="Method",
        yaxis_title="Sharpe Ratio",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_weights_heatmap(comparison):
    """Plot portfolio weights heatmap."""
    
    weights_df = comparison.get_weights_df()
    
    # Convert to percentages
    weights_pct = weights_df * 100
    
    fig = go.Figure(data=go.Heatmap(
        z=weights_pct.values,
        x=weights_pct.columns,
        y=weights_pct.index,
        colorscale='RdYlGn',
        text=weights_pct.values.round(1),
        texttemplate='%{text}%',
        textfont={"size": 10},
        colorbar=dict(title="Weight (%)")
    ))
    
    fig.update_layout(
        title="Portfolio Weights by Method",
        xaxis_title="Optimization Method",
        yaxis_title="Asset",
        height=max(400, len(weights_df) * 40)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_risk_return(comparison):
    """Plot risk-return scatter."""
    
    comparison_df = comparison.comparison_metrics
    
    fig = go.Figure()
    
    for idx, row in comparison_df.iterrows():
        # Convert to percentage (values are already annualized from base.py)
        ret = row['expected_return'] * 100
        vol = row['expected_volatility'] * 100
        method = row['method']
        
        # Highlight best Sharpe
        if method == comparison.best_sharpe_method.replace('_', ' ').title():
            fig.add_trace(go.Scatter(
                x=[vol],
                y=[ret],
                mode='markers+text',
                name=method,
                marker=dict(size=20, color='green', symbol='star'),
                text=[method],
                textposition='top center',
                textfont=dict(size=12, color='green')
            ))
        else:
            fig.add_trace(go.Scatter(
                x=[vol],
                y=[ret],
                mode='markers+text',
                name=method,
                marker=dict(size=12),
                text=[method],
                textposition='top center',
                textfont=dict(size=10)
            ))
    
    fig.update_layout(
        title="Risk-Return Profile",
        xaxis_title="Annual Volatility (%)",
        yaxis_title="Annual Return (%)",
        height=600,
        showlegend=False,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_weight_distribution(comparison):
    """Plot weight distribution by method."""
    
    weights_df = comparison.get_weights_df()
    
    # Transpose for plotting
    weights_pct = (weights_df * 100).T
    
    fig = go.Figure()
    
    for asset in weights_pct.columns:
        fig.add_trace(go.Bar(
            name=asset,
            x=weights_pct.index,
            y=weights_pct[asset],
        ))
    
    fig.update_layout(
        title="Portfolio Weight Distribution by Method",
        xaxis_title="Optimization Method",
        yaxis_title="Weight (%)",
        barmode='stack',
        height=500,
        legend=dict(
            title="Asset",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    render()
