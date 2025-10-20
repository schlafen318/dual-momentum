"""
Data source plugins for the dual momentum system.
"""

# Import YahooFinanceDirectSource (no yfinance dependency required)
from .yahoo_finance_direct import YahooFinanceDirectSource

# Optional: Import YahooFinanceSource only if yfinance is available
try:
    from .yahoo_finance import YahooFinanceSource
    _YFINANCE_AVAILABLE = True
except ImportError:
    _YFINANCE_AVAILABLE = False
    YahooFinanceSource = None

__all__ = [
    'YahooFinanceDirectSource',
]

if _YFINANCE_AVAILABLE:
    __all__.append('YahooFinanceSource')
