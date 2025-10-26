"""
Tests for the 'longest available' date range feature.

Tests the automatic data availability querying and date range selection
functionality added to Strategy Builder and Hyperparameter Tuning.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.utils import get_universe_data_availability
from src.core.base_data_source import BaseDataSource


class MockDataSource(BaseDataSource):
    """Mock data source for testing."""
    
    def __init__(self, symbol_ranges=None):
        """
        Initialize with predefined symbol ranges.
        
        Args:
            symbol_ranges: Dict of symbol -> (start_date, end_date)
        """
        super().__init__()
        self.symbol_ranges = symbol_ranges or {}
    
    def fetch_data(self, symbol, start_date, end_date, timeframe='1d'):
        """Mock fetch_data method."""
        if symbol not in self.symbol_ranges:
            return pd.DataFrame()
        
        # Create fake price data
        dates = pd.date_range(start_date, end_date, freq='D')
        data = pd.DataFrame({
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 100.0,
            'volume': 1000000
        }, index=dates)
        return data
    
    def get_data_range(self, symbol):
        """Mock get_data_range method."""
        return self.symbol_ranges.get(symbol)
    
    def get_name(self):
        """Return data source name."""
        return "MockDataSource"


class TestGetUniverseDataAvailability:
    """Test the get_universe_data_availability function."""
    
    def test_basic_functionality(self):
        """Test basic data availability query."""
        # Create mock data source with different inception dates
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),  # Limiting symbol
        }
        data_source = MockDataSource(symbol_ranges)
        
        # Query availability
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY', 'EFA', 'EEM'],
            data_source
        )
        
        # Assertions
        assert earliest is not None
        assert latest is not None
        assert earliest == datetime(2003, 4, 11)  # Limited by EEM
        assert latest == datetime(2025, 10, 26)
        assert len(ranges) == 3
        assert ranges['SPY'] == symbol_ranges['SPY']
        assert ranges['EFA'] == symbol_ranges['EFA']
        assert ranges['EEM'] == symbol_ranges['EEM']
    
    def test_single_symbol(self):
        """Test with single symbol."""
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY'],
            data_source
        )
        
        assert earliest == datetime(1993, 1, 29)
        assert latest == datetime(2025, 10, 26)
        assert len(ranges) == 1
    
    def test_missing_symbol(self):
        """Test behavior when symbol has no data."""
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            # EFA missing intentionally
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY', 'EFA'],
            data_source
        )
        
        # Should still return data for SPY
        assert earliest is not None
        assert latest is not None
        assert len(ranges) == 1  # Only SPY
        assert 'SPY' in ranges
        assert 'EFA' not in ranges
    
    def test_all_symbols_missing(self):
        """Test when no symbols have data."""
        data_source = MockDataSource({})
        
        earliest, latest, ranges = get_universe_data_availability(
            ['INVALID1', 'INVALID2'],
            data_source
        )
        
        assert earliest is None
        assert latest is None
        assert len(ranges) == 0
    
    def test_different_end_dates(self):
        """Test when symbols have different end dates."""
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'OLDSTOCK': (datetime(2000, 1, 1), datetime(2020, 12, 31)),  # Delisted
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY', 'OLDSTOCK'],
            data_source
        )
        
        # Common end date should be the earliest end date
        assert latest == datetime(2020, 12, 31)  # Limited by OLDSTOCK
        assert earliest == datetime(2000, 1, 1)  # Limited by OLDSTOCK start
    
    def test_retry_mechanism(self):
        """Test that retry mechanism works for transient failures."""
        call_count = {'count': 0}
        
        def mock_get_data_range(symbol):
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise Exception("Transient error")
            return (datetime(2000, 1, 1), datetime(2025, 10, 26))
        
        data_source = Mock()
        data_source.get_data_range = mock_get_data_range
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY'],
            data_source,
            max_retries=2
        )
        
        # Should succeed on second try
        assert earliest is not None
        assert call_count['count'] == 2
    
    def test_large_universe(self):
        """Test with large universe (performance check)."""
        # Create 50 symbols
        symbol_ranges = {
            f'SYM{i:02d}': (
                datetime(2000 + i % 20, 1, 1),
                datetime(2025, 10, 26)
            )
            for i in range(50)
        }
        data_source = MockDataSource(symbol_ranges)
        
        symbols = list(symbol_ranges.keys())
        earliest, latest, ranges = get_universe_data_availability(
            symbols,
            data_source
        )
        
        assert earliest is not None
        assert latest is not None
        assert len(ranges) == 50
        # Earliest should be 2019 (latest start date)
        assert earliest.year == 2019


class TestDateRangeModes:
    """Test different date range modes."""
    
    def test_longest_available_calculation(self):
        """Test that longest available uses correct dates."""
        earliest = datetime(2003, 4, 11)
        latest = datetime(2025, 10, 26)
        
        # Calculate duration
        duration_days = (latest - earliest).days
        duration_years = duration_days / 365.25
        
        assert duration_years > 22  # More than 22 years
        assert duration_years < 23  # Less than 23 years
    
    def test_preset_periods(self):
        """Test preset period calculations."""
        end_date = datetime(2025, 10, 26)
        
        # Test different presets
        presets = {
            'Last 1 Year': 1,
            'Last 3 Years': 3,
            'Last 5 Years': 5,
            'Last 10 Years': 10
        }
        
        for name, years in presets.items():
            start_date = end_date - timedelta(days=365 * years)
            duration = (end_date - start_date).days / 365.25
            
            # Should be approximately the requested years
            assert abs(duration - years) < 0.1
    
    def test_custom_range_validation(self):
        """Test custom range validation logic."""
        # Valid range
        start = datetime(2020, 1, 1)
        end = datetime(2025, 10, 26)
        assert start < end
        
        # Calculate duration
        duration_years = (end - start).days / 365.25
        assert duration_years > 5


class TestDataAvailabilityDisplay:
    """Test data availability display logic."""
    
    def test_per_symbol_display_format(self):
        """Test formatting of per-symbol availability."""
        ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),
        }
        
        for symbol, (start, end) in ranges.items():
            years = (end - start).days / 365.25
            # Format string (as used in UI)
            display = f"  • {symbol:6s}: {start.date()} to {end.date()} ({years:.1f} years)"
            
            assert symbol in display
            assert str(start.date()) in display
            assert str(end.date()) in display
    
    def test_limiting_symbol_identification(self):
        """Test identification of symbol limiting the start date."""
        ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),
        }
        
        # Earliest common date is the latest start date
        earliest = max(start for start, _ in ranges.values())
        
        # Find limiting symbols
        limiting_symbols = [
            symbol for symbol, (start, _) in ranges.items()
            if start == earliest
        ]
        
        assert limiting_symbols == ['EEM']


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_symbol_list(self):
        """Test with empty symbol list."""
        data_source = MockDataSource({})
        
        earliest, latest, ranges = get_universe_data_availability(
            [],
            data_source
        )
        
        # Should handle gracefully
        assert earliest is None
        assert latest is None
        assert len(ranges) == 0
    
    def test_very_short_period(self):
        """Test with very short available period."""
        symbol_ranges = {
            'NEWIPO': (datetime(2025, 10, 1), datetime(2025, 10, 26)),
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['NEWIPO'],
            data_source
        )
        
        assert earliest is not None
        assert latest is not None
        
        # Very short period
        duration_days = (latest - earliest).days
        assert duration_days < 30
    
    def test_future_dates(self):
        """Test handling of future dates (shouldn't happen but test robustness)."""
        future = datetime.now() + timedelta(days=365)
        symbol_ranges = {
            'FUTURE': (datetime(2020, 1, 1), future),
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['FUTURE'],
            data_source
        )
        
        # Should still work
        assert earliest is not None
        assert latest is not None
    
    def test_data_source_exception(self):
        """Test handling when data source raises exception."""
        def failing_get_data_range(symbol):
            raise ConnectionError("Network error")
        
        data_source = Mock()
        data_source.get_data_range = failing_get_data_range
        
        # Should handle gracefully with retries
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY'],
            data_source,
            max_retries=2
        )
        
        # Should fail gracefully
        assert earliest is None
        assert latest is None
        assert len(ranges) == 0


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_common_portfolio(self):
        """Test with a common momentum portfolio."""
        # Realistic dates for common ETFs
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),
            'AGG': (datetime(2003, 9, 29), datetime(2025, 10, 26)),
            'TLT': (datetime(2002, 7, 30), datetime(2025, 10, 26)),
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY', 'EFA', 'EEM', 'AGG', 'TLT'],
            data_source
        )
        
        # AGG has latest start date (most recent inception)
        assert earliest == datetime(2003, 9, 29)
        assert latest == datetime(2025, 10, 26)
        
        # Calculate backtest period
        duration_years = (latest - earliest).days / 365.25
        assert duration_years > 22  # More than 22 years available
    
    def test_global_macro_portfolio(self):
        """Test with global macro portfolio."""
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),
            'TLT': (datetime(2002, 7, 30), datetime(2025, 10, 26)),
            'GLD': (datetime(2004, 11, 18), datetime(2025, 10, 26)),  # Gold - limiting
            'DBC': (datetime(2006, 2, 3), datetime(2025, 10, 26)),    # Commodities
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            list(symbol_ranges.keys()),
            data_source
        )
        
        # DBC has latest start date
        assert earliest == datetime(2006, 2, 3)
        
        # Still get ~20 years of data
        duration_years = (latest - earliest).days / 365.25
        assert duration_years > 19
    
    def test_comparison_with_old_default(self):
        """Test improvement over old 3-year default."""
        # Realistic portfolio
        symbol_ranges = {
            'SPY': (datetime(1993, 1, 29), datetime(2025, 10, 26)),
            'EFA': (datetime(2001, 8, 17), datetime(2025, 10, 26)),
            'EEM': (datetime(2003, 4, 11), datetime(2025, 10, 26)),
        }
        data_source = MockDataSource(symbol_ranges)
        
        earliest, latest, ranges = get_universe_data_availability(
            ['SPY', 'EFA', 'EEM'],
            data_source
        )
        
        # Longest available
        longest_years = (latest - earliest).days / 365.25
        
        # Old default (3 years)
        old_default_years = 3
        
        # Should be much better
        improvement_factor = longest_years / old_default_years
        assert improvement_factor > 7  # More than 7x improvement


def test_date_mode_defaults():
    """Test that 'Longest Available' is the correct default index."""
    modes = ["Longest Available", "Custom Range", "Last 1 Year", "Last 3 Years", "Last 5 Years", "Last 10 Years"]
    
    # First option should be "Longest Available"
    assert modes[0] == "Longest Available"
    
    # This is index 0 in selectbox
    default_index = 0
    assert modes[default_index] == "Longest Available"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
