"""
Twelve Data source implementation.

This module provides another alternative data source using Twelve Data's API.
Twelve Data offers a free tier with 800 requests/day, making it a good
alternative when other sources fail.

API Key: Get free key at https://twelvedata.com/pricing
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import time

import pandas as pd
import requests
from loguru import logger

from ..core.base_data_source import BaseDataSource
from ..core.types import AssetType


class TwelveDataSource(BaseDataSource):
    """
    Data source for Twelve Data API.
    
    Twelve Data provides stock, forex, crypto, and ETF data with a free tier.
    Free tier limits: 800 requests/day, 8 requests/minute.
    
    Example:
        >>> source = TwelveDataSource({
        ...     'api_key': 'YOUR_API_KEY',
        ...     'cache_enabled': True
        ... })
        >>> data = source.fetch_data('AAPL', start_date, end_date)
    """
    
    BASE_URL = "https://api.twelvedata.com"
    
    # Free tier rate limits
    DEFAULT_RATE_LIMIT = {
        'requests_per_minute': 8,
        'requests_per_day': 800
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Twelve Data source.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - api_key: Twelve Data API key (required, or set TWELVEDATA_API_KEY env var)
                   - cache_enabled: Enable caching (default: True)
                   - timeout: Request timeout in seconds (default: 30)
                   - rate_limit: Custom rate limit dict (optional)
        """
        super().__init__(config)
        
        # Get API key from config or environment
        import os
        self.api_key = self.config.get('api_key') or os.environ.get('TWELVEDATA_API_KEY')
        
        if not self.api_key:
            logger.warning("Twelve Data API key not configured. Set 'api_key' in config or TWELVEDATA_API_KEY env var")
        
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
    
    def _map_timeframe(self, timeframe: str) -> str:
        """
        Map standard timeframe to Twelve Data interval.
        
        Twelve Data uses: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month
        """
        mapping = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1h',
            '60m': '1h',
            '2h': '2h',
            '4h': '4h',
            '1d': '1day',
            'daily': '1day',
            '1wk': '1week',
            'weekly': '1week',
            '1mo': '1month',
            'monthly': '1month'
        }
        
        if timeframe in mapping:
            return mapping[timeframe]
        
        # Try as-is
        return timeframe
    
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Twelve Data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            DataFrame with OHLCV data
        
        Raises:
            ValueError: If API key not configured
            ConnectionError: If unable to fetch data
        """
        if not self.api_key:
            raise ValueError("Twelve Data API key not configured")
        
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.debug(f"Using cached data for {symbol}")
            return cached_data
        
        try:
            logger.info(f"Fetching {symbol} from Twelve Data: {start_date} to {end_date}")
            
            # Enforce rate limiting
            self._enforce_rate_limit()
            
            # Map timeframe
            interval = self._map_timeframe(timeframe)
            
            # Build request parameters
            params = {
                'symbol': symbol,
                'interval': interval,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'apikey': self.api_key,
                'format': 'JSON',
                'outputsize': 5000  # Maximum output size
            }
            
            # Make request
            url = f"{self.BASE_URL}/time_series"
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'status' in data and data['status'] == 'error':
                error_msg = data.get('message', 'Unknown error')
                raise ConnectionError(f"Twelve Data error: {error_msg}")
            
            # Parse response
            df = self._parse_response(data)
            
            if df.empty:
                logger.warning(f"Empty dataframe after parsing for {symbol}")
                return pd.DataFrame()
            
            # Add to cache
            self.add_to_cache(symbol, start_date, end_date, timeframe, df)
            
            logger.debug(f"Successfully fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise ConnectionError(f"Failed to fetch data from Twelve Data: {e}")
    
    def _parse_response(self, data: Dict) -> pd.DataFrame:
        """Parse Twelve Data API response."""
        try:
            if 'values' not in data:
                logger.error(f"No 'values' in response. Keys: {data.keys()}")
                return pd.DataFrame()
            
            values = data['values']
            
            if not values:
                return pd.DataFrame()
            
            # Parse into DataFrame
            rows = []
            for item in values:
                row = {
                    'open': float(item.get('open', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'close': float(item.get('close', 0)),
                    'volume': float(item.get('volume', 0))
                }
                rows.append((item['datetime'], row))
            
            # Create DataFrame
            df = pd.DataFrame([r[1] for r in rows], index=[r[0] for r in rows])
            df.index = pd.to_datetime(df.index)
            df.index.name = 'Date'
            
            # Sort by date (Twelve Data returns newest first)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return pd.DataFrame()
    
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets.
        
        Note: Twelve Data supports stocks, ETFs, forex, and crypto.
        Returns empty list to indicate validation should be done via API calls.
        
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
            '1h', '60m',
            '2h',
            '4h',
            '1d', 'daily', '1day',
            '1wk', 'weekly', '1week',
            '1mo', 'monthly', '1month'
        ]
    
    def is_available(self) -> bool:
        """
        Check if Twelve Data API is available.
        
        Returns:
            True if service is reachable and API key is configured
        """
        if not self.api_key:
            return False
        
        try:
            # Simple query to check availability
            params = {
                'symbol': 'AAPL',
                'interval': '1day',
                'outputsize': 1,
                'apikey': self.api_key,
                'format': 'JSON'
            }
            
            url = f"{self.BASE_URL}/time_series"
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check for error messages
            if 'status' in data and data['status'] == 'error':
                return False
            
            return 'values' in data
            
        except Exception:
            return False
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent price using real-time quote endpoint.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Latest close price or None
        """
        if not self.api_key:
            return None
        
        try:
            self._enforce_rate_limit()
            
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            url = f"{self.BASE_URL}/quote"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'close' in data:
                return float(data['close'])
            
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
        """Twelve Data requires an API key."""
        return True
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Twelve Data source. Provides stock, ETF, forex, and crypto data. "
            "Free tier: 800 requests/day, 8 requests/minute. "
            "Requires API key from twelvedata.com."
        )
