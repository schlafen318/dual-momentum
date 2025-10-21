"""
Data source plugins for the dual momentum system.
"""

import os
from loguru import logger

# Core data sources (no external dependencies except requests)
from .yahoo_finance_direct import YahooFinanceDirectSource
from .multi_source import MultiSourceDataProvider

# Alternative data sources
from .alpha_vantage import AlphaVantageSource
from .twelve_data import TwelveDataSource

# Optional: Import YahooFinanceSource only if yfinance is available
try:
    from .yahoo_finance import YahooFinanceSource
    _YFINANCE_AVAILABLE = True
except ImportError:
    _YFINANCE_AVAILABLE = False
    YahooFinanceSource = None


def _is_streamlit_cloud():
    """
    Detect if running on Streamlit Cloud or similar restricted environments.
    
    Returns:
        bool: True if running on Streamlit Cloud or similar platform
    """
    # Check for Streamlit Cloud environment variables
    streamlit_indicators = [
        'STREAMLIT_SHARING_MODE',  # Streamlit Cloud specific
        'STREAMLIT_SERVER_PORT',    # Streamlit server
        'HOSTNAME' in os.environ and 'streamlit' in os.environ.get('HOSTNAME', '').lower(),
    ]
    
    # Check for common cloud platform indicators
    cloud_indicators = [
        os.environ.get('DYNO'),  # Heroku
        os.environ.get('RENDER'),  # Render.com
        os.environ.get('RAILWAY_ENVIRONMENT'),  # Railway
        os.environ.get('VERCEL'),  # Vercel
        os.environ.get('NETLIFY'),  # Netlify
    ]
    
    return any(streamlit_indicators) or any(cloud_indicators)


def get_default_data_source(config=None):
    """
    Get the default data source with failover support.
    
    This returns a MultiSourceDataProvider that intelligently selects data sources:
    - On Streamlit Cloud: Prioritizes YahooFinanceDirectSource (more reliable)
    - Locally: Can use yfinance if available, with DirectSource as fallback
    
    Source priority:
    1. Yahoo Finance Direct (on cloud) OR Yahoo Finance via yfinance (locally, if available)
    2. Yahoo Finance fallback (the opposite of #1)
    3. Alpha Vantage (if API key configured)
    4. Twelve Data (if API key configured)
    
    Args:
        config: Optional configuration dict with API keys:
               - alphavantage_api_key: Alpha Vantage API key
               - twelvedata_api_key: Twelve Data API key
               - force_direct: Force use of YahooFinanceDirectSource (default: auto-detect)
    
    Returns:
        MultiSourceDataProvider with all available sources
    
    Example:
        >>> # Without API keys (Yahoo only)
        >>> source = get_default_data_source()
        >>> 
        >>> # With API keys for failover
        >>> source = get_default_data_source({
        ...     'alphavantage_api_key': 'YOUR_KEY',
        ...     'twelvedata_api_key': 'YOUR_KEY'
        ... })
        >>> 
        >>> # Force direct source (recommended for Streamlit Cloud)
        >>> source = get_default_data_source({'force_direct': True})
    """
    config = config or {}
    
    sources = []
    
    # Detect if running on Streamlit Cloud or similar platform
    is_cloud = _is_streamlit_cloud()
    force_direct = config.get('force_direct', False)
    
    if is_cloud or force_direct:
        logger.info("[DATA SOURCE] Streamlit Cloud/restricted environment detected - prioritizing YahooFinanceDirectSource")
        
        # Primary: Yahoo Finance Direct (more reliable on cloud platforms)
        sources.append(YahooFinanceDirectSource({'cache_enabled': True}))
        
        # Backup: Yahoo Finance via yfinance (if available, but less reliable on cloud)
        if _YFINANCE_AVAILABLE and YahooFinanceSource is not None and not force_direct:
            logger.debug("[DATA SOURCE] Adding YahooFinanceSource as backup (may be unreliable on cloud)")
            sources.append(YahooFinanceSource({'cache_enabled': True}))
    else:
        logger.info("[DATA SOURCE] Local environment detected - using standard source priority")
        
        # Primary: Yahoo Finance via yfinance if available (works well locally)
        if _YFINANCE_AVAILABLE and YahooFinanceSource is not None:
            logger.debug("[DATA SOURCE] Using YahooFinanceSource as primary")
            sources.append(YahooFinanceSource({'cache_enabled': True}))
        
        # Fallback: Yahoo Finance Direct (always available, no API key needed)
        logger.debug("[DATA SOURCE] Adding YahooFinanceDirectSource as fallback")
        sources.append(YahooFinanceDirectSource({'cache_enabled': True}))
    
    # Backup 1: Alpha Vantage (if API key provided)
    if config.get('alphavantage_api_key'):
        logger.debug("[DATA SOURCE] Adding AlphaVantageSource with API key")
        sources.append(AlphaVantageSource({
            'api_key': config['alphavantage_api_key'],
            'cache_enabled': True
        }))
    
    # Backup 2: Twelve Data (if API key provided)
    if config.get('twelvedata_api_key'):
        logger.debug("[DATA SOURCE] Adding TwelveDataSource with API key")
        sources.append(TwelveDataSource({
            'api_key': config['twelvedata_api_key'],
            'cache_enabled': True
        }))
    
    logger.info(f"[DATA SOURCE] Initialized with {len(sources)} source(s): {[type(s).__name__ for s in sources]}")
    
    return MultiSourceDataProvider({
        'sources': sources,
        'cache_enabled': True
    })


__all__ = [
    'YahooFinanceDirectSource',
    'MultiSourceDataProvider',
    'AlphaVantageSource',
    'TwelveDataSource',
    'get_default_data_source',
]

if _YFINANCE_AVAILABLE:
    __all__.append('YahooFinanceSource')
