"""
Utility functions for backtesting.

Provides helper functions to make backtesting easier and avoid common pitfalls.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple

from loguru import logger


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
