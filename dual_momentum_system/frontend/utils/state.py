"""
Session state management for the Streamlit dashboard.

Manages persistent state across page navigation.
"""

import streamlit as st
from typing import Any, Dict, List
import json
from pathlib import Path


def initialize_session_state():
    """Initialize all session state variables."""
    
    # Backtest results
    if 'backtest_results' not in st.session_state:
        st.session_state.backtest_results = None
    
    # Comparison data
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = []
    
    # Asset universes
    if 'asset_universes' not in st.session_state:
        st.session_state.asset_universes = load_asset_universes()
    
    # Current strategy configuration
    if 'current_strategy_config' not in st.session_state:
        st.session_state.current_strategy_config = {}
    
    # Last backtest parameters
    if 'last_backtest_params' not in st.session_state:
        st.session_state.last_backtest_params = {}
    
    # Cached price data
    if 'cached_price_data' not in st.session_state:
        st.session_state.cached_price_data = {}


def load_asset_universes() -> Dict[str, Dict[str, Any]]:
    """
    Load saved asset universes from file.
    
    Returns:
        Dictionary of asset universes
    """
    universes_file = Path(__file__).parent.parent.parent / 'data' / 'asset_universes.json'
    
    # Default universes
    default_universes = {
        "US Large Cap": {
            "description": "S&P 500 sector representatives",
            "asset_class": "equity",
            "symbols": ["SPY", "QQQ", "IWM", "DIA"],
            "benchmark": "SPY"
        },
        "Global Equities": {
            "description": "Global equity market ETFs",
            "asset_class": "equity",
            "symbols": ["VTI", "VEA", "VWO", "EEM"],
            "benchmark": "VT"
        },
        "Crypto Major": {
            "description": "Major cryptocurrencies",
            "asset_class": "crypto",
            "symbols": ["BTC/USD", "ETH/USD", "BNB/USD"],
            "benchmark": "BTC/USD"
        },
        "Commodities": {
            "description": "Major commodity futures",
            "asset_class": "commodity",
            "symbols": ["GC", "CL", "NG", "SI"],
            "benchmark": "GC"
        },
        "Fixed Income": {
            "description": "Bond ETFs across duration",
            "asset_class": "bond",
            "symbols": ["TLT", "IEF", "SHY", "AGG"],
            "benchmark": "AGG"
        },
        "FX Majors": {
            "description": "Major currency pairs",
            "asset_class": "fx",
            "symbols": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"],
            "benchmark": "EUR/USD"
        }
    }
    
    # Try to load from file, otherwise use defaults
    if universes_file.exists():
        try:
            with open(universes_file, 'r') as f:
                return json.load(f)
        except Exception:
            return default_universes
    
    return default_universes


def save_asset_universes(universes: Dict[str, Dict[str, Any]]):
    """
    Save asset universes to file.
    
    Args:
        universes: Dictionary of asset universes to save
    """
    universes_file = Path(__file__).parent.parent.parent / 'data' / 'asset_universes.json'
    universes_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(universes_file, 'w') as f:
            json.dump(universes, f, indent=2)
        st.session_state.asset_universes = universes
        return True
    except Exception as e:
        st.error(f"Failed to save asset universes: {str(e)}")
        return False


def add_to_comparison(result: Any, name: str):
    """
    Add a backtest result to comparison list.
    
    Args:
        result: Backtest result object
        name: Name for this result
    """
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = []
    
    # Avoid duplicates
    existing_names = [r['name'] for r in st.session_state.comparison_results]
    if name in existing_names:
        # Remove old version
        st.session_state.comparison_results = [
            r for r in st.session_state.comparison_results if r['name'] != name
        ]
    
    st.session_state.comparison_results.append({
        'name': name,
        'result': result,
        'timestamp': st.session_state.get('last_backtest_params', {}).get('timestamp', 'Unknown')
    })


def clear_comparison():
    """Clear all comparison results."""
    st.session_state.comparison_results = []


def cache_price_data(symbol: str, data: Any):
    """
    Cache price data for a symbol.
    
    Args:
        symbol: Asset symbol
        data: Price data
    """
    if 'cached_price_data' not in st.session_state:
        st.session_state.cached_price_data = {}
    
    st.session_state.cached_price_data[symbol] = data


def get_cached_price_data(symbol: str) -> Any:
    """
    Get cached price data for a symbol.
    
    Args:
        symbol: Asset symbol
        
    Returns:
        Cached price data or None
    """
    if 'cached_price_data' not in st.session_state:
        return None
    
    return st.session_state.cached_price_data.get(symbol)
