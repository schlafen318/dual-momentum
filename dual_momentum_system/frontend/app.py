"""
Main Streamlit dashboard application.

Professional multi-page dashboard for interactive backtesting of momentum strategies.
"""

import streamlit as st
from pathlib import Path
import sys
import streamlit.components.v1 as components

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
        # App branding header
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%); border-radius: 8px; margin-bottom: 1rem;'>
            <h2 style='color: white; margin: 0;'>📈 Dual Momentum</h2>
            <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>Backtesting Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        # Track previous page for auto-collapse detection
        previous_page = st.session_state.get('current_page', pages[0])
        
        page = st.radio(
            "Navigation",
            pages,
            index=default_index,
            key='page_navigation'
        )
        
        # Update current page in session state
        st.session_state.current_page = page
        
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
    
    # Auto-collapse sidebar after navigation (on page change)
    if previous_page != page:
        # Use components.html for more reliable JavaScript execution
        collapse_sidebar_js = """
            <script>
                function collapseSidebar() {
                    const doc = window.parent.document;
                    
                    // Method 1: Try to find and click the close button
                    const buttons = doc.querySelectorAll('button[kind="header"]');
                    for (let button of buttons) {
                        const ariaLabel = button.getAttribute('aria-label');
                        if (ariaLabel && (ariaLabel.toLowerCase().includes('close') || ariaLabel.toLowerCase().includes('collapse'))) {
                            button.click();
                            return;
                        }
                    }
                    
                    // Method 2: Try alternative selector
                    const closeBtn = doc.querySelector('[data-testid="collapsedControl"]');
                    if (closeBtn) {
                        const parentBtn = closeBtn.closest('button');
                        if (parentBtn) parentBtn.click();
                        return;
                    }
                    
                    // Method 3: Find button with SVG icon (Streamlit's close button)
                    const allButtons = doc.querySelectorAll('button');
                    for (let button of allButtons) {
                        const svg = button.querySelector('svg');
                        if (svg && button.parentElement && button.parentElement.parentElement) {
                            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                            if (sidebar && sidebar.contains(button)) {
                                continue;
                            }
                            if (button.offsetParent !== null) {
                                button.click();
                                break;
                            }
                        }
                    }
                }
                
                // Try immediately and after a delay
                setTimeout(collapseSidebar, 100);
            </script>
        """
        components.html(collapse_sidebar_js, height=0)
    
    # Route to appropriate page
    if page == "🏠 Home":
        from frontend.views import home
        home.render()
    elif page == "🛠️ Strategy Builder":
        from frontend.views import strategy_builder
        strategy_builder.render()
    elif page == "📊 Backtest Results":
        from frontend.views import backtest_results
        backtest_results.render()
    elif page == "🔄 Compare Strategies":
        from frontend.views import compare_strategies
        compare_strategies.render()
    elif page == "🗂️ Asset Universe Manager":
        from frontend.views import asset_universe_manager
        asset_universe_manager.render()


if __name__ == "__main__":
    main()
