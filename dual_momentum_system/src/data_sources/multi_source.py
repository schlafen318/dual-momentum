"""
Multi-source data provider with automatic failover.

This module provides a data source that can try multiple providers
in order, automatically falling back to alternatives if the primary
source fails. This ensures maximum reliability for data fetching.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import time

import pandas as pd
from loguru import logger

from ..core.base_data_source import BaseDataSource
from ..core.types import AssetType


class MultiSourceDataProvider(BaseDataSource):
    """
    Data source that tries multiple providers with automatic failover.
    
    This provider maintains a list of data sources and tries them in order
    until one succeeds. This provides high reliability and availability.
    
    Example:
        >>> from .yahoo_finance_direct import YahooFinanceDirectSource
        >>> from .alpha_vantage import AlphaVantageSource
        >>> 
        >>> multi = MultiSourceDataProvider({
        ...     'sources': [
        ...         YahooFinanceDirectSource(),
        ...         AlphaVantageSource({'api_key': 'YOUR_KEY'})
        ...     ]
        ... })
        >>> 
        >>> # Will try Yahoo first, then Alpha Vantage if Yahoo fails
        >>> data = multi.fetch_data('AAPL', start, end)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize multi-source data provider.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - sources: List of data source instances (required)
                   - retry_on_empty: Retry if data is empty (default: True)
                   - log_failures: Log failed attempts (default: True)
                   - cache_enabled: Enable caching (default: True)
        """
        super().__init__(config)
        
        self.sources = self.config.get('sources', [])
        if not self.sources:
            raise ValueError("MultiSourceDataProvider requires at least one data source")
        
        self.retry_on_empty = self.config.get('retry_on_empty', True)
        self.log_failures = self.config.get('log_failures', True)
        
        logger.info(f"Initialized MultiSourceDataProvider with {len(self.sources)} sources")
        for i, source in enumerate(self.sources):
            logger.info(f"  Source {i+1}: {source.get_name()}")
    
    def fetch_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch data with automatic failover to alternative sources.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            DataFrame with OHLCV data
        
        Raises:
            ConnectionError: If all sources fail
        """
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.debug(f"Using cached data for {symbol}")
            return cached_data
        
        errors = []
        
        for i, source in enumerate(self.sources):
            try:
                logger.debug(f"Trying source {i+1}/{len(self.sources)}: {source.get_name()}")
                
                # Validate timeframe support (but skip is_available() check here
                # to avoid making extra HTTP requests for each symbol)
                if not source.validate_timeframe(timeframe):
                    logger.warning(f"Source {source.get_name()} doesn't support timeframe {timeframe}")
                    errors.append(f"{source.get_name()}: Timeframe not supported")
                    continue
                
                # Attempt to fetch data
                # The actual fetch will fail naturally if the source is unavailable,
                # so we don't need a separate is_available() check that makes extra requests
                data = source.fetch_data(symbol, start_date, end_date, timeframe)
                
                # Check if data is empty
                if data is None or data.empty:
                    if self.retry_on_empty:
                        logger.warning(f"Source {source.get_name()} returned empty data for {symbol}")
                        errors.append(f"{source.get_name()}: Empty data")
                        continue
                
                # Success!
                logger.info(f"✓ Successfully fetched {len(data)} rows for {symbol} from {source.get_name()}")
                
                # Add to cache
                self.add_to_cache(symbol, start_date, end_date, timeframe, data)
                
                return data
                
            except Exception as e:
                if self.log_failures:
                    logger.warning(f"Source {source.get_name()} failed for {symbol}: {e}")
                errors.append(f"{source.get_name()}: {str(e)}")
                continue
        
        # All sources failed
        error_msg = f"All {len(self.sources)} data sources failed for {symbol}:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ConnectionError(error_msg)
    
    def fetch_multiple(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols with failover.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        logger.info(f"Fetching {len(symbols)} symbols with multi-source failover")
        
        result = {}
        failed = []
        
        for symbol in symbols:
            try:
                df = self.fetch_data(symbol, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    result[symbol] = df
                else:
                    failed.append(symbol)
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                failed.append(symbol)
                continue
        
        logger.info(f"Successfully fetched {len(result)}/{len(symbols)} symbols")
        if failed:
            logger.warning(f"Failed symbols: {', '.join(failed)}")
        
        return result
    
    def get_supported_assets(self) -> List[str]:
        """
        Get union of all supported assets from all sources.
        
        Returns:
            Combined list of supported assets
        """
        all_assets = set()
        for source in self.sources:
            assets = source.get_supported_assets()
            if assets:
                all_assets.update(assets)
        
        return list(all_assets) if all_assets else []
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get intersection of supported timeframes (only common ones).
        
        Returns:
            List of timeframes supported by all sources
        """
        if not self.sources:
            return []
        
        # Start with first source's timeframes
        common_timeframes = set(self.sources[0].get_supported_timeframes())
        
        # Intersect with all other sources
        for source in self.sources[1:]:
            common_timeframes &= set(source.get_supported_timeframes())
        
        return list(common_timeframes)
    
    def is_available(self) -> bool:
        """
        Check if at least one source is available.
        
        Returns:
            True if any source is available
        """
        for source in self.sources:
            if source.is_available():
                return True
        return False
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get latest price with failover.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Latest price or None
        """
        for source in self.sources:
            try:
                price = source.get_latest_price(symbol)
                if price is not None:
                    return price
            except Exception:
                continue
        return None
    
    def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get asset info with failover.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Asset info dictionary or None
        """
        for source in self.sources:
            try:
                info = source.get_asset_info(symbol)
                if info is not None:
                    return info
            except Exception:
                continue
        return None
    
    def get_supported_asset_types(self) -> Set[AssetType]:
        """
        Get union of all supported asset types.
        
        Returns:
            Set of all supported asset types
        """
        all_types = set()
        for source in self.sources:
            all_types.update(source.get_supported_asset_types())
        return all_types
    
    def get_source_status(self) -> Dict[str, bool]:
        """
        Get availability status of all sources.
        
        Returns:
            Dictionary mapping source names to availability status
        """
        status = {}
        for source in self.sources:
            try:
                status[source.get_name()] = source.is_available()
            except Exception:
                status[source.get_name()] = False
        return status
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Multi-source data provider with automatic failover. "
            "Tries multiple data sources in order until one succeeds, "
            "providing maximum reliability and uptime."
        )
