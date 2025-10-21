"""
Data source plugins for the dual momentum system.
"""

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


def get_default_data_source(config=None):
    """
    Get the default data source with failover support.
    
    This returns a MultiSourceDataProvider that tries:
    1. Yahoo Finance via yfinance (if available)
    2. Yahoo Finance Direct (fallback, no API key needed)
    3. Alpha Vantage (if API key configured)
    4. Twelve Data (if API key configured)
    
    Args:
        config: Optional configuration dict with API keys:
               - alphavantage_api_key: Alpha Vantage API key
               - twelvedata_api_key: Twelve Data API key
    
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
    """
    config = config or {}
    
    sources = []
    
    # Primary: Yahoo Finance via yfinance if available
    if _YFINANCE_AVAILABLE and YahooFinanceSource is not None:
        sources.append(YahooFinanceSource({'cache_enabled': True}))
    
    # Fallback: Yahoo Finance Direct (always available, no API key needed)
    sources.append(YahooFinanceDirectSource({'cache_enabled': True}))
    
    # Backup 1: Alpha Vantage (if API key provided)
    if config.get('alphavantage_api_key'):
        sources.append(AlphaVantageSource({
            'api_key': config['alphavantage_api_key'],
            'cache_enabled': True
        }))
    
    # Backup 2: Twelve Data (if API key provided)
    if config.get('twelvedata_api_key'):
        sources.append(TwelveDataSource({
            'api_key': config['twelvedata_api_key'],
            'cache_enabled': True
        }))
    
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
