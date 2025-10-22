"""
Styling utilities for the Streamlit dashboard.

Provides consistent, professional styling across all pages.
"""

import streamlit as st


def apply_custom_css(collapse_sidebar=False):
    """Apply custom CSS styling to the dashboard.
    
    Args:
        collapse_sidebar: If True, applies CSS to collapse the sidebar
    """
    
    # Sidebar collapse CSS (applied when page changes)
    sidebar_collapse_css = ""
    if collapse_sidebar:
        sidebar_collapse_css = """
        /* Auto-collapse sidebar on page change */
        section[data-testid="stSidebar"] {
            width: 0px !important;
            min-width: 0px !important;
        }
        
        section[data-testid="stSidebar"] > div {
            width: 0px !important;
            margin-left: -21rem !important;
        }
        
        /* Show collapse button */
        button[kind="header"] {
            display: block !important;
        }
        """
    
    st.markdown(f"""
    <style>
        {sidebar_collapse_css}
        
        /* Main container styling */
        .main {{
            padding: 0rem 1rem;
        }}
        
        /* Header styling */
        .page-header {{
            background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
        }}
        
        .page-header h1 {{
            color: white !important;
            margin-bottom: 0.5rem;
        }}
        
        .page-header p {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;
        }}
        
        /* Metric cards - Light mode default */
        .metric-card {
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #1f77b4;
            margin-bottom: 1rem;
        }
        
        .metric-card h3 {
            color: #333333;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
        }
        
        /* Ensure light mode metric cards have light background */
        [data-theme="light"] .metric-card {
            background: #ffffff !important;
        }
        
        [data-theme="light"] .metric-card h3 {
            color: #333333 !important;
        }
        
        [data-theme="light"] .metric-card .value {
            color: #1f77b4 !important;
        }
        
        .metric-card .delta {
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .metric-card.positive {
            border-left-color: #2ca02c;
        }
        
        .metric-card.positive .value {
            color: #2ca02c;
        }
        
        .metric-card.negative {
            border-left-color: #d62728;
        }
        
        .metric-card.negative .value {
            color: #d62728;
        }
        
        /* Info boxes */
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            color: #1565c0;
        }
        
        .warning-box {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            color: #e65100;
        }
        
        .success-box {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            color: #2e7d32;
        }
        
        .error-box {
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            color: #c62828;
        }
        
        /* Buttons */
        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 5px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        
        /* Data tables */
        .dataframe {
            font-size: 0.9rem;
        }
        
        .dataframe th {
            background-color: #1f77b4 !important;
            color: white !important;
            font-weight: bold;
            text-align: left;
            padding: 0.75rem;
        }
        
        .dataframe td {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .dataframe tr:hover {
            background-color: #f5f5f5;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 5px;
            font-weight: bold;
        }
        
        /* Tooltips */
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
            color: #1f77b4;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            background-color: transparent;
            border-radius: 5px 5px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #1f77b4;
            color: white;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Card container - Light mode default */
        .card {
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            color: #333333;
        }
        
        .card h3, .card h4 {
            color: #1f77b4;
        }
        
        .card p, .card ul, .card li {
            color: #333333;
        }
        
        /* Ensure light mode cards have light background */
        [data-theme="light"] .card {
            background: #ffffff !important;
            color: #333333 !important;
        }
        
        [data-theme="light"] .card h3,
        [data-theme="light"] .card h4 {
            color: #1f77b4 !important;
        }
        
        [data-theme="light"] .card p,
        [data-theme="light"] .card ul,
        [data-theme="light"] .card li {
            color: #333333 !important;
        }
        
        /* Footer styling */
        .sidebar-footer {
            text-align: center;
            color: #888;
            font-size: 0.8em;
        }
        
        /* Section divider */
        .section-divider {
            border-top: 2px solid #e0e0e0;
            margin: 2rem 0;
        }
        
        /* Status badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: bold;
        }
        
        .badge-success {
            background-color: #4caf50;
            color: white;
        }
        
        .badge-warning {
            background-color: #ff9800;
            color: white;
        }
        
        .badge-error {
            background-color: #f44336;
            color: white;
        }
        
        .badge-info {
            background-color: #2196f3;
            color: white;
        }
        
        /* Colored highlight cards - Light mode default */
        .card-success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        
        .card-success h4 {
            color: #1b5e20;
        }
        
        .card-success p {
            color: #2ca02c;
        }
        
        .card-info {
            background: #e3f2fd;
            color: #1565c0;
        }
        
        .card-info h4 {
            color: #0d47a1;
        }
        
        .card-info p {
            color: #1f77b4;
        }
        
        .card-warning {
            background: #fff3e0;
            color: #e65100;
        }
        
        .card-warning h4 {
            color: #bf360c;
        }
        
        .card-warning p {
            color: #ff9800;
        }
        
        /* Ensure colored cards work in light mode */
        [data-theme="light"] .card-success {
            background: #e8f5e9 !important;
            color: #2e7d32 !important;
        }
        
        [data-theme="light"] .card-success h4 {
            color: #1b5e20 !important;
        }
        
        [data-theme="light"] .card-success p {
            color: #2ca02c !important;
        }
        
        [data-theme="light"] .card-info {
            background: #e3f2fd !important;
            color: #1565c0 !important;
        }
        
        [data-theme="light"] .card-info h4 {
            color: #0d47a1 !important;
        }
        
        [data-theme="light"] .card-info p {
            color: #1f77b4 !important;
        }
        
        [data-theme="light"] .card-warning {
            background: #fff3e0 !important;
            color: #e65100 !important;
        }
        
        [data-theme="light"] .card-warning h4 {
            color: #bf360c !important;
        }
        
        [data-theme="light"] .card-warning p {
            color: #ff9800 !important;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {{
            /* Card containers in dark mode */
            .card {{
                background: #1e1e1e !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                color: #e0e0e0 !important;
            }}
            
            .card h3 {{
                color: #4fc3f7 !important;
            }}
            
            .card p, .card ul, .card li {{
                color: #e0e0e0 !important;
            }}
            
            /* Metric cards in dark mode */
            .metric-card {{
                background: #1e1e1e !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            }}
            
            .metric-card h3 {{
                color: #b0b0b0 !important;
            }}
            
            .metric-card .value {{
                color: #4fc3f7 !important;
            }}
            
            .metric-card.positive .value {{
                color: #66bb6a !important;
            }}
            
            .metric-card.negative .value {{
                color: #ef5350 !important;
            }}
            
            /* Info boxes in dark mode */
            .info-box {{
                background: #1a237e !important;
                color: #90caf9 !important;
                border-left-color: #42a5f5;
            }}
            
            .warning-box {{
                background: #4a2c00 !important;
                color: #ffb74d !important;
                border-left-color: #ffa726;
            }}
            
            .success-box {{
                background: #1b5e20 !important;
                color: #81c784 !important;
                border-left-color: #66bb6a;
            }}
            
            .error-box {{
                background: #4a0000 !important;
                color: #ef9a9a !important;
                border-left-color: #ef5350;
            }}
            
            /* Data tables in dark mode */
            .dataframe th {{
                background-color: #1565c0 !important;
            }}
            
            .dataframe td {{
                border-bottom-color: #424242 !important;
                color: #e0e0e0 !important;
            }}
            
            .dataframe tr:hover {{
                background-color: #2a2a2a !important;
            }}
            
            /* Expander in dark mode */
            .streamlit-expanderHeader {{
                background-color: #2a2a2a !important;
                color: #e0e0e0 !important;
            }}
            
            /* Section divider in dark mode */
            .section-divider {{
                border-top-color: #424242;
            }}
            
            /* Footer in dark mode */
            .sidebar-footer {{
                color: #b0b0b0 !important;
            }}
            
            /* Colored highlight cards in dark mode */
            .card-success {{
                background: #1b5e20 !important;
                color: #a5d6a7 !important;
            }}
            
            .card-success h4 {{
                color: #c8e6c9 !important;
            }}
            
            .card-success p {{
                color: #66bb6a !important;
            }}
            
            .card-info {{
                background: #1a237e !important;
                color: #90caf9 !important;
            }}
            
            .card-info h4 {{
                color: #bbdefb !important;
            }}
            
            .card-info p {{
                color: #42a5f5 !important;
            }}
            
            .card-warning {{
                background: #4a2c00 !important;
                color: #ffcc80 !important;
            }}
            
            .card-warning h4 {{
                color: #ffe0b2 !important;
            }}
            
            .card-warning p {{
                color: #ffa726 !important;
            }}
        }}
        
        /* Force dark mode for Streamlit dark theme */
        [data-theme="dark"] .card {{
            background: #1e1e1e !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            color: #e0e0e0 !important;
        }}
        
        [data-theme="dark"] .card h3,
        [data-theme="dark"] .card h4 {{
            color: #4fc3f7 !important;
        }}
        
        [data-theme="dark"] .card p,
        [data-theme="dark"] .card ul,
        [data-theme="dark"] .card li {{
            color: #e0e0e0 !important;
        }}
        
        [data-theme="dark"] .metric-card {{
            background: #1e1e1e !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }}
        
        [data-theme="dark"] .metric-card h3 {{
            color: #b0b0b0 !important;
        }}
        
        [data-theme="dark"] .metric-card .value {{
            color: #4fc3f7 !important;
        }}
        
        [data-theme="dark"] .metric-card.positive .value {{
            color: #66bb6a !important;
        }}
        
        [data-theme="dark"] .metric-card.negative .value {{
            color: #ef5350 !important;
        }}
        
        [data-theme="dark"] .info-box {{
            background: #1a237e !important;
            color: #90caf9 !important;
            border-left-color: #42a5f5;
        }}
        
        [data-theme="dark"] .warning-box {{
            background: #4a2c00 !important;
            color: #ffb74d !important;
            border-left-color: #ffa726;
        }}
        
        [data-theme="dark"] .success-box {{
            background: #1b5e20 !important;
            color: #81c784 !important;
            border-left-color: #66bb6a;
        }}
        
        [data-theme="dark"] .error-box {{
            background: #4a0000 !important;
            color: #ef9a9a !important;
            border-left-color: #ef5350;
        }}
        
        /* Colored highlight cards in Streamlit dark theme */
        [data-theme="dark"] .card-success {{
            background: #1b5e20 !important;
            color: #a5d6a7 !important;
        }}
        
        [data-theme="dark"] .card-success h4 {{
            color: #c8e6c9 !important;
        }}
        
        [data-theme="dark"] .card-success p {{
            color: #66bb6a !important;
        }}
        
        [data-theme="dark"] .card-info {{
            background: #1a237e !important;
            color: #90caf9 !important;
        }}
        
        [data-theme="dark"] .card-info h4 {{
            color: #bbdefb !important;
        }}
        
        [data-theme="dark"] .card-info p {{
            color: #42a5f5 !important;
        }}
        
        [data-theme="dark"] .card-warning {{
            background: #4a2c00 !important;
            color: #ffcc80 !important;
        }}
        
        [data-theme="dark"] .card-warning h4 {{
            color: #ffe0b2 !important;
        }}
        
        [data-theme="dark"] .card-warning p {{
            color: #ffa726 !important;
        }}
        
        /* Footer in Streamlit dark theme */
        [data-theme="dark"] .sidebar-footer {{
            color: #b0b0b0 !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_page_header(title: str, description: str, icon: str = "📈"):
    """
    Render a consistent page header.
    
    Args:
        title: Page title
        description: Page description
        icon: Emoji icon for the page
    """
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon} {title}</h1>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, delta: str = None, 
                       delta_color: str = "normal"):
    """
    Render a metric card.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Change indicator
        delta_color: Color for delta (positive, negative, normal)
    """
    card_class = "metric-card"
    if delta_color == "positive":
        card_class += " positive"
    elif delta_color == "negative":
        card_class += " negative"
    
    delta_html = ""
    if delta:
        delta_symbol = "▲" if delta_color == "positive" else "▼" if delta_color == "negative" else "●"
        delta_html = f'<div class="delta">{delta_symbol} {delta}</div>'
    
    st.markdown(f"""
    <div class="{card_class}">
        <h3>{title}</h3>
        <div class="value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_info_box(message: str, box_type: str = "info"):
    """
    Render an info/warning/success/error box.
    
    Args:
        message: Message to display
        box_type: Type of box (info, warning, success, error)
    """
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "success": "✅",
        "error": "❌"
    }
    
    icon = icons.get(box_type, "ℹ️")
    
    st.markdown(f"""
    <div class="{box_type}-box">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def render_section_divider():
    """Render a visual section divider."""
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
