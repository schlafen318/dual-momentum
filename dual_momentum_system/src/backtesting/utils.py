"""
Utility functions for backtesting.

Provides helper functions to make backtesting easier and avoid common pitfalls.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..core.base_strategy import BaseStrategy
from ..core.base_data_source import BaseDataSource


def get_universe_data_availability(
    symbols: List[str],
    data_source: BaseDataSource,
    max_retries: int = 2
) -> Tuple[Optional[datetime], Optional[datetime], Dict[str, Tuple[Optional[datetime], Optional[datetime]]]]:
    """
    Query the earliest and latest available dates across all symbols in a universe.
    
    This function checks data availability for each symbol and returns:
    1. The latest inception date (most conservative for backtesting all symbols)
    2. The earliest inception date (most optimistic)
    3. Per-symbol date ranges
    
    Args:
        symbols: List of symbols to check
        data_source: Data source instance to query
        max_retries: Maximum retries per symbol (default: 2)
    
    Returns:
        Tuple of (
            earliest_common_date: datetime or None,
            latest_common_date: datetime or None, 
            per_symbol_ranges: Dict[symbol, (start, end)]
        )
        
        earliest_common_date is the LATEST inception date across all symbols
        (i.e., the date from which ALL symbols have data)
    
    Example:
        >>> earliest, latest, ranges = get_universe_data_availability(
        ...     ['SPY', 'EFA', 'EEM'],
        ...     data_source
        ... )
        >>> print(f"All symbols available from: {earliest}")
        All symbols available from: 2003-04-11  # EEM inception date
        >>> 
        >>> print(f"Per-symbol ranges:")
        >>> for symbol, (start, end) in ranges.items():
        ...     print(f"  {symbol}: {start.date()} to {end.date()}")
        SPY: 1993-01-29 to 2025-10-24
        EFA: 2001-08-17 to 2025-10-24
        EEM: 2003-04-11 to 2025-10-24
    """
    logger.info(f"🔍 Checking data availability for {len(symbols)} symbols...")
    
    per_symbol_ranges = {}
    earliest_starts = []
    latest_starts = []
    earliest_ends = []
    
    for symbol in symbols:
        retries = 0
        date_range = None
        
        while retries <= max_retries and date_range is None:
            try:
                # Try to get date range from data source
                date_range = data_source.get_data_range(symbol)
                
                if date_range:
                    start_date, end_date = date_range
                    per_symbol_ranges[symbol] = (start_date, end_date)
                    earliest_starts.append(start_date)
                    latest_starts.append(start_date)
                    earliest_ends.append(end_date)
                    
                    logger.info(
                        f"  ✓ {symbol}: {start_date.date()} to {end_date.date()} "
                        f"({(end_date - start_date).days} days)"
                    )
                else:
                    logger.warning(f"  ⚠️  {symbol}: No date range available")
                    
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"  ✗ {symbol}: Failed to get date range after {max_retries} retries: {e}")
                else:
                    logger.debug(f"  Retry {retries}/{max_retries} for {symbol}")
    
    # Calculate common date range
    if earliest_starts and latest_starts and earliest_ends:
        # The earliest common date is the LATEST of all start dates
        # (i.e., the date from which ALL symbols have data)
        earliest_common_date = max(latest_starts)
        
        # The latest common date is the EARLIEST of all end dates
        latest_common_date = min(earliest_ends)
        
        logger.info(
            f"\n📊 Data Availability Summary:"
            f"\n  ✓ {len(per_symbol_ranges)}/{len(symbols)} symbols checked"
            f"\n  📅 Common date range: {earliest_common_date.date()} to {latest_common_date.date()}"
            f"\n  📏 Common period: {(latest_common_date - earliest_common_date).days} days "
            f"({(latest_common_date - earliest_common_date).days / 365.25:.1f} years)"
        )
        
        # Show which symbol limits the backtest start date
        limiting_symbol = None
        for symbol, (start_date, _) in per_symbol_ranges.items():
            if start_date == earliest_common_date:
                limiting_symbol = symbol
                break
        
        if limiting_symbol:
            logger.info(f"  ℹ️  Earliest common date limited by: {limiting_symbol}")
        
        return earliest_common_date, latest_common_date, per_symbol_ranges
    else:
        logger.warning("⚠️  Could not determine data availability for any symbols")
        return None, None, per_symbol_ranges


def calculate_data_fetch_dates(
    backtest_start_date: datetime,
    backtest_end_date: datetime,
    lookback_period: int,
    safety_factor: float = 1.5
) -> Tuple[datetime, datetime]:
    """
    Calculate the date range for fetching data to ensure sufficient warm-up period.
    
    For momentum strategies, you need historical data BEFORE your backtest start
    to calculate initial momentum scores. This function helps you determine
    how far back to fetch data.
    
    Args:
        backtest_start_date: When you want the backtest to start
        backtest_end_date: When you want the backtest to end
        lookback_period: Strategy lookback period in trading days
        safety_factor: Multiplier for extra safety (default: 1.5)
            - 1.0 = exactly lookback_period
            - 1.5 = 50% extra (recommended)
            - 2.0 = double the lookback (very safe)
    
    Returns:
        Tuple of (data_fetch_start_date, data_fetch_end_date)
    
    Example:
        >>> # Want to backtest 2022-2024 with 252-day lookback
        >>> data_start, data_end = calculate_data_fetch_dates(
        ...     datetime(2022, 1, 1),
        ...     datetime(2024, 12, 31),
        ...     lookback_period=252
        ... )
        >>> print(f"Fetch data from {data_start.date()} to {data_end.date()}")
        Fetch data from 2020-08-28 to 2024-12-31
        
        >>> # Then fetch and backtest:
        >>> data = fetch_data(symbols, data_start, data_end)
        >>> results = engine.run(
        ...     strategy=strategy,
        ...     price_data=data,
        ...     start_date=datetime(2022, 1, 1),  # Your desired backtest start
        ...     end_date=datetime(2024, 12, 31)
        ... )
    """
    # Calculate warm-up period in calendar days
    # Assuming ~252 trading days per year, or ~70% of calendar days
    warm_up_trading_days = int(lookback_period * safety_factor)
    warm_up_calendar_days = int(warm_up_trading_days / 0.7)
    
    # Calculate data fetch start date
    data_fetch_start = backtest_start_date - timedelta(days=warm_up_calendar_days)
    data_fetch_end = backtest_end_date
    
    logger.info(
        f"📅 Data fetch calculation:"
        f"\n  Backtest period: {backtest_start_date.date()} to {backtest_end_date.date()}"
        f"\n  Lookback period: {lookback_period} trading days"
        f"\n  Warm-up needed: {warm_up_trading_days} trading days (~{warm_up_calendar_days} calendar days)"
        f"\n  ➜ Fetch data from: {data_fetch_start.date()} to {data_fetch_end.date()}"
    )
    
    return data_fetch_start, data_fetch_end


def estimate_required_data_bars(lookback_period: int, safety_factor: float = 1.5) -> int:
    """
    Estimate how many data bars are needed before the first rebalance.
    
    Args:
        lookback_period: Strategy lookback period in trading days
        safety_factor: Multiplier for extra safety (default: 1.5)
    
    Returns:
        Estimated number of bars needed
    
    Example:
        >>> bars_needed = estimate_required_data_bars(252)
        >>> print(f"Need {bars_needed} bars before first rebalance")
        Need 378 bars before first rebalance
    """
    return int(lookback_period * safety_factor)


def validate_data_sufficiency(
    price_data: Dict,
    lookback_period: int,
    min_bars_required: int = None
) -> Tuple[bool, str]:
    """
    Validate that price data has sufficient bars for the strategy.
    
    Args:
        price_data: Dictionary of PriceData objects
        lookback_period: Strategy lookback period
        min_bars_required: Minimum bars needed (defaults to lookback_period)
    
    Returns:
        Tuple of (is_sufficient: bool, message: str)
    
    Example:
        >>> is_valid, message = validate_data_sufficiency(price_data, 252)
        >>> if not is_valid:
        ...     print(f"Data validation failed: {message}")
    """
    if min_bars_required is None:
        min_bars_required = lookback_period
    
    min_bars_available = min(len(pdata.data) for pdata in price_data.values())
    
    if min_bars_available < min_bars_required:
        shortage = min_bars_required - min_bars_available
        message = (
            f"Insufficient data: have {min_bars_available} bars, "
            f"need {min_bars_required} bars (short by {shortage}). "
            f"\n\nSolution: Fetch data starting from an earlier date. "
            f"Use calculate_data_fetch_dates() to determine the correct start date."
        )
        return False, message
    
    return True, f"Data validation passed: {min_bars_available} bars available"


def print_backtest_summary(
    strategy_name: str,
    backtest_start: datetime,
    backtest_end: datetime,
    lookback_period: int,
    data_bars_available: int,
    first_rebalance_expected: datetime = None
):
    """
    Print a helpful summary of backtest configuration and data availability.
    
    Args:
        strategy_name: Name of the strategy
        backtest_start: Backtest start date
        backtest_end: Backtest end date
        lookback_period: Strategy lookback period
        data_bars_available: Number of data bars available
        first_rebalance_expected: Expected date of first rebalance
    """
    print("=" * 80)
    print("BACKTEST CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"\nStrategy: {strategy_name}")
    print(f"Lookback Period: {lookback_period} trading days")
    print(f"\nBacktest Period:")
    print(f"  Start: {backtest_start.date()}")
    print(f"  End: {backtest_end.date()}")
    print(f"\nData Availability:")
    print(f"  Bars Available: {data_bars_available}")
    print(f"  Bars Required: {lookback_period}")
    print(f"  Status: {'✓ SUFFICIENT' if data_bars_available >= lookback_period else '✗ INSUFFICIENT'}")
    
    if first_rebalance_expected:
        print(f"\nFirst Rebalance:")
        print(f"  Expected on or after: {first_rebalance_expected.date()}")
    
    print("=" * 80 + "\n")


def ensure_safe_asset_data(
    strategy: BaseStrategy,
    price_data: Dict[str, Any],
    data_source: BaseDataSource,
    start_date: datetime,
    end_date: datetime,
    asset_class: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Automatically fetch safe asset data if it's configured but missing.
    
    This function solves the common issue where a strategy has a safe_asset
    configured (e.g., 'SHY', 'AGG') but that asset is not included in the
    universe or price data. During bearish markets, the strategy will try to
    rotate to the safe asset but the signal will be silently skipped, leaving
    the portfolio in cash instead of bonds.
    
    This function:
    1. Checks if the strategy has a safe_asset configured
    2. Checks if that safe_asset is already in the price_data
    3. If missing, automatically fetches it and adds to price_data
    
    Args:
        strategy: Strategy instance with potential safe_asset config
        price_data: Dictionary of existing price data (symbol -> PriceData)
        data_source: Data source instance to fetch missing data
        start_date: Start date for data fetching
        end_date: End date for data fetching
        asset_class: Optional asset class instance for normalization
    
    Returns:
        Updated price_data dictionary with safe asset included if needed
    
    Example:
        >>> from src.data_sources.yahoo_finance import YahooFinanceSource
        >>> from src.strategies.dual_momentum import DualMomentumStrategy
        >>> from src.asset_classes.equity import EquityAsset
        >>> 
        >>> strategy = DualMomentumStrategy({
        ...     'safe_asset': 'SHY',  # Safe asset not in universe
        ...     'position_count': 1
        ... })
        >>> 
        >>> # Fetch universe data
        >>> price_data = {}
        >>> for symbol in ['SPY', 'AGG', 'GLD']:
        ...     raw = data_source.fetch_data(symbol, start, end)
        ...     price_data[symbol] = asset.normalize_data(raw, symbol)
        >>> 
        >>> # Automatically fetch safe asset if missing
        >>> price_data = ensure_safe_asset_data(
        ...     strategy, price_data, data_source, start, end, asset
        ... )
        >>> # Now price_data includes 'SHY'
        >>> 
        >>> # Run backtest - safe asset signals will now work
        >>> results = engine.run(strategy, price_data)
    
    Note:
        - This is called automatically if you use `prepare_backtest_data()`
        - You can call it manually before running backtests
        - Works with any data source (Yahoo Finance, Alpha Vantage, etc.)
        - Handles both strategy.config['safe_asset'] and strategy.safe_asset
    """
    # Try to get safe asset from strategy
    safe_asset = None
    
    if hasattr(strategy, 'config') and isinstance(strategy.config, dict):
        safe_asset = strategy.config.get('safe_asset')
    elif hasattr(strategy, 'safe_asset'):
        safe_asset = strategy.safe_asset
    
    # If no safe asset configured, nothing to do
    if not safe_asset:
        logger.debug("No safe asset configured in strategy")
        return price_data
    
    # Check if safe asset already in price_data
    if safe_asset in price_data:
        logger.debug(f"Safe asset '{safe_asset}' already in price data")
        return price_data
    
    # Safe asset is missing - fetch it
    logger.info(
        f"🛡️  Safe asset '{safe_asset}' configured but not in price data. "
        f"Fetching automatically..."
    )
    
    try:
        # Fetch safe asset data
        raw_data = data_source.fetch_data(safe_asset, start_date, end_date)
        
        if raw_data.empty:
            logger.warning(
                f"⚠️ Failed to fetch data for safe asset '{safe_asset}'. "
                f"Safe asset signals will be skipped during backtest."
            )
            return price_data
        
        # Normalize data if asset class provided
        if asset_class:
            try:
                normalized_data = asset_class.normalize_data(raw_data, safe_asset)
                price_data[safe_asset] = normalized_data
                logger.info(
                    f"✓ Successfully fetched {len(normalized_data.data)} bars for safe asset '{safe_asset}'"
                )
            except Exception as e:
                logger.error(f"Failed to normalize safe asset data: {e}")
                # Still add raw data as fallback
                from ..core.types import PriceData
                price_data[safe_asset] = PriceData(symbol=safe_asset, data=raw_data)
                logger.info(f"✓ Added raw data for safe asset '{safe_asset}' (normalization failed)")
        else:
            # No asset class provided, wrap in PriceData
            from ..core.types import PriceData
            price_data[safe_asset] = PriceData(symbol=safe_asset, data=raw_data)
            logger.info(f"✓ Successfully fetched {len(raw_data)} bars for safe asset '{safe_asset}'")
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch safe asset '{safe_asset}': {e}\n"
            f"   Safe asset signals will be skipped. Consider:\n"
            f"   1. Adding '{safe_asset}' to your universe manually, OR\n"
            f"   2. Changing safe_asset to one already in your universe"
        )
    
    return price_data


def prepare_backtest_data(
    strategy: BaseStrategy,
    symbols: list,
    data_source: BaseDataSource,
    start_date: datetime,
    end_date: datetime,
    asset_class: Optional[Any] = None,
    include_safe_asset: bool = True
) -> Dict[str, Any]:
    """
    Prepare all data needed for backtesting, including automatic safe asset fetching.
    
    This is a convenience function that:
    1. Fetches data for all symbols in the universe
    2. Automatically fetches safe asset if configured and missing
    3. Normalizes all data using the provided asset class
    4. Returns a ready-to-use price_data dictionary
    
    Args:
        strategy: Strategy instance
        symbols: List of symbols in the universe
        data_source: Data source to fetch from
        start_date: Start date for data
        end_date: End date for data
        asset_class: Asset class for data normalization
        include_safe_asset: Whether to auto-fetch safe asset (default: True)
    
    Returns:
        Dictionary of symbol -> PriceData ready for backtesting
    
    Example:
        >>> from src.backtesting.utils import prepare_backtest_data
        >>> 
        >>> # One-line data preparation
        >>> price_data = prepare_backtest_data(
        ...     strategy=strategy,
        ...     symbols=['SPY', 'AGG', 'GLD'],
        ...     data_source=data_source,
        ...     start_date=start,
        ...     end_date=end,
        ...     asset_class=equity_asset
        ... )
        >>> # Automatically includes safe asset if configured
        >>> 
        >>> # Run backtest
        >>> results = engine.run(strategy, price_data)
    """
    logger.info(f"Preparing backtest data for {len(symbols)} symbols")
    
    price_data = {}
    
    # Fetch data for all symbols
    for symbol in symbols:
        try:
            logger.debug(f"Fetching {symbol}...")
            raw_data = data_source.fetch_data(symbol, start_date, end_date)
            
            if raw_data.empty:
                logger.warning(f"No data returned for {symbol}")
                continue
            
            # Normalize if asset class provided
            if asset_class:
                normalized_data = asset_class.normalize_data(raw_data, symbol)
                price_data[symbol] = normalized_data
            else:
                from ..core.types import PriceData
                price_data[symbol] = PriceData(symbol=symbol, data=raw_data)
            
            logger.debug(f"✓ Loaded {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            continue
    
    logger.info(f"✓ Successfully loaded {len(price_data)} symbols")
    
    # Automatically include safe asset if configured
    if include_safe_asset:
        price_data = ensure_safe_asset_data(
            strategy, price_data, data_source, start_date, end_date, asset_class
        )
    
    return price_data
