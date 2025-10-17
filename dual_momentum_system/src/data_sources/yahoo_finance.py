"""
Yahoo Finance data source plugin.

Provides historical price data using the yfinance library.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yfinance as yf
from loguru import logger

from ..core.base_data_source import BaseDataSource
from ..core.types import AssetType


class YahooFinanceSource(BaseDataSource):
    """
    Data source for Yahoo Finance.
    
    Provides access to historical price data for equities, ETFs,
    indices, and other assets available on Yahoo Finance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Yahoo Finance data source.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - cache_enabled: Enable caching (default: True)
                   - auto_adjust: Use adjusted prices (default: True)
                   - validate_symbols: Validate symbols before fetching (default: False)
        """
        super().__init__(config)
        
        self.auto_adjust = self.config.get('auto_adjust', True)
        self.validate_symbols = self.config.get('validate_symbols', False)
    
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
            logger.info(f"Fetching {symbol} from Yahoo Finance: {start_date} to {end_date}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=timeframe,
                auto_adjust=self.auto_adjust
            )
            
            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Normalize column names to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_cols if col not in data.columns]
            
            if missing:
                logger.error(f"Missing columns for {symbol}: {missing}")
                return pd.DataFrame()
            
            # Add to cache
            self.add_to_cache(symbol, start_date, end_date, timeframe, data)
            
            logger.debug(f"Successfully fetched {len(data)} rows for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise ConnectionError(f"Failed to fetch data from Yahoo Finance: {e}")
    
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported assets.
        
        Note: Yahoo Finance supports a vast universe of symbols.
        This returns an empty list to indicate all symbols are potentially valid.
        Use validate_symbol() to check specific symbols.
        
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
            # Try to fetch a well-known symbol
            test_data = yf.download('SPY', period='1d', progress=False)
            return not test_data.empty
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
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try various price fields
            for field in ['currentPrice', 'regularMarketPrice', 'previousClose']:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            # Fallback to recent history
            return super().get_latest_price(symbol)
            
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
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'exchange': info.get('exchange'),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap'),
                'description': info.get('longBusinessSummary'),
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
            ticker = yf.Ticker(symbol)
            
            # Fetch all available history (max period)
            data = ticker.history(period='max')
            
            if data.empty:
                return None
            
            return (
                data.index[0].to_pydatetime(),
                data.index[-1].to_pydatetime()
            )
            
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
        Fetch data for multiple symbols (optimized batch fetch).
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date
            end_date: End date
            timeframe: Data interval
        
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        try:
            logger.info(f"Batch fetching {len(symbols)} symbols from Yahoo Finance")
            
            # Use yfinance download for batch fetching
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                interval=timeframe,
                auto_adjust=self.auto_adjust,
                group_by='ticker',
                progress=False
            )
            
            if data.empty:
                logger.warning("No data returned from batch fetch")
                return {}
            
            result = {}
            
            # Handle single vs multiple symbols
            if len(symbols) == 1:
                symbol = symbols[0]
                df = data.copy()
                df.columns = [col.lower() for col in df.columns]
                result[symbol] = df
            else:
                for symbol in symbols:
                    try:
                        if symbol in data.columns.levels[0]:
                            df = data[symbol].copy()
                            df.columns = [col.lower() for col in df.columns]
                            result[symbol] = df
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
            
            logger.info(f"Successfully fetched {len(result)} symbols")
            return result
            
        except Exception as e:
            logger.error(f"Error in batch fetch: {e}")
            # Fallback to individual fetches
            return super().fetch_multiple(symbols, start_date, end_date, timeframe)
    
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
            "Yahoo Finance data source providing historical price data for equities, "
            "ETFs, indices, commodities, currencies, and cryptocurrencies. "
            "Free to use with no authentication required."
        )
