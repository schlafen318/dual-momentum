"""
Tests for the plugin system.

Verifies that plugin discovery, registration, and instantiation work correctly.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    BaseAssetClass,
    BaseDataSource,
    BaseStrategy,
    BaseRiskManager,
    PluginManager,
    AssetType,
    MomentumType,
)


class TestPluginDiscovery:
    """Test plugin discovery functionality."""
    
    def test_plugin_manager_initialization(self):
        """Test that plugin manager initializes correctly."""
        manager = PluginManager()
        assert manager is not None
        assert manager.registry is not None
    
    def test_discover_asset_classes(self):
        """Test discovery of asset class plugins."""
        manager = PluginManager()
        manager.discover_asset_classes()
        
        asset_classes = manager.list_asset_classes()
        assert isinstance(asset_classes, list)
        
        # Should find at least EquityAsset
        if 'EquityAsset' in asset_classes:
            equity_class = manager.get_asset_class('EquityAsset')
            assert equity_class is not None
            assert issubclass(equity_class, BaseAssetClass)
    
    def test_discover_data_sources(self):
        """Test discovery of data source plugins."""
        manager = PluginManager()
        manager.discover_data_sources()
        
        data_sources = manager.list_data_sources()
        assert isinstance(data_sources, list)
        
        # Should find at least YahooFinanceSource
        if 'YahooFinanceSource' in data_sources:
            yahoo_class = manager.get_data_source('YahooFinanceSource')
            assert yahoo_class is not None
            assert issubclass(yahoo_class, BaseDataSource)
    
    def test_discover_strategies(self):
        """Test discovery of strategy plugins."""
        manager = PluginManager()
        manager.discover_strategies()
        
        strategies = manager.list_strategies()
        assert isinstance(strategies, list)
        
        # Should find at least DualMomentumStrategy
        if 'DualMomentumStrategy' in strategies:
            strategy_class = manager.get_strategy('DualMomentumStrategy')
            assert strategy_class is not None
            assert issubclass(strategy_class, BaseStrategy)
    
    def test_discover_risk_managers(self):
        """Test discovery of risk manager plugins."""
        manager = PluginManager()
        manager.discover_risk_managers()
        
        risk_managers = manager.list_risk_managers()
        assert isinstance(risk_managers, list)
        
        # Should find at least BasicRiskManager
        if 'BasicRiskManager' in risk_managers:
            risk_class = manager.get_risk_manager('BasicRiskManager')
            assert risk_class is not None
            assert issubclass(risk_class, BaseRiskManager)
    
    def test_discover_all(self):
        """Test discovery of all plugins at once."""
        manager = PluginManager()
        manager.discover_all()
        
        # Should have discovered plugins in all categories
        all_plugins = manager.registry.get_all_plugins()
        assert 'asset_classes' in all_plugins
        assert 'data_sources' in all_plugins
        assert 'strategies' in all_plugins
        assert 'risk_managers' in all_plugins


class TestPluginInstantiation:
    """Test plugin instantiation."""
    
    def test_equity_asset_instantiation(self):
        """Test instantiating equity asset class."""
        manager = PluginManager()
        manager.discover_asset_classes()
        
        equity_class = manager.get_asset_class('EquityAsset')
        if equity_class:
            equity = equity_class()
            assert equity.get_asset_type() == AssetType.EQUITY
            assert equity.validate_symbol('AAPL')
            assert not equity.validate_symbol('invalid123')
    
    def test_yahoo_finance_instantiation(self):
        """Test instantiating Yahoo Finance data source."""
        manager = PluginManager()
        manager.discover_data_sources()
        
        yahoo_class = manager.get_data_source('YahooFinanceSource')
        if yahoo_class:
            yahoo = yahoo_class(config={'cache_enabled': True})
            assert yahoo is not None
            timeframes = yahoo.get_supported_timeframes()
            assert '1d' in timeframes
            assert '1h' in timeframes
    
    def test_dual_momentum_instantiation(self):
        """Test instantiating dual momentum strategy."""
        manager = PluginManager()
        manager.discover_strategies()
        
        strategy_class = manager.get_strategy('DualMomentumStrategy')
        if strategy_class:
            config = {
                'lookback_period': 252,
                'rebalance_frequency': 'monthly',
                'position_count': 1,
            }
            strategy = strategy_class(config=config)
            assert strategy.get_momentum_type() == MomentumType.DUAL
            assert strategy.get_required_history() == 252
            assert strategy.get_rebalance_frequency() == 'monthly'
    
    def test_basic_risk_instantiation(self):
        """Test instantiating basic risk manager."""
        manager = PluginManager()
        manager.discover_risk_managers()
        
        risk_class = manager.get_risk_manager('BasicRiskManager')
        if risk_class:
            config = {
                'max_position_size': 0.2,
                'max_leverage': 1.0,
            }
            risk_manager = risk_class(config=config)
            assert risk_manager.get_max_leverage() == 1.0
            assert risk_manager.get_max_position_size() == 0.2


class TestPluginInfo:
    """Test plugin information retrieval."""
    
    def test_get_plugin_info(self):
        """Test getting plugin information."""
        manager = PluginManager()
        manager.discover_all()
        
        # Test strategy info
        strategies = manager.list_strategies()
        if strategies:
            strategy_name = strategies[0]
            info = manager.get_plugin_info('strategy', strategy_name)
            assert info is not None
            assert 'name' in info
            assert 'version' in info
            assert 'description' in info


class TestManualRegistration:
    """Test manual plugin registration."""
    
    def test_manual_registration(self):
        """Test manually registering a plugin."""
        manager = PluginManager()
        
        # Create a simple test plugin
        class TestStrategy(BaseStrategy):
            def calculate_momentum(self, price_data):
                pass
            
            def generate_signals(self, price_data):
                return []
            
            def get_momentum_type(self):
                return MomentumType.CUSTOM
        
        # Register it
        manager.register_plugin(TestStrategy, 'strategy', 'TestStrategy')
        
        # Verify it's registered
        assert 'TestStrategy' in manager.list_strategies()
        retrieved = manager.get_strategy('TestStrategy')
        assert retrieved == TestStrategy


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
