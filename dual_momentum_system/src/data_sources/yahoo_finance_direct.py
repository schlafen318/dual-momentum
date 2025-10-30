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

# Try to import yfinance as fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("[INIT] yfinance not available - only direct API will be used")


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
                   - use_yfinance_fallback: Use yfinance library as fallback (default: True)
        """
        super().__init__(config)
        
        self.timeout = self.config.get('timeout', 10)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
        self.request_delay = self.config.get('request_delay', 0.5)
        self.use_yfinance_fallback = self.config.get('use_yfinance_fallback', True)
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
        fetch_start_time = time.time()
        # Normalize date/datetime inputs
        if hasattr(start_date, 'date') and not isinstance(start_date, datetime):
            try:
                start_date = datetime.combine(start_date, datetime.min.time())  # type: ignore[arg-type]
            except Exception:
                pass
        if hasattr(end_date, 'date') and not isinstance(end_date, datetime):
            try:
                end_date = datetime.combine(end_date, datetime.max.time())  # type: ignore[arg-type]
            except Exception:
                pass
        # Robust logging for mixed date types
        try:
            start_for_log = start_date.date() if isinstance(start_date, datetime) else start_date
            end_for_log = end_date.date() if isinstance(end_date, datetime) else end_date
            logger.info(f"[FETCH START] Symbol: {symbol}, Date Range: {start_for_log} to {end_for_log}, Timeframe: {timeframe}")
        except Exception:
            logger.info(f"[FETCH START] Symbol: {symbol}, Timeframe: {timeframe}")
        
        # Check cache first
        cached_data = self.get_from_cache(symbol, start_date, end_date, timeframe)
        if cached_data is not None:
            logger.info(f"[CACHE HIT] {symbol}: Found {len(cached_data)} cached rows (elapsed: {time.time() - fetch_start_time:.2f}s)")
            return cached_data
        else:
            logger.debug(f"[CACHE MISS] {symbol}: No cached data found, fetching from API")
        
        # Validate timeframe
        if not self.validate_timeframe(timeframe):
            logger.error(f"[VALIDATION ERROR] Unsupported timeframe '{timeframe}' for {symbol}. Supported: {self.get_supported_timeframes()}")
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        try:
            logger.info(f"[API REQUEST] Initiating Yahoo Finance request for {symbol}")
            
            # Build request parameters
            params = {
                'period1': self._timestamp_to_unix(start_date),
                'period2': self._timestamp_to_unix(end_date),
                'interval': self._interval_to_yahoo(timeframe),
                'events': 'history',
                'includeAdjustedClose': 'true'
            }
            
            url = f"{self.BASE_URL}{symbol}"
            logger.debug(f"[REQUEST DETAILS] URL: {url}")
            logger.debug(f"[REQUEST DETAILS] Params: {params}")
            logger.debug(f"[REQUEST DETAILS] Timeout: {self.timeout}s, Max Retries: {self.max_retries}")
            
            # Make request with retries
            request_start = time.time()
            data = self._make_request_with_retry(url, params)
            request_duration = time.time() - request_start
            
            if not data:
                logger.error(f"[API ERROR] No data returned for {symbol} after {request_duration:.2f}s")
                return pd.DataFrame()
            
            logger.info(f"[API SUCCESS] Received response for {symbol} in {request_duration:.2f}s")
            logger.debug(f"[RESPONSE STRUCTURE] Keys: {list(data.keys())}")
            
            # Parse response
            parse_start = time.time()
            df = self._parse_chart_response(data)
            parse_duration = time.time() - parse_start
            
            if df.empty:
                logger.warning(f"[PARSE WARNING] Empty dataframe after parsing {symbol} (parse time: {parse_duration:.2f}s)")
                logger.debug(f"[PARSE WARNING] Response data: {str(data)[:500]}...")
                
                # Try yfinance fallback if available
                if self.use_yfinance_fallback and YFINANCE_AVAILABLE:
                    logger.info(f"[FALLBACK] Trying yfinance library for {symbol}")
                    try:
                        df = self._fetch_with_yfinance(symbol, start_date, end_date, timeframe)
                        if not df.empty and isinstance(df, pd.DataFrame):
                            logger.info(f"[FALLBACK SUCCESS] Retrieved {len(df)} rows using yfinance")
                            # Cache the successful result
                            try:
                                self.add_to_cache(symbol, df.copy(), start_date, end_date, timeframe)
                            except Exception as cache_error:
                                logger.warning(f"[CACHE] Failed to cache yfinance data: {cache_error}")
                            return df
                    except Exception as e:
                        logger.error(f"[FALLBACK FAILED] yfinance also failed: {e}")
                
                return pd.DataFrame()
            
            # Validate data quality
            logger.debug(f"[DATA VALIDATION] {symbol}: Shape={df.shape}, Columns={list(df.columns)}")
            logger.debug(f"[DATA VALIDATION] {symbol}: Date range={df.index[0]} to {df.index[-1]}")
            
            null_counts = df.isnull().sum()
            if null_counts.any():
                logger.warning(f"[DATA QUALITY] {symbol}: Null values detected: {null_counts[null_counts > 0].to_dict()}")
            
            # Add to cache
            self.add_to_cache(symbol, start_date, end_date, timeframe, df)
            
            total_duration = time.time() - fetch_start_time
            logger.info(f"[FETCH SUCCESS] {symbol}: {len(df)} rows fetched successfully (total: {total_duration:.2f}s, parse: {parse_duration:.2f}s)")
            return df
            
        except Exception as e:
            total_duration = time.time() - fetch_start_time
            logger.error(f"[FETCH FAILED] {symbol}: {type(e).__name__}: {e} (elapsed: {total_duration:.2f}s)")
            logger.exception(f"[FETCH FAILED] Full traceback for {symbol}:")
            raise ConnectionError(f"Failed to fetch data from Yahoo Finance: {e}")
    
    def _make_request_with_retry(self, url: str, params: Dict) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"[HTTP REQUEST] Attempt {attempt + 1}/{self.max_retries}: GET {url}")
                request_time = time.time()
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                response_time = time.time() - request_time
                logger.debug(f"[HTTP RESPONSE] Status: {response.status_code}, Time: {response_time:.2f}s, Size: {len(response.content)} bytes")
                logger.debug(f"[HTTP RESPONSE] Headers: {dict(response.headers)}")
                
                response.raise_for_status()
                
                json_data = response.json()
                logger.debug(f"[HTTP RESPONSE] Successfully parsed JSON response")
                return json_data
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"[HTTP TIMEOUT] Attempt {attempt + 1}/{self.max_retries}: Request timed out after {self.timeout}s: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[HTTP FAILED] All {self.max_retries} attempts timed out")
                    raise
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                response_body = e.response.text[:500] if e.response else None
                
                logger.warning(f"[HTTP ERROR] Attempt {attempt + 1}/{self.max_retries}: HTTP {status_code}: {e}")
                logger.debug(f"[HTTP ERROR] Response body: {response_body}")
                
                if attempt < self.max_retries - 1:
                    # Increase delay for rate limit errors
                    delay = self.retry_delay
                    if status_code == 429 or 'Too Many Requests' in str(e):
                        delay = self.retry_delay * 2
                        logger.info(f"[RATE LIMIT] Detected 429 error, waiting {delay}s before retry")
                    elif status_code and 500 <= status_code < 600:
                        logger.info(f"[SERVER ERROR] Server error {status_code}, waiting {delay}s before retry")
                    time.sleep(delay)
                else:
                    logger.error(f"[HTTP FAILED] All {self.max_retries} attempts failed with HTTP errors")
                    raise
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"[CONNECTION ERROR] Attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[CONNECTION FAILED] Could not establish connection after {self.max_retries} attempts")
                    raise
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"[REQUEST ERROR] Attempt {attempt + 1}/{self.max_retries}: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[REQUEST FAILED] All {self.max_retries} attempts failed")
                    raise
        
        return None
    
    def _parse_chart_response(self, data: Dict) -> pd.DataFrame:
        """Parse Yahoo Finance chart API response."""
        try:
            logger.debug(f"[PARSE START] Parsing chart response")
            
            # Check for error in response
            if 'chart' in data and 'error' in data['chart']:
                error_info = data['chart']['error']
                logger.error(f"[PARSE ERROR] API returned error: {error_info}")
                return pd.DataFrame()
            
            result = data.get('chart', {}).get('result', [])
            if not result:
                logger.warning(f"[PARSE WARNING] No result in chart response. Available keys: {list(data.keys())}")
                if 'chart' in data:
                    logger.debug(f"[PARSE WARNING] Chart keys: {list(data['chart'].keys())}")
                return pd.DataFrame()
            
            result = result[0]
            logger.debug(f"[PARSE INFO] Result keys: {list(result.keys())}")
            
            # Extract metadata
            meta = result.get('meta', {})
            logger.debug(f"[PARSE INFO] Symbol: {meta.get('symbol')}, Currency: {meta.get('currency')}, Exchange: {meta.get('exchangeName')}")
            logger.debug(f"[PARSE INFO] Regular market price: {meta.get('regularMarketPrice')}, Previous close: {meta.get('previousClose')}")
            
            # Extract timestamps
            timestamps = result.get('timestamp', [])
            if not timestamps:
                logger.warning(f"[PARSE WARNING] No timestamps in result. Available keys: {list(result.keys())}")
                return pd.DataFrame()
            
            logger.debug(f"[PARSE INFO] Found {len(timestamps)} timestamps")
            
            # Extract quotes
            quotes = result.get('indicators', {}).get('quote', [])
            if not quotes:
                logger.warning(f"[PARSE WARNING] No quotes in indicators. Indicators keys: {list(result.get('indicators', {}).keys())}")
                return pd.DataFrame()
            
            quote = quotes[0]
            logger.debug(f"[PARSE INFO] Quote keys: {list(quote.keys())}")
            
            # Build dataframe
            df = pd.DataFrame({
                'open': quote.get('open', []),
                'high': quote.get('high', []),
                'low': quote.get('low', []),
                'close': quote.get('close', []),
                'volume': quote.get('volume', [])
            })
            
            logger.debug(f"[PARSE INFO] Created dataframe with shape: {df.shape}")
            
            # Add timestamps as index
            df.index = pd.to_datetime(timestamps, unit='s')
            df.index.name = 'Date'
            
            # Handle adjusted close if available
            adjclose = result.get('indicators', {}).get('adjclose', [])
            if adjclose and adjclose[0].get('adjclose'):
                df['adjclose'] = adjclose[0]['adjclose']
                logger.debug(f"[PARSE INFO] Added adjusted close column")
            
            # Remove rows with all NaN values
            rows_before = len(df)
            df = df.dropna(how='all')
            rows_after = len(df)
            
            if rows_before != rows_after:
                logger.debug(f"[PARSE INFO] Removed {rows_before - rows_after} rows with all NaN values")
            
            logger.debug(f"[PARSE SUCCESS] Final dataframe: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"[PARSE EXCEPTION] {type(e).__name__}: {e}")
            logger.exception(f"[PARSE EXCEPTION] Full traceback:")
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
        batch_start = time.time()
        logger.info(f"[BATCH START] Fetching {len(symbols)} symbols from Yahoo Finance (Direct)")
        logger.info(f"[BATCH START] Symbols: {', '.join(symbols)}")
        # Robust logging for mixed date types
        try:
            start_for_log = start_date.date() if isinstance(start_date, datetime) else start_date
            end_for_log = end_date.date() if isinstance(end_date, datetime) else end_date
            logger.info(f"[BATCH START] Date range: {start_for_log} to {end_for_log}, Timeframe: {timeframe}")
        except Exception:
            logger.info(f"[BATCH START] Timeframe: {timeframe}")
        
        result = {}
        failed = []
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"[BATCH PROGRESS] Processing {i+1}/{len(symbols)}: {symbol}")
                df = self.fetch_data(symbol, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    result[symbol] = df
                    logger.info(f"[BATCH SUCCESS] {symbol}: {len(df)} rows retrieved")
                else:
                    failed.append((symbol, "Empty data"))
                    logger.warning(f"[BATCH FAILED] {symbol}: Received empty data")
                
                # Add delay between requests to avoid rate limiting
                # (except after the last symbol)
                if i < len(symbols) - 1:
                    logger.debug(f"[BATCH DELAY] Waiting {self.request_delay}s before next request")
                    time.sleep(self.request_delay)
                    
            except Exception as e:
                error_type = type(e).__name__
                failed.append((symbol, f"{error_type}: {str(e)[:100]}"))
                logger.error(f"[BATCH ERROR] {symbol}: {error_type}: {e}")
                # Add delay even on error to avoid hammering the API
                if i < len(symbols) - 1:
                    time.sleep(self.request_delay)
                continue
        
        batch_duration = time.time() - batch_start
        success_rate = (len(result) / len(symbols) * 100) if symbols else 0
        
        logger.info(f"[BATCH COMPLETE] Successfully fetched {len(result)}/{len(symbols)} symbols ({success_rate:.1f}%) in {batch_duration:.2f}s")
        
        if failed:
            logger.warning(f"[BATCH FAILED] Failed to fetch {len(failed)} symbols:")
            for symbol, reason in failed:
                logger.warning(f"[BATCH FAILED]   - {symbol}: {reason}")
        
        return result
    
    def _fetch_with_yfinance(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Fetch data using yfinance library as fallback.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            
        Returns:
            DataFrame with price data
        """
        if not YFINANCE_AVAILABLE:
            logger.error(f"[YFINANCE] Library not available")
            return pd.DataFrame()
        
        try:
            logger.debug(f"[YFINANCE] Downloading {symbol} from {start_date.date()} to {end_date.date()}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Map timeframe
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h',
                '1d': '1d', '1wk': '1wk', '1mo': '1mo'
            }
            yf_interval = interval_map.get(timeframe, '1d')
            
            # Download data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=False
            )
            
            if df.empty:
                logger.warning(f"[YFINANCE] No data returned for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"[YFINANCE] Missing required columns in {symbol} data")
                return pd.DataFrame()
            
            # Keep only OHLCV columns
            df = df[required_cols].copy()
            
            # Remove timezone info if present
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Remove rows with all NaN values
            df = df.dropna(how='all')
            
            logger.info(f"[YFINANCE] Successfully fetched {len(df)} rows for {symbol}")
            logger.debug(f"[YFINANCE] Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            logger.error(f"[YFINANCE] Error fetching {symbol}: {e}")
            import traceback
            logger.debug(f"[YFINANCE] Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
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
