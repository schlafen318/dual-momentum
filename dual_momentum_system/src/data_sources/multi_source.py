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
        fetch_start = time.time()
        logger.info(f"[MULTI-SOURCE] Fetching {symbol} from {len(self.sources)} sources with failover")
        logger.debug(f"[MULTI-SOURCE] Available sources: {[s.get_name() for s in self.sources]}")
        
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.info(f"[MULTI-SOURCE CACHE HIT] {symbol}: Using cached data with {len(cached_data)} rows")
            return cached_data
        else:
            logger.debug(f"[MULTI-SOURCE CACHE MISS] {symbol}: No cached data, trying sources")
        
        errors = []
        attempt_details = []
        
        for i, source in enumerate(self.sources):
            source_name = source.get_name()
            attempt_start = time.time()
            
            try:
                logger.info(f"[FAILOVER ATTEMPT {i+1}/{len(self.sources)}] Trying {source_name} for {symbol}")
                
                # Validate timeframe support (but skip is_available() check here
                # to avoid making extra HTTP requests for each symbol)
                if not source.validate_timeframe(timeframe):
                    reason = f"Timeframe '{timeframe}' not supported"
                    attempt_duration = time.time() - attempt_start
                    logger.warning(f"[FAILOVER SKIP] {source_name}: {reason} (checked in {attempt_duration:.2f}s)")
                    errors.append(f"{source_name}: {reason}")
                    attempt_details.append({
                        'source': source_name,
                        'status': 'skipped',
                        'reason': reason,
                        'duration': attempt_duration
                    })
                    continue
                
                # Attempt to fetch data
                # The actual fetch will fail naturally if the source is unavailable,
                # so we don't need a separate is_available() check that makes extra requests
                logger.debug(f"[FAILOVER ATTEMPT] {source_name}: Calling fetch_data()...")
                data = source.fetch_data(symbol, start_date, end_date, timeframe)
                attempt_duration = time.time() - attempt_start
                
                # Check if data is empty
                if data is None or data.empty:
                    if self.retry_on_empty:
                        reason = "Empty data returned"
                        logger.warning(f"[FAILOVER FAILED] {source_name}: {reason} (attempt took {attempt_duration:.2f}s)")
                        errors.append(f"{source_name}: {reason}")
                        attempt_details.append({
                            'source': source_name,
                            'status': 'empty',
                            'reason': reason,
                            'duration': attempt_duration
                        })
                        continue
                    else:
                        logger.info(f"[FAILOVER EMPTY] {source_name}: Empty data but retry_on_empty=False, accepting result")
                
                # Success!
                total_duration = time.time() - fetch_start
                logger.info(f"[FAILOVER SUCCESS] ✓ {symbol}: Fetched {len(data)} rows from {source_name} (source: {attempt_duration:.2f}s, total: {total_duration:.2f}s)")
                logger.info(f"[FAILOVER SUCCESS] Data range: {data.index[0]} to {data.index[-1]}")
                
                attempt_details.append({
                    'source': source_name,
                    'status': 'success',
                    'rows': len(data),
                    'duration': attempt_duration
                })
                
                # Log attempt summary
                if len(attempt_details) > 1:
                    logger.info(f"[FAILOVER SUMMARY] Succeeded on attempt {i+1}/{len(self.sources)} after trying: {', '.join([a['source'] for a in attempt_details])}")
                
                # Add to cache
                self.add_to_cache(symbol, start_date, end_date, timeframe, data)
                
                return data
                
            except ValueError as e:
                # Configuration or validation errors
                attempt_duration = time.time() - attempt_start
                error_msg = str(e)
                logger.warning(f"[FAILOVER VALIDATION ERROR] {source_name}: {error_msg} (attempt took {attempt_duration:.2f}s)")
                errors.append(f"{source_name}: Validation - {error_msg}")
                attempt_details.append({
                    'source': source_name,
                    'status': 'validation_error',
                    'error': error_msg,
                    'duration': attempt_duration
                })
                continue
                
            except ConnectionError as e:
                # Network or API errors
                attempt_duration = time.time() - attempt_start
                error_msg = str(e)[:200]  # Truncate long error messages
                if self.log_failures:
                    logger.warning(f"[FAILOVER CONNECTION ERROR] {source_name}: {error_msg} (attempt took {attempt_duration:.2f}s)")
                errors.append(f"{source_name}: Connection - {error_msg}")
                attempt_details.append({
                    'source': source_name,
                    'status': 'connection_error',
                    'error': error_msg,
                    'duration': attempt_duration
                })
                continue
                
            except Exception as e:
                # Unexpected errors
                attempt_duration = time.time() - attempt_start
                error_type = type(e).__name__
                error_msg = str(e)[:200]
                if self.log_failures:
                    logger.warning(f"[FAILOVER ERROR] {source_name}: {error_type}: {error_msg} (attempt took {attempt_duration:.2f}s)")
                    logger.debug(f"[FAILOVER ERROR] Full error for {source_name}:", exc_info=True)
                errors.append(f"{source_name}: {error_type} - {error_msg}")
                attempt_details.append({
                    'source': source_name,
                    'status': 'error',
                    'error_type': error_type,
                    'error': error_msg,
                    'duration': attempt_duration
                })
                continue
        
        # All sources failed
        total_duration = time.time() - fetch_start
        logger.error(f"[FAILOVER EXHAUSTED] All {len(self.sources)} sources failed for {symbol} after {total_duration:.2f}s")
        logger.error(f"[FAILOVER EXHAUSTED] Attempt details:")
        for detail in attempt_details:
            logger.error(f"[FAILOVER EXHAUSTED]   - {detail['source']}: {detail['status']} ({detail['duration']:.2f}s)")
        
        error_msg = f"All {len(self.sources)} data sources failed for {symbol}:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(f"[FAILOVER EXHAUSTED] Detailed errors:\n{error_msg}")
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
        batch_start = time.time()
        logger.info(f"[MULTI-BATCH START] Fetching {len(symbols)} symbols with multi-source failover")
        logger.info(f"[MULTI-BATCH START] Symbols: {', '.join(symbols)}")
        logger.info(f"[MULTI-BATCH START] Sources: {', '.join([s.get_name() for s in self.sources])}")
        
        result = {}
        failed = []
        source_usage = {source.get_name(): 0 for source in self.sources}
        
        for i, symbol in enumerate(symbols):
            symbol_start = time.time()
            try:
                logger.info(f"[MULTI-BATCH] Processing {i+1}/{len(symbols)}: {symbol}")
                df = self.fetch_data(symbol, start_date, end_date, timeframe)
                
                if df is not None and not df.empty:
                    result[symbol] = df
                    symbol_duration = time.time() - symbol_start
                    logger.info(f"[MULTI-BATCH SUCCESS] {symbol}: {len(df)} rows ({symbol_duration:.2f}s)")
                else:
                    failed.append((symbol, "Empty data from all sources"))
                    logger.warning(f"[MULTI-BATCH FAILED] {symbol}: Empty data")
                    
            except ConnectionError as e:
                symbol_duration = time.time() - symbol_start
                error_msg = str(e)[:200]
                failed.append((symbol, error_msg))
                logger.error(f"[MULTI-BATCH FAILED] {symbol}: {error_msg} ({symbol_duration:.2f}s)")
                continue
                
            except Exception as e:
                symbol_duration = time.time() - symbol_start
                error_type = type(e).__name__
                error_msg = str(e)[:200]
                failed.append((symbol, f"{error_type}: {error_msg}"))
                logger.error(f"[MULTI-BATCH ERROR] {symbol}: {error_type}: {error_msg} ({symbol_duration:.2f}s)")
                continue
        
        batch_duration = time.time() - batch_start
        success_rate = (len(result) / len(symbols) * 100) if symbols else 0
        
        logger.info(f"[MULTI-BATCH COMPLETE] Successfully fetched {len(result)}/{len(symbols)} symbols ({success_rate:.1f}%) in {batch_duration:.2f}s")
        logger.info(f"[MULTI-BATCH COMPLETE] Average time per symbol: {batch_duration/len(symbols):.2f}s")
        
        if failed:
            logger.warning(f"[MULTI-BATCH FAILED] Failed to fetch {len(failed)} symbols:")
            for symbol, reason in failed:
                logger.warning(f"[MULTI-BATCH FAILED]   - {symbol}: {reason}")
        
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
