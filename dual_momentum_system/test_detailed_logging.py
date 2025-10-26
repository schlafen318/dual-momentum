#!/usr/bin/env python3
"""
Test script for detailed download logging.

This script tests the enhanced logging functionality added to diagnose
data download failures. It attempts to fetch data using multiple sources
and logs detailed information about each step.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Configure loguru for detailed console output
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# Also log to file
log_file = project_root / "download_test.log"
logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB"
)

logger.info("=" * 80)
logger.info("DETAILED LOGGING TEST - Data Download Diagnostics")
logger.info("=" * 80)

# Import data sources
from src.data_sources import get_default_data_source

def check_single_symbol(data_source, symbol, start_date, end_date):
    """Test fetching a single symbol with detailed logging."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: Fetching single symbol: {symbol}")
    logger.info(f"{'='*80}")
    
    try:
        df = data_source.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe='1d'
        )
        
        if df is not None and not df.empty:
            logger.success(f"✓ Successfully fetched {symbol}: {len(df)} rows")
            logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")
            logger.info(f"  Columns: {list(df.columns)}")
            logger.info(f"  First row:\n{df.head(1)}")
            return True
        else:
            logger.warning(f"✗ Empty data for {symbol}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to fetch {symbol}: {type(e).__name__}: {e}")
        return False


def check_multiple_symbols(data_source, symbols, start_date, end_date):
    """Test fetching multiple symbols with detailed logging."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: Fetching multiple symbols: {', '.join(symbols)}")
    logger.info(f"{'='*80}")
    
    try:
        result = data_source.fetch_multiple(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe='1d'
        )
        
        logger.info(f"\nRESULTS SUMMARY:")
        logger.info(f"  Total symbols: {len(symbols)}")
        logger.info(f"  Successful: {len(result)}")
        logger.info(f"  Failed: {len(symbols) - len(result)}")
        
        for symbol in symbols:
            if symbol in result:
                logger.success(f"  ✓ {symbol}: {len(result[symbol])} rows")
            else:
                logger.warning(f"  ✗ {symbol}: Failed")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Batch fetch failed: {type(e).__name__}: {e}")
        return {}


def check_invalid_symbol(data_source, symbol, start_date, end_date):
    """Test fetching an invalid symbol to see error handling."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: Fetching invalid symbol: {symbol} (expect failure)")
    logger.info(f"{'='*80}")
    
    try:
        df = data_source.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe='1d'
        )
        
        if df is not None and not df.empty:
            logger.warning(f"Unexpected: Got data for invalid symbol {symbol}")
            return True
        else:
            logger.info(f"Expected result: Empty data for invalid symbol {symbol}")
            return False
            
    except Exception as e:
        logger.info(f"Expected error for invalid symbol: {type(e).__name__}: {str(e)[:100]}")
        return False


def check_cache_functionality(data_source, symbol, start_date, end_date):
    """Test caching with detailed logging."""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: Cache functionality for {symbol}")
    logger.info(f"{'='*80}")
    
    # First fetch - should hit API
    logger.info("First fetch (should hit API):")
    df1 = data_source.fetch_data(symbol, start_date, end_date, '1d')
    
    # Second fetch - should hit cache
    logger.info("\nSecond fetch (should hit cache):")
    df2 = data_source.fetch_data(symbol, start_date, end_date, '1d')
    
    if df1 is not None and df2 is not None:
        logger.success(f"✓ Cache test passed for {symbol}")
        return True
    else:
        logger.warning(f"✗ Cache test inconclusive for {symbol}")
        return False


def main():
    """Main test runner."""
    logger.info("Initializing data source...")
    
    # Get default data source (multi-source with failover)
    data_source = get_default_data_source()
    
    logger.info(f"Data source initialized: {type(data_source).__name__}")
    
    # Define test parameters
    # Use dates in the past to ensure data is available
    end_date = datetime(2024, 10, 20)
    start_date = datetime(2024, 9, 20)  # 30 days of data
    
    logger.info(f"Test date range: {start_date.date()} to {end_date.date()}")
    
    # Test 1: Single well-known symbol
    logger.info("\n" + "="*80)
    logger.info("TEST SUITE 1: Single Symbol Tests")
    logger.info("="*80)
    
    test_symbols = ['SPY', 'AAPL', 'MSFT']
    for symbol in test_symbols:
        check_single_symbol(data_source, symbol, start_date, end_date)
    
    # Test 2: Multiple symbols batch fetch
    logger.info("\n" + "="*80)
    logger.info("TEST SUITE 2: Multiple Symbol Batch Fetch")
    logger.info("="*80)
    
    batch_symbols = ['SPY', 'QQQ', 'IWM', 'DIA']
    check_multiple_symbols(data_source, batch_symbols, start_date, end_date)
    
    # Test 3: Invalid symbol
    logger.info("\n" + "="*80)
    logger.info("TEST SUITE 3: Invalid Symbol (Error Handling)")
    logger.info("="*80)
    
    check_invalid_symbol(data_source, 'INVALID_SYMBOL_12345', start_date, end_date)
    
    # Test 4: Cache functionality
    logger.info("\n" + "="*80)
    logger.info("TEST SUITE 4: Cache Functionality")
    logger.info("="*80)
    
    check_cache_functionality(data_source, 'SPY', start_date, end_date)
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    logger.info(f"Detailed logs written to: {log_file}")
    logger.info("Review the logs above to diagnose any download failures")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error in test script:")
        sys.exit(1)
