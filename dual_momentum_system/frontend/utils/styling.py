"""
Styling utilities for the Streamlit dashboard.

Provides consistent, professional styling across all pages.
"""

import streamlit as st


def apply_custom_css():
    """Apply custom CSS styling to the dashboard."""
    
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            padding: 0rem 1rem;
        }
        
        /* Header styling */
        .page-header {
            background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
        }
        
        .page-header h1 {
            color: white !important;
            margin-bottom: 0.5rem;
        }
        
        .page-header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #1f77b4;
            margin-bottom: 1rem;
        }
        
        .metric-card h3 {
            color: #333;
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
        }
        
        .warning-box {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .success-box {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        
        .error-box {
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
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
        
        /* Card container */
        .card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
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
