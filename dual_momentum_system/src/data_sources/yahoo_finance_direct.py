"""
Yahoo Finance data source using direct HTTP requests.

This implementation uses direct HTTP requests to Yahoo Finance API
instead of the yfinance library, making it more reliable on Streamlit Cloud
and other restricted environments.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import time

import pandas as pd
import requests
from loguru import logger

from ..core.base_data_source import BaseDataSource
from ..core.types import AssetType


class YahooFinanceDirectSource(BaseDataSource):
    """
    Data source for Yahoo Finance using direct HTTP requests.
    
    This implementation bypasses the yfinance library and directly
    calls Yahoo Finance's API endpoints, making it more reliable
    on Streamlit Cloud and similar platforms.
    """
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
    DOWNLOAD_URL = "https://query1.finance.yahoo.com/v7/finance/download/"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Yahoo Finance Direct data source.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - cache_enabled: Enable caching (default: True)
                   - timeout: Request timeout in seconds (default: 10)
                   - max_retries: Maximum retry attempts (default: 3)
                   - retry_delay: Delay between retries in seconds (default: 1)
        """
        super().__init__(config)
        
        self.timeout = self.config.get('timeout', 10)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _timestamp_to_unix(self, dt: datetime) -> int:
        """Convert datetime to Unix timestamp."""
        return int(dt.timestamp())
    
    def _interval_to_yahoo(self, timeframe: str) -> str:
        """Convert standard timeframe to Yahoo Finance interval."""
        # Yahoo Finance uses same format
        return timeframe
    
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            timeframe: Data interval (1d, 1h, 5m, etc.)
        
        Returns:
            DataFrame with OHLCV data
        
        Raises:
            ValueError: If symbol or timeframe is invalid
            ConnectionError: If unable to fetch data
        """
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.debug(f"Using cached data for {symbol}")
            return cached_data
        
        # Validate timeframe
        if not self.validate_timeframe(timeframe):
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        try:
            logger.info(f"Fetching {symbol} from Yahoo Finance (Direct): {start_date} to {end_date}")
            
            # Build request parameters
            params = {
                'period1': self._timestamp_to_unix(start_date),
                'period2': self._timestamp_to_unix(end_date),
                'interval': self._interval_to_yahoo(timeframe),
                'events': 'history',
                'includeAdjustedClose': 'true'
            }
            
            # Make request with retries
            url = f"{self.BASE_URL}{symbol}"
            data = self._make_request_with_retry(url, params)
            
            if not data:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Parse response
            df = self._parse_chart_response(data)
            
            if df.empty:
                logger.warning(f"Empty dataframe after parsing for {symbol}")
                return pd.DataFrame()
            
            # Add to cache
            self.add_to_cache(symbol, start_date, end_date, timeframe, df)
            
            logger.debug(f"Successfully fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise ConnectionError(f"Failed to fetch data from Yahoo Finance: {e}")
    
    def _make_request_with_retry(self, url: str, params: Dict) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
        
        return None
    
    def _parse_chart_response(self, data: Dict) -> pd.DataFrame:
        """Parse Yahoo Finance chart API response."""
        try:
            result = data.get('chart', {}).get('result', [])
            if not result:
                return pd.DataFrame()
            
            result = result[0]
            
            # Extract timestamps
            timestamps = result.get('timestamp', [])
            if not timestamps:
                return pd.DataFrame()
            
            # Extract quotes
            quotes = result.get('indicators', {}).get('quote', [])
            if not quotes:
                return pd.DataFrame()
            
            quote = quotes[0]
            
            # Build dataframe
            df = pd.DataFrame({
                'open': quote.get('open', []),
                'high': quote.get('high', []),
                'low': quote.get('low', []),
                'close': quote.get('close', []),
                'volume': quote.get('volume', [])
            })
            
            # Add timestamps as index
            df.index = pd.to_datetime(timestamps, unit='s')
            df.index.name = 'Date'
            
            # Handle adjusted close if available
            adjclose = result.get('indicators', {}).get('adjclose', [])
            if adjclose and adjclose[0].get('adjclose'):
                df['adjclose'] = adjclose[0]['adjclose']
            
            # Remove rows with all NaN values
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return pd.DataFrame()
    
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets.
        
        Note: Yahoo Finance supports a vast universe of symbols.
        This returns an empty list to indicate all symbols are potentially valid.
        
        Returns:
            Empty list (all symbols potentially supported)
        """
        return []
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get supported timeframes.
        
        Returns:
            List of supported interval strings
        """
        return [
            '1m',   # 1 minute (only last 7 days available)
            '2m',   # 2 minutes
            '5m',   # 5 minutes
            '15m',  # 15 minutes
            '30m',  # 30 minutes
            '60m',  # 60 minutes
            '90m',  # 90 minutes
            '1h',   # 1 hour
            '1d',   # 1 day
            '5d',   # 5 days
            '1wk',  # 1 week
            '1mo',  # 1 month
            '3mo'   # 3 months
        ]
    
    def is_available(self) -> bool:
        """
        Check if Yahoo Finance is available.
        
        Returns:
            True if service is reachable
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            params = {
                'period1': self._timestamp_to_unix(start_date),
                'period2': self._timestamp_to_unix(end_date),
                'interval': '1d'
            }
            url = f"{self.BASE_URL}SPY"
            
            response = self.session.get(url, params=params, timeout=5)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent price.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Latest close price or None
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            
            data = self.fetch_data(symbol, start_date, end_date, timeframe='1d')
            
            if data is not None and len(data) > 0:
                return float(data['close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed asset information.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dictionary with asset info
        """
        try:
            # Use quote summary endpoint
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'assetProfile,summaryProfile,price'
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            result = data.get('quoteSummary', {}).get('result', [])
            if not result:
                return None
            
            info = result[0]
            price_info = info.get('price', {})
            profile_info = info.get('assetProfile', {}) or info.get('summaryProfile', {})
            
            return {
                'symbol': symbol,
                'name': price_info.get('longName', symbol),
                'sector': profile_info.get('sector'),
                'industry': profile_info.get('industry'),
                'exchange': price_info.get('exchange'),
                'currency': price_info.get('currency', 'USD'),
                'market_cap': price_info.get('marketCap'),
                'description': profile_info.get('longBusinessSummary'),
            }
            
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            return None
    
    def get_data_range(self, symbol: str) -> Optional[tuple[datetime, datetime]]:
        """
        Get available date range for a symbol.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Tuple of (earliest_date, latest_date)
        """
        try:
            # Fetch max period (approximately)
            end_date = datetime.now()
            start_date = datetime(1970, 1, 1)  # Yahoo Finance epoch
            
            data = self.fetch_data(symbol, start_date, end_date, timeframe='1d')
            
            if data is not None and len(data) > 0:
                return (
                    data.index[0].to_pydatetime(),
                    data.index[-1].to_pydatetime()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting date range for {symbol}: {e}")
            return None
    
    def get_supported_asset_types(self) -> Set[AssetType]:
        """
        Get supported asset types.
        
        Returns:
            Set of supported AssetType values
        """
        return {
            AssetType.EQUITY,
            AssetType.COMMODITY,
            AssetType.FX,
            AssetType.CRYPTO,
        }
    
    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        logger.info(f"Fetching {len(symbols)} symbols from Yahoo Finance (Direct)")
        
        result = {}
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    result[symbol] = df
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(result)} symbols")
        return result
    
    @classmethod
    def requires_authentication(cls) -> bool:
        """Yahoo Finance doesn't require authentication."""
        return False
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Yahoo Finance data source using direct HTTP requests. "
            "Provides historical price data for equities, ETFs, indices, "
            "commodities, currencies, and cryptocurrencies. "
            "More reliable on Streamlit Cloud than yfinance library. "
            "Free to use with no authentication required."
        )
