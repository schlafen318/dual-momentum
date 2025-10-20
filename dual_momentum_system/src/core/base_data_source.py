"""
Base class for data source plugins.

This module defines the abstract interface for data source implementations.
Data sources handle fetching historical and real-time data from various providers
(Yahoo Finance, CCXT, custom APIs, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from loguru import logger

from .types import AssetType


class BaseDataSource(ABC):
    """
    Abstract base class for data source plugins.
    
    Data source plugins fetch price data from various providers.
    Each implementation handles the specific API/protocol of its provider.
    
    Example:
        >>> class YahooFinanceSource(BaseDataSource):
        ...     def fetch_data(self, symbol, start_date, end_date, timeframe='1d'):
        ...         import yfinance as yf
        ...         ticker = yf.Ticker(symbol)
        ...         return ticker.history(start=start_date, end=end_date, interval=timeframe)
        ...     
        ...     # ... implement other required methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data source.
        
        Args:
            config: Configuration dictionary. May include:
                   - API keys/credentials
                   - Rate limits
                   - Cache settings
                   - Retry policies
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self._validate_config()
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_enabled = self.config.get('cache_enabled', True)
        self._initialized = True
    
    @abstractmethod
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical price data.
        
        This method should return OHLCV data as a pandas DataFrame.
        The DataFrame must have a DatetimeIndex and columns:
        'open', 'high', 'low', 'close', 'volume' (case-insensitive).
        
        Args:
            symbol: Asset symbol (format may vary by provider)
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe/interval
                      Common values: '1d', '1h', '5m', '1m'
                      
        Returns:
            DataFrame with OHLCV data indexed by timestamp
            
        Raises:
            ValueError: If symbol or timeframe is invalid
            ConnectionError: If unable to connect to data provider
            
        Example:
            >>> data = source.fetch_data('AAPL', 
            ...                          datetime(2023, 1, 1), 
            ...                          datetime(2023, 12, 31),
            ...                          timeframe='1d')
            >>> print(data.head())
                        open    high     low   close    volume
            2023-01-03  130.28  130.90  124.17  125.07  112117500
        """
        pass
    
    @abstractmethod
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported asset symbols.
        
        For large universes (e.g., all stocks), this may return
        a subset or reference to where the full list can be obtained.
        
        Returns:
            List of supported asset symbols
            
        Example:
            >>> symbols = source.get_supported_assets()
            >>> print(len(symbols))
            5000
            >>> print(symbols[:3])
            ['AAPL', 'MSFT', 'GOOGL']
        """
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes.
        
        Returns:
            List of supported timeframe strings
            
        Example:
            >>> timeframes = source.get_supported_timeframes()
            >>> print(timeframes)
            ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the data source is currently available.
        
        This method can verify:
        - Network connectivity
        - API authentication
        - Service status
        
        Returns:
            True if data source is available, False otherwise
            
        Example:
            >>> if source.is_available():
            ...     data = source.fetch_data(...)
        """
        return True
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent price for an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Latest price, or None if unavailable
            
        Example:
            >>> price = source.get_latest_price('AAPL')
            >>> print(price)
            150.25
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)  # Get recent data
            data = self.fetch_data(symbol, start_date, end_date, timeframe='1d')
            if data is not None and len(data) > 0:
                return float(data['close'].iloc[-1])
        except Exception:
            pass
        return None
    
    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Default implementation calls fetch_data for each symbol.
        Override for batch-optimized implementations.
        
        Args:
            symbols: List of asset symbols
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            
        Returns:
            Dictionary mapping symbols to DataFrames
            
        Example:
            >>> data = source.fetch_multiple(['AAPL', 'MSFT'], 
            ...                               datetime(2023, 1, 1),
            ...                               datetime(2023, 12, 31))
            >>> print(data.keys())
            dict_keys(['AAPL', 'MSFT'])
        """
        logger.info(f"[BASE FETCH_MULTIPLE] Fetching {len(symbols)} symbols using default sequential method")
        result = {}
        failed = []
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    result[symbol] = df
                else:
                    failed.append(symbol)
                    logger.warning(f"[BASE FETCH_MULTIPLE] {symbol}: Empty result")
            except Exception as e:
                failed.append(symbol)
                logger.warning(f"[BASE FETCH_MULTIPLE] Failed to fetch {symbol}: {type(e).__name__}: {e}")
                continue
        
        logger.info(f"[BASE FETCH_MULTIPLE] Completed: {len(result)} succeeded, {len(failed)} failed")
        return result
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported by this data source.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
            
        Example:
            >>> source.validate_symbol('AAPL')
            True
            >>> source.validate_symbol('INVALID123')
            False
        """
        supported = self.get_supported_assets()
        if not supported:  # If list is empty, assume all symbols are potentially valid
            return True
        return symbol in supported
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate if a timeframe is supported.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            True if timeframe is valid, False otherwise
            
        Example:
            >>> source.validate_timeframe('1d')
            True
            >>> source.validate_timeframe('3s')
            False
        """
        supported = self.get_supported_timeframes()
        return timeframe in supported
    
    def get_data_range(self, symbol: str) -> Optional[tuple[datetime, datetime]]:
        """
        Get the available date range for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Tuple of (earliest_date, latest_date), or None if unavailable
            
        Example:
            >>> date_range = source.get_data_range('AAPL')
            >>> print(date_range)
            (datetime(1980, 12, 12), datetime(2023, 10, 17))
        """
        return None  # Override in subclasses if available
    
    def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get additional information about an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Dictionary with asset information, or None if unavailable
            
        Example:
            >>> info = source.get_asset_info('AAPL')
            >>> print(info['longName'])
            'Apple Inc.'
        """
        return None  # Override in subclasses if available
    
    def get_supported_asset_types(self) -> Set[AssetType]:
        """
        Get the asset types supported by this data source.
        
        Returns:
            Set of AssetType enums
            
        Example:
            >>> asset_types = source.get_supported_asset_types()
            >>> print(asset_types)
            {AssetType.EQUITY, AssetType.ETF}
        """
        return set()  # Override in subclasses
    
    def supports_asset_type(self, asset_type: AssetType) -> bool:
        """
        Check if this data source supports a specific asset type.
        
        Args:
            asset_type: Asset type to check
            
        Returns:
            True if supported, False otherwise
        """
        supported_types = self.get_supported_asset_types()
        if not supported_types:  # If empty, assume all types supported
            return True
        return asset_type in supported_types
    
    def get_cache_key(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> str:
        """
        Generate cache key for data request.
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe
            
        Returns:
            Cache key string
        """
        # Handle both datetime and date objects
        start = start_date.date() if hasattr(start_date, 'date') and callable(start_date.date) else start_date
        end = end_date.date() if hasattr(end_date, 'date') and callable(end_date.date) else end_date
        return f"{symbol}_{start}_{end}_{timeframe}"
    
    def get_from_cache(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve data from cache if available.
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe
            
        Returns:
            Cached DataFrame or None
        """
        if not self._cache_enabled:
            logger.debug(f"[CACHE DISABLED] Caching is disabled for {self.get_name()}")
            return None
        
        cache_key = self.get_cache_key(symbol, start_date, end_date, timeframe)
        cached_data = self._cache.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"[CACHE HIT] {symbol}: Found in cache (key: {cache_key}, rows: {len(cached_data)})")
        else:
            logger.debug(f"[CACHE MISS] {symbol}: Not in cache (key: {cache_key})")
        
        return cached_data
    
    def add_to_cache(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
        data: pd.DataFrame
    ) -> None:
        """
        Add data to cache.
        
        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe
            data: DataFrame to cache
        """
        if not self._cache_enabled:
            logger.debug(f"[CACHE DISABLED] Not caching {symbol} (caching disabled)")
            return
        
        cache_key = self.get_cache_key(symbol, start_date, end_date, timeframe)
        self._cache[cache_key] = data.copy()
        
        # Calculate cache statistics
        memory_usage = data.memory_usage(deep=True).sum() / 1024  # KB
        logger.debug(f"[CACHE ADD] {symbol}: Cached {len(data)} rows (~{memory_usage:.1f} KB, key: {cache_key})")
        logger.debug(f"[CACHE STATS] Total cached items: {len(self._cache)}")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        items_before = len(self._cache)
        self._cache.clear()
        logger.info(f"[CACHE CLEAR] Cleared {items_before} cached items from {self.get_name()}")
    
    def get_rate_limit(self) -> Optional[Dict[str, Any]]:
        """
        Get rate limit information for this data source.
        
        Returns:
            Dictionary with rate limit info, or None
            
        Example:
            >>> limits = source.get_rate_limit()
            >>> print(limits)
            {'requests_per_minute': 60, 'requests_per_day': 2000}
        """
        return self.config.get('rate_limit')
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Override this method to add custom validation logic.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Default implementation does nothing
        # Override in subclasses for custom validation
        pass
    
    @classmethod
    def get_name(cls) -> str:
        """
        Return the data source name.
        
        Returns:
            Class name as string
            
        Example:
            >>> YahooFinanceSource.get_name()
            'YahooFinanceSource'
        """
        return cls.__name__
    
    @classmethod
    def get_version(cls) -> str:
        """
        Return the plugin version.
        
        Override to provide version information.
        
        Returns:
            Version string
        """
        return "1.0.0"
    
    @classmethod
    def requires_authentication(cls) -> bool:
        """
        Indicate if this data source requires authentication.
        
        Returns:
            True if authentication required, False otherwise
        """
        return False
    
    def __repr__(self) -> str:
        """String representation of the data source."""
        return f"{self.get_name()}(available={self.is_available()})"
