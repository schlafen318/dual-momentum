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
    
    # Initialize session state
    initialize_session_state()
    
    # Track current page for auto-hide sidebar functionality
    if 'current_page' not in st.session_state:
        st.session_state.current_page = None
    if 'previous_page' not in st.session_state:
        st.session_state.previous_page = None
    if 'page_changed' not in st.session_state:
        st.session_state.page_changed = False
    if 'first_load' not in st.session_state:
        st.session_state.first_load = True
    
    # Apply custom styling (no sidebar collapse on CSS - we'll use JS instead)
    apply_custom_css(collapse_sidebar=False)
    
    # Sidebar navigation
    with st.sidebar:
        # App title
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #1f77b4; margin: 0;'>📈</h1>
            <h3 style='margin: 0.5rem 0 0 0;'>Dual Momentum</h3>
            <p style='font-size: 0.8rem; color: #888; margin: 0.25rem 0 0 0;'>Backtesting Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        pages = [
            "🏠 Home",
            "🛠️ Strategy Builder",
            "📊 Backtest Results",
            "🔄 Compare Strategies",
            "🎯 Hyperparameter Tuning",
            "🤖 Autonomous Agent",
            "💼 Portfolio Optimization",
            "🗂️ Asset Universe Manager"
        ]
        
        # Check if navigation is triggered programmatically
        default_index = 0
        if 'navigate_to' in st.session_state:
            if st.session_state.navigate_to in pages:
                default_index = pages.index(st.session_state.navigate_to)
            del st.session_state.navigate_to
        
        page = st.radio(
            "Select Page",
            pages,
            index=default_index,
            key="page_navigation",  # Explicit key to preserve state on rerun
            label_visibility="collapsed"
        )
        
        # Track page changes for auto-hide functionality
        if st.session_state.current_page != page:
            st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = page
            # Only set page_changed if this is not the first load
            if not st.session_state.first_load:
                st.session_state.page_changed = True
            else:
                st.session_state.page_changed = False
                st.session_state.first_load = False
        else:
            st.session_state.page_changed = False
        
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
        from frontend.page_modules import home
        home.render()
    elif page == "🛠️ Strategy Builder":
        from frontend.page_modules import strategy_builder
        strategy_builder.render()
    elif page == "📊 Backtest Results":
        from frontend.page_modules import backtest_results
        backtest_results.render()
    elif page == "🔄 Compare Strategies":
        from frontend.page_modules import compare_strategies
        compare_strategies.render()
    elif page == "🎯 Hyperparameter Tuning":
        from frontend.page_modules import hyperparameter_tuning
        hyperparameter_tuning.render()
    elif page == "🤖 Autonomous Agent":
        from frontend.page_modules import autonomous_agent
        autonomous_agent.render()
    elif page == "💼 Portfolio Optimization":
        from frontend.page_modules import portfolio_optimization
        portfolio_optimization.render()
    elif page == "🗂️ Asset Universe Manager":
        from frontend.page_modules import asset_universe_manager
        asset_universe_manager.render()
    
    # Auto-hide sidebar AFTER page content loads (if page changed)
    if st.session_state.get('page_changed', False):
        # Use HTML/JS to trigger sidebar collapse after content renders
        st.markdown("""
        <script>
            // Wait for DOM and page content to be ready
            setTimeout(function() {
                const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                const collapseBtn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
                
                // Check if sidebar is expanded and collapse it
                if (sidebar && collapseBtn) {
                    const sidebarWidth = window.getComputedStyle(sidebar).width;
                    if (parseFloat(sidebarWidth) > 0) {
                        collapseBtn.click();
                    }
                }
            }, 200);
        </script>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
