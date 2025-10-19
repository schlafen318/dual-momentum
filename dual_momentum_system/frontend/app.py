"""
Main Streamlit dashboard application.

Professional multi-page dashboard for interactive backtesting of momentum strategies.
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import utilities
from frontend.utils.styling import apply_custom_css, render_page_header
from frontend.utils.state import initialize_session_state


def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="Dual Momentum Backtesting Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/yourusername/dual-momentum',
            'Report a bug': "https://github.com/yourusername/dual-momentum/issues",
            'About': """
            # Dual Momentum Backtesting Dashboard
            
            Professional backtesting platform for momentum-based trading strategies.
            
            **Version:** 1.0.0
            
            **Features:**
            - Multi-asset class support
            - Interactive strategy builder
            - Comprehensive performance analytics
            - Strategy comparison tools
            - Asset universe management
            """
        }
    )
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Dual+Momentum", 
                 width='stretch')
        
        st.markdown("---")
        
        # Navigation
        pages = [
            "🏠 Home",
            "🛠️ Strategy Builder",
            "📊 Backtest Results",
            "🔄 Compare Strategies",
            "🗂️ Asset Universe Manager"
        ]
        
        # Check if navigation is triggered programmatically
        default_index = 0
        if 'navigate_to' in st.session_state:
            if st.session_state.navigate_to in pages:
                default_index = pages.index(st.session_state.navigate_to)
            del st.session_state.navigate_to
        
        page = st.radio(
            "Navigation",
            pages,
            index=default_index
        )
        
        st.markdown("---")
        
        # Quick stats (if backtest results exist)
        if 'backtest_results' in st.session_state and st.session_state.backtest_results:
            st.markdown("### 📈 Quick Stats")
            results = st.session_state.backtest_results
            
            if hasattr(results, 'metrics'):
                col1, col2 = st.columns(2)
                with col1:
                    total_return = results.metrics.get('total_return', 0) * 100
                    st.metric("Total Return", f"{total_return:.1f}%")
                with col2:
                    sharpe = results.metrics.get('sharpe_ratio', 0)
                    st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            
            st.markdown("---")
        
        # Footer
        st.markdown("""
        <div class='sidebar-footer'>
            <p>© 2025 Dual Momentum Framework</p>
            <p>v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Route to appropriate page
    if page == "🏠 Home":
        from frontend.pages import home
        home.render()
    elif page == "🛠️ Strategy Builder":
        from frontend.pages import strategy_builder
        strategy_builder.render()
    elif page == "📊 Backtest Results":
        from frontend.pages import backtest_results
        backtest_results.render()
    elif page == "🔄 Compare Strategies":
        from frontend.pages import compare_strategies
        compare_strategies.render()
    elif page == "🗂️ Asset Universe Manager":
        from frontend.pages import asset_universe_manager
        asset_universe_manager.render()


if __name__ == "__main__":
    main()
