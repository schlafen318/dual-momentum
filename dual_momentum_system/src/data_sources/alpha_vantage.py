"""
Alpha Vantage data source implementation.

This module provides an alternative data source using Alpha Vantage's API.
Alpha Vantage offers free tier with 500 requests per day, making it a good
fallback when Yahoo Finance is unavailable.

API Key: Get free key at https://www.alphavantage.co/support/#api-key
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import time

import pandas as pd
import requests
from loguru import logger

from ..core.base_data_source import BaseDataSource
from ..core.types import AssetType


class AlphaVantageSource(BaseDataSource):
    """
    Data source for Alpha Vantage API.
    
    Alpha Vantage provides stock, forex, and crypto data with a free tier.
    Free tier limits: 500 requests/day, 5 requests/minute.
    
    Example:
        >>> source = AlphaVantageSource({
        ...     'api_key': 'YOUR_API_KEY',
        ...     'cache_enabled': True
        ... })
        >>> data = source.fetch_data('AAPL', start_date, end_date)
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Free tier rate limits
    DEFAULT_RATE_LIMIT = {
        'requests_per_minute': 5,
        'requests_per_day': 500
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Alpha Vantage data source.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - api_key: Alpha Vantage API key (required, or set ALPHAVANTAGE_API_KEY env var)
                   - cache_enabled: Enable caching (default: True)
                   - timeout: Request timeout in seconds (default: 30)
                   - rate_limit: Custom rate limit dict (optional)
        """
        super().__init__(config)
        
        # Get API key from config or environment
        import os
        self.api_key = self.config.get('api_key') or os.environ.get('ALPHAVANTAGE_API_KEY')
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured. Set 'api_key' in config or ALPHAVANTAGE_API_KEY env var")
        
        self.timeout = self.config.get('timeout', 30)
        self.rate_limit = self.config.get('rate_limit', self.DEFAULT_RATE_LIMIT)
        self.session = requests.Session()
        
        # Rate limiting
        self._request_times: List[datetime] = []
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        minute_ago = now - timedelta(minutes=1)
        self._request_times = [t for t in self._request_times if t > minute_ago]
        
        # Check minute limit
        if len(self._request_times) >= self.rate_limit['requests_per_minute']:
            sleep_time = 60 - (now - self._request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self._request_times = []
        
        self._request_times.append(now)
    
    def _map_timeframe(self, timeframe: str) -> tuple[str, str]:
        """
        Map standard timeframe to Alpha Vantage function and interval.
        
        Returns:
            Tuple of (function_name, interval)
        """
        # Alpha Vantage supports: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        if timeframe in ['1d', 'daily']:
            return ('TIME_SERIES_DAILY', None)
        elif timeframe in ['1wk', 'weekly']:
            return ('TIME_SERIES_WEEKLY', None)
        elif timeframe in ['1mo', 'monthly']:
            return ('TIME_SERIES_MONTHLY', None)
        elif timeframe in ['1m', '1min']:
            return ('TIME_SERIES_INTRADAY', '1min')
        elif timeframe in ['5m', '5min']:
            return ('TIME_SERIES_INTRADAY', '5min')
        elif timeframe in ['15m', '15min']:
            return ('TIME_SERIES_INTRADAY', '15min')
        elif timeframe in ['30m', '30min']:
            return ('TIME_SERIES_INTRADAY', '30min')
        elif timeframe in ['60m', '1h', '60min']:
            return ('TIME_SERIES_INTRADAY', '60min')
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Alpha Vantage.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            DataFrame with OHLCV data
        
        Raises:
            ValueError: If API key not configured or timeframe invalid
            ConnectionError: If unable to fetch data
        """
        fetch_start = time.time()
        logger.info(f"[ALPHA VANTAGE] Fetching {symbol} from {start_date.date()} to {end_date.date()}, timeframe: {timeframe}")
        
        if not self.api_key:
            logger.error(f"[ALPHA VANTAGE ERROR] API key not configured for {symbol}")
            raise ValueError("Alpha Vantage API key not configured")
        
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.info(f"[ALPHA VANTAGE CACHE HIT] {symbol}: Using {len(cached_data)} cached rows")
            return cached_data
        
        try:
            # Enforce rate limiting
            rate_limit_start = time.time()
            self._enforce_rate_limit()
            rate_limit_duration = time.time() - rate_limit_start
            if rate_limit_duration > 0.1:
                logger.info(f"[ALPHA VANTAGE RATE LIMIT] Waited {rate_limit_duration:.2f}s for rate limiting")
            
            # Map timeframe
            function, interval = self._map_timeframe(timeframe)
            logger.debug(f"[ALPHA VANTAGE] {symbol}: Using function={function}, interval={interval}")
            
            # Build request parameters
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': '***',  # Don't log the actual key
                'outputsize': 'full',
                'datatype': 'json'
            }
            
            if interval:
                params['interval'] = interval
            
            logger.debug(f"[ALPHA VANTAGE REQUEST] URL: {self.BASE_URL}")
            logger.debug(f"[ALPHA VANTAGE REQUEST] Params: {params}")
            
            # Make request
            request_start = time.time()
            response = self.session.get(
                self.BASE_URL,
                params={**params, 'apikey': self.api_key},  # Use real key for request
                timeout=self.timeout
            )
            request_duration = time.time() - request_start
            
            logger.info(f"[ALPHA VANTAGE RESPONSE] {symbol}: HTTP {response.status_code} in {request_duration:.2f}s, Size: {len(response.content)} bytes")
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"[ALPHA VANTAGE RESPONSE] {symbol}: Response keys: {list(data.keys())}")
            
            # Check for API errors
            if 'Error Message' in data:
                error_msg = data['Error Message']
                logger.error(f"[ALPHA VANTAGE API ERROR] {symbol}: {error_msg}")
                raise ConnectionError(f"Alpha Vantage error: {error_msg}")
            
            if 'Note' in data:
                # Rate limit message
                note_msg = data['Note']
                logger.warning(f"[ALPHA VANTAGE RATE LIMIT] {symbol}: {note_msg}")
                raise ConnectionError("Alpha Vantage rate limit exceeded")
            
            if 'Information' in data:
                info_msg = data['Information']
                logger.warning(f"[ALPHA VANTAGE INFO] {symbol}: {info_msg}")
            
            # Parse response
            parse_start = time.time()
            df = self._parse_response(data, function)
            parse_duration = time.time() - parse_start
            
            if df.empty:
                logger.warning(f"[ALPHA VANTAGE EMPTY] {symbol}: Empty dataframe after parsing (parse time: {parse_duration:.2f}s)")
                return pd.DataFrame()
            
            logger.debug(f"[ALPHA VANTAGE PARSE] {symbol}: Parsed {len(df)} rows in {parse_duration:.2f}s")
            
            # Filter by date range
            rows_before = len(df)
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            rows_after = len(df)
            
            if rows_before != rows_after:
                logger.debug(f"[ALPHA VANTAGE FILTER] {symbol}: Filtered {rows_before} -> {rows_after} rows for date range")
            
            # Add to cache
            self.add_to_cache(symbol, start_date, end_date, timeframe, df)
            
            total_duration = time.time() - fetch_start
            logger.info(f"[ALPHA VANTAGE SUCCESS] {symbol}: {len(df)} rows in {total_duration:.2f}s (request: {request_duration:.2f}s, parse: {parse_duration:.2f}s)")
            return df
            
        except Exception as e:
            total_duration = time.time() - fetch_start
            logger.error(f"[ALPHA VANTAGE FAILED] {symbol}: {type(e).__name__}: {e} (elapsed: {total_duration:.2f}s)")
            raise ConnectionError(f"Failed to fetch data from Alpha Vantage: {e}")
    
    def _parse_response(self, data: Dict, function: str) -> pd.DataFrame:
        """Parse Alpha Vantage API response."""
        try:
            # Find the time series key
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key or time_series_key not in data:
                logger.error(f"No time series data found. Response keys: {data.keys()}")
                return pd.DataFrame()
            
            time_series = data[time_series_key]
            
            if not time_series:
                return pd.DataFrame()
            
            # Parse into DataFrame
            rows = []
            for timestamp, values in time_series.items():
                row = {
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': float(values.get('5. volume', 0))
                }
                rows.append((timestamp, row))
            
            # Create DataFrame
            df = pd.DataFrame([r[1] for r in rows], index=[r[0] for r in rows])
            df.index = pd.to_datetime(df.index)
            df.index.name = 'Date'
            
            # Sort by date
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return pd.DataFrame()
    
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets.
        
        Note: Alpha Vantage supports all US stocks, some international,
        forex pairs, and cryptocurrencies. Returns empty list to indicate
        validation should be done via API calls.
        
        Returns:
            Empty list (validation via API)
        """
        return []
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get supported timeframes.
        
        Returns:
            List of supported interval strings
        """
        return [
            '1m', '1min',
            '5m', '5min',
            '15m', '15min',
            '30m', '30min',
            '60m', '1h', '60min',
            '1d', 'daily',
            '1wk', 'weekly',
            '1mo', 'monthly'
        ]
    
    def is_available(self) -> bool:
        """
        Check if Alpha Vantage API is available.
        
        Returns:
            True if service is reachable and API key is configured
        """
        if not self.api_key:
            return False
        
        try:
            # Simple query to check availability
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': 'AAPL',
                'apikey': self.api_key,
                'outputsize': 'compact',
                'datatype': 'json'
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=5)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check for error messages
            if 'Error Message' in data or 'Note' in data:
                return False
            
            return True
            
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
            start_date = end_date - timedelta(days=7)
            
            data = self.fetch_data(symbol, start_date, end_date, timeframe='1d')
            
            if data is not None and len(data) > 0:
                return float(data['close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    def get_supported_asset_types(self) -> Set[AssetType]:
        """
        Get supported asset types.
        
        Returns:
            Set of supported AssetType values
        """
        return {
            AssetType.EQUITY,
            AssetType.FX,
            AssetType.CRYPTO,
        }
    
    @classmethod
    def requires_authentication(cls) -> bool:
        """Alpha Vantage requires an API key."""
        return True
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Alpha Vantage data source. Provides stock, forex, and crypto data. "
            "Free tier: 500 requests/day, 5 requests/minute. "
            "Requires API key from alphavantage.co."
        )
