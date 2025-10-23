"""
Hyperparameter Tuning page for the dashboard.

Provides interface for optimizing strategy parameters using various
optimization methods (grid search, random search, Bayesian optimization).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    ParameterSpace,
    create_default_param_space,
)
from src.strategies.dual_momentum import DualMomentumStrategy
from src.data_sources.multi_source import MultiSourceDataProvider
from src.backtesting.utils import ensure_safe_asset_data


def render():
    """Render the hyperparameter tuning page."""
    
    st.title("🎯 Hyperparameter Tuning")
    st.markdown("""
    Optimize strategy parameters to maximize performance metrics using various optimization methods.
    """)
    
    # Create tabs for different sections
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
    
    st.header("Optimization Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backtest Settings")
        
        # Date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=5*365)  # 5 years default
        
        date_range = st.date_input(
            "Backtest Period",
            value=(start_date, end_date),
            help="Select the date range for backtesting"
        )
        
        if len(date_range) == 2:
            st.session_state.tune_start_date = date_range[0]
            st.session_state.tune_end_date = date_range[1]
        
        # Initial capital
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000.0,
            value=100000.0,
            step=10000.0,
            help="Starting portfolio value"
        )
        st.session_state.tune_initial_capital = initial_capital
        
        # Transaction costs
        commission = st.number_input(
            "Commission (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01,
            help="Commission rate per trade"
        ) / 100
        st.session_state.tune_commission = commission
        
        slippage = st.number_input(
            "Slippage (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.05,
            step=0.01,
            help="Slippage rate per trade"
        ) / 100
        st.session_state.tune_slippage = slippage
        
        # Benchmark
        benchmark_symbol = st.selectbox(
            "Benchmark",
            options=["SPY", "QQQ", "AGG", "None"],
            index=0,
            help="Benchmark for comparison"
        )
        st.session_state.tune_benchmark = None if benchmark_symbol == "None" else benchmark_symbol
    
    with col2:
        st.subheader("Optimization Settings")
        
        # Optimization method
        optimization_method = st.selectbox(
            "Optimization Method",
            options=["Grid Search", "Random Search", "Bayesian Optimization"],
            help="""
            - **Grid Search**: Exhaustive search over all parameter combinations
            - **Random Search**: Random sampling from parameter space
            - **Bayesian Optimization**: Smart search using probabilistic models
            """
        )
        st.session_state.tune_method = optimization_method
        
        # Optimization metric
        metric = st.selectbox(
            "Optimization Metric",
            options=[
                "sharpe_ratio",
                "sortino_ratio",
                "calmar_ratio",
                "annual_return",
                "total_return",
                "max_drawdown",
            ],
            index=0,
            help="Metric to optimize"
        )
        st.session_state.tune_metric = metric
        
        # Higher is better?
        higher_is_better = metric != "max_drawdown"
        st.session_state.tune_higher_is_better = higher_is_better
        
        if higher_is_better:
            st.success(f"Maximizing {metric}")
        else:
            st.info(f"Minimizing {metric} (less negative is better)")
        
        # Number of trials (for random/Bayesian)
        if optimization_method != "Grid Search":
            n_trials = st.number_input(
                "Number of Trials",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="Number of parameter combinations to try"
            )
            st.session_state.tune_n_trials = n_trials
        
        # Random seed
        use_random_seed = st.checkbox("Use Random Seed", value=True)
        if use_random_seed:
            random_seed = st.number_input(
                "Random Seed",
                min_value=0,
                value=42,
                help="For reproducible results"
            )
            st.session_state.tune_random_seed = random_seed
        else:
            st.session_state.tune_random_seed = None
    
    # Parameter Space Configuration
    st.subheader("Parameter Space")
    
    st.markdown("""
    Define the range or discrete values for each parameter to tune.
    """)
    
    # Initialize parameter space in session state
    if 'tune_param_space' not in st.session_state:
        st.session_state.tune_param_space = []
    
    # Add parameter button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        if st.button("➕ Add Parameter", use_container_width=True):
            st.session_state.tune_param_space.append({
                'name': 'lookback_period',
                'type': 'int',
                'values': [126, 189, 252, 315],
            })
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.session_state.tune_param_space = [
                {'name': 'lookback_period', 'type': 'int', 'values': [63, 126, 189, 252, 315]},
                {'name': 'position_count', 'type': 'int', 'values': [1, 2, 3]},
                {'name': 'absolute_threshold', 'type': 'float', 'values': [0.0, 0.01, 0.02]},
            ]
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.tune_param_space = []
    
    # Display and edit parameters
    if st.session_state.tune_param_space:
        st.markdown("---")
        
        for idx, param in enumerate(st.session_state.tune_param_space):
            with st.expander(f"Parameter {idx + 1}: {param.get('name', 'Unnamed')}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    param_name = st.selectbox(
                        "Parameter Name",
                        options=[
                            "lookback_period",
                            "position_count",
                            "absolute_threshold",
                            "use_volatility_adjustment",
                            "rebalance_frequency",
                        ],
                        key=f"param_name_{idx}",
                        index=0 if 'name' not in param else [
                            "lookback_period",
                            "position_count",
                            "absolute_threshold",
                            "use_volatility_adjustment",
                            "rebalance_frequency",
                        ].index(param['name']) if param['name'] in [
                            "lookback_period",
                            "position_count",
                            "absolute_threshold",
                            "use_volatility_adjustment",
                            "rebalance_frequency",
                        ] else 0
                    )
                    param['name'] = param_name
                
                with col2:
                    param_type = st.selectbox(
                        "Type",
                        options=["int", "float", "categorical"],
                        key=f"param_type_{idx}",
                        index=["int", "float", "categorical"].index(param.get('type', 'int'))
                    )
                    param['type'] = param_type
                
                with col3:
                    if st.button("🗑️", key=f"delete_param_{idx}", help="Delete this parameter"):
                        st.session_state.tune_param_space.pop(idx)
                        st.rerun()
                
                # Values input
                if param_type == "categorical":
                    values_str = st.text_input(
                        "Values (comma-separated)",
                        value=", ".join(str(v) for v in param.get('values', [])),
                        key=f"param_values_{idx}",
                        help="e.g., monthly, weekly, daily"
                    )
                    param['values'] = [v.strip() for v in values_str.split(',') if v.strip()]
                
                elif param_type == "int":
                    values_str = st.text_input(
                        "Values (comma-separated integers)",
                        value=", ".join(str(v) for v in param.get('values', [])),
                        key=f"param_values_{idx}",
                        help="e.g., 126, 189, 252, 315"
                    )
                    try:
                        param['values'] = [int(v.strip()) for v in values_str.split(',') if v.strip()]
                    except ValueError:
                        st.error("Please enter valid integers")
                        param['values'] = []
                
                elif param_type == "float":
                    values_str = st.text_input(
                        "Values (comma-separated floats)",
                        value=", ".join(str(v) for v in param.get('values', [])),
                        key=f"param_values_{idx}",
                        help="e.g., 0.0, 0.01, 0.02, 0.05"
                    )
                    try:
                        param['values'] = [float(v.strip()) for v in values_str.split(',') if v.strip()]
                    except ValueError:
                        st.error("Please enter valid floats")
                        param['values'] = []
    
    else:
        st.info("No parameters defined. Click '➕ Add Parameter' or '🔄 Reset to Defaults' to get started.")
    
    # Show estimated number of combinations for grid search
    if st.session_state.tune_method == "Grid Search" and st.session_state.tune_param_space:
        n_combinations = 1
        for param in st.session_state.tune_param_space:
            n_combinations *= len(param.get('values', []))
        
        st.info(f"📊 Grid Search will evaluate **{n_combinations}** parameter combinations")
        
        if n_combinations > 100:
            st.warning(
                "⚠️ Large number of combinations may take a long time. "
                "Consider using Random Search or Bayesian Optimization."
            )


def render_optimization_tab():
    """Render the optimization execution tab."""
    
    st.header("Run Optimization")
    
    # Check if configuration is complete
    if 'tune_param_space' not in st.session_state or not st.session_state.tune_param_space:
        st.warning("⚠️ Please configure parameter space in the Configuration tab first.")
        return
    
    # Display configuration summary
    st.subheader("Configuration Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Method", st.session_state.get('tune_method', 'N/A'))
        st.metric("Metric", st.session_state.get('tune_metric', 'N/A'))
    
    with col2:
        start_date = st.session_state.get('tune_start_date', 'N/A')
        end_date = st.session_state.get('tune_end_date', 'N/A')
        st.metric("Period", f"{start_date} to {end_date}")
        st.metric("Initial Capital", f"${st.session_state.get('tune_initial_capital', 0):,.0f}")
    
    with col3:
        st.metric("Parameters", len(st.session_state.tune_param_space))
        if st.session_state.get('tune_method') != "Grid Search":
            st.metric("Trials", st.session_state.get('tune_n_trials', 'N/A'))
    
    st.markdown("---")
    
    # Asset universe selection
    st.subheader("Asset Universe")
    
    universe_option = st.radio(
        "Select Universe",
        options=["Default (SPY, EFA, EEM, AGG, TLT, GLD)", "Custom"],
        horizontal=True
    )
    
    if universe_option == "Custom":
        universe_input = st.text_input(
            "Enter symbols (comma-separated)",
            value="SPY, EFA, EEM, AGG, TLT, GLD",
            help="Enter ticker symbols separated by commas"
        )
        universe = [s.strip().upper() for s in universe_input.split(',') if s.strip()]
    else:
        universe = ["SPY", "EFA", "EEM", "AGG", "TLT", "GLD"]
    
    st.session_state.tune_universe = universe
    
    # Safe asset
    safe_asset = st.selectbox(
        "Safe Asset",
        options=["AGG", "TLT", "SHY", "BIL", "None"],
        index=0,
        help="Asset to hold during defensive periods"
    )
    st.session_state.tune_safe_asset = None if safe_asset == "None" else safe_asset
    
    st.markdown("---")
    
    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Start Optimization", type="primary", use_container_width=True):
            run_optimization()


def run_optimization():
    """Execute the hyperparameter optimization."""
    
    try:
        with st.spinner("Running optimization... This may take several minutes."):
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Loading data...")
            progress_bar.progress(10)
            
            # Load price data
            start_date = st.session_state.tune_start_date
            end_date = st.session_state.tune_end_date
            universe = st.session_state.tune_universe
            
            data_provider = MultiSourceDataProvider()
            
            # Add some buffer for lookback period
            buffer_days = 400
            data_start = pd.to_datetime(start_date) - timedelta(days=buffer_days)
            
            price_data = {}
            for symbol in universe:
                try:
                    data = data_provider.fetch_data(
                        symbol,
                        start_date=data_start,
                        end_date=end_date
                    )
                    price_data[symbol] = data
                except Exception as e:
                    st.warning(f"Could not load data for {symbol}: {e}")
            
            if not price_data:
                st.error("❌ No price data loaded. Please check your symbols and date range.")
                return
            
            progress_bar.progress(30)
            status_text.text(f"Loaded data for {len(price_data)} assets")
            
            # Ensure safe asset data
            safe_asset = st.session_state.tune_safe_asset
            if safe_asset and safe_asset not in price_data:
                try:
                    data = data_provider.fetch_data(
                        safe_asset,
                        start_date=data_start,
                        end_date=end_date
                    )
                    price_data[safe_asset] = data
                except Exception as e:
                    st.warning(f"Could not load safe asset {safe_asset}: {e}")
            
            # Load benchmark data
            benchmark_data = None
            if st.session_state.tune_benchmark:
                try:
                    benchmark_data = data_provider.fetch_data(
                        st.session_state.tune_benchmark,
                        start_date=data_start,
                        end_date=end_date
                    )
                except Exception as e:
                    st.warning(f"Could not load benchmark data: {e}")
            
            progress_bar.progress(50)
            status_text.text("Setting up optimization...")
            
            # Create backtest engine
            engine = BacktestEngine(
                initial_capital=st.session_state.tune_initial_capital,
                commission=st.session_state.tune_commission,
                slippage=st.session_state.tune_slippage,
            )
            
            # Create base config
            base_config = {
                'safe_asset': safe_asset,
                'rebalance_frequency': 'monthly',
                'universe': universe,
            }
            
            # Convert parameter space
            param_spaces = []
            for param in st.session_state.tune_param_space:
                ps = ParameterSpace(
                    name=param['name'],
                    param_type=param['type'],
                    values=param.get('values', [])
                )
                param_spaces.append(ps)
            
            # Create tuner
            tuner = HyperparameterTuner(
                strategy_class=DualMomentumStrategy,
                backtest_engine=engine,
                price_data=price_data,
                base_config=base_config,
                start_date=pd.to_datetime(start_date),
                end_date=pd.to_datetime(end_date),
                benchmark_data=benchmark_data,
            )
            
            progress_bar.progress(60)
            status_text.text("Running optimization trials...")
            
            # Run optimization
            method = st.session_state.tune_method
            metric = st.session_state.tune_metric
            higher_is_better = st.session_state.tune_higher_is_better
            
            if method == "Grid Search":
                results = tuner.grid_search(
                    param_space=param_spaces,
                    metric=metric,
                    higher_is_better=higher_is_better,
                    verbose=False,
                )
            elif method == "Random Search":
                results = tuner.random_search(
                    param_space=param_spaces,
                    n_trials=st.session_state.tune_n_trials,
                    metric=metric,
                    higher_is_better=higher_is_better,
                    random_state=st.session_state.tune_random_seed,
                    verbose=False,
                )
            else:  # Bayesian Optimization
                results = tuner.bayesian_optimization(
                    param_space=param_spaces,
                    n_trials=st.session_state.tune_n_trials,
                    metric=metric,
                    higher_is_better=higher_is_better,
                    random_state=st.session_state.tune_random_seed,
                    verbose=False,
                )
            
            progress_bar.progress(100)
            status_text.text("Optimization complete!")
            
            # Store results
            st.session_state.tune_results = results
            st.session_state.tune_completed = True
            
            st.success("✅ Optimization completed successfully!")
            st.balloons()
            
            # Auto-navigate to results tab
            st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error during optimization: {e}")
        import traceback
        st.code(traceback.format_exc())


def render_results_tab():
    """Render the results tab."""
    
    st.header("Optimization Results")
    
    if 'tune_results' not in st.session_state or not st.session_state.tune_completed:
        st.info("No optimization results yet. Configure and run optimization first.")
        return
    
    results = st.session_state.tune_results
    
    # Summary metrics
    st.subheader("🏆 Best Configuration")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Best Score", f"{results.best_score:.4f}")
    
    with col2:
        st.metric("Method", results.method.replace('_', ' ').title())
    
    with col3:
        st.metric("Trials Completed", results.n_trials)
    
    with col4:
        st.metric("Time Elapsed", f"{results.optimization_time:.1f}s")
    
    st.markdown("---")
    
    # Best parameters
    st.subheader("📋 Best Parameters")
    
    params_df = pd.DataFrame([
        {"Parameter": k, "Value": v}
        for k, v in results.best_params.items()
    ])
    st.table(params_df)
    
    # Best backtest metrics
    if results.best_backtest:
        st.subheader("📊 Best Backtest Performance")
        
        metrics = results.best_backtest.metrics
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{metrics.get('total_return', 0)*100:.2f}%")
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
        
        with col2:
            st.metric("Annual Return", f"{metrics.get('annual_return', 0)*100:.2f}%")
            st.metric("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.2f}")
        
        with col3:
            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0)*100:.2f}%")
            st.metric("Calmar Ratio", f"{metrics.get('calmar_ratio', 0):.2f}")
        
        with col4:
            st.metric("Volatility", f"{metrics.get('volatility', 0)*100:.2f}%")
            st.metric("Win Rate", f"{metrics.get('win_rate', 0)*100:.2f}%")
    
    st.markdown("---")
    
    # All results table
    st.subheader("📈 All Trials")
    
    # Filter and display options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=list(results.all_results.columns),
            index=list(results.all_results.columns).index('score') if 'score' in results.all_results.columns else 0
        )
    
    with col2:
        ascending = st.checkbox("Ascending", value=False)
    
    # Sort and display
    sorted_results = results.all_results.sort_values(by=sort_by, ascending=ascending)
    st.dataframe(sorted_results, use_container_width=True, height=400)
    
    # Visualization
    st.subheader("📊 Optimization Progress")
    
    # Score over trials
    if 'trial' in results.all_results.columns and 'score' in results.all_results.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=results.all_results['trial'],
            y=results.all_results['score'],
            mode='markers+lines',
            name='Score',
            marker=dict(size=6, color=results.all_results['score'], colorscale='Viridis', showscale=True),
            line=dict(width=1, color='lightgray')
        ))
        
        # Add best score line
        fig.add_hline(
            y=results.best_score,
            line_dash="dash",
            line_color="red",
            annotation_text="Best Score",
            annotation_position="right"
        )
        
        fig.update_layout(
            title="Optimization Progress",
            xaxis_title="Trial",
            yaxis_title=results.metric_name,
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Parameter importance (if multiple params)
    param_cols = [col for col in results.all_results.columns if col.startswith('param_')]
    if len(param_cols) > 1:
        st.subheader("🎯 Parameter Analysis")
        
        # Create parallel coordinates plot
        plot_df = results.all_results[param_cols + ['score']].dropna()
        
        if not plot_df.empty:
            fig = px.parallel_coordinates(
                plot_df,
                color='score',
                dimensions=param_cols + ['score'],
                color_continuous_scale='Viridis',
                title="Parameter Relationships"
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # Download results
    st.markdown("---")
    st.subheader("💾 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = results.all_results.to_csv(index=False)
        st.download_button(
            label="Download Results CSV",
            data=csv,
            file_name=f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        import json
        params_json = json.dumps({
            'best_params': results.best_params,
            'best_score': float(results.best_score),
            'metric': results.metric_name,
            'method': results.method,
        }, indent=2)
        
        st.download_button(
            label="Download Best Parameters JSON",
            data=params_json,
            file_name=f"best_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


if __name__ == "__main__":
    render()
