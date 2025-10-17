"""
Tests for the configuration system.

Tests universe loader, strategy loader, and configuration API.
"""

import pytest
from pathlib import Path
import yaml

from src.config import (
    get_config_api,
    get_universe_loader,
    get_strategy_loader,
    get_config_manager
)


class TestUniverseLoader:
    """Test universe loading and management."""
    
    def test_load_universes(self):
        """Test loading pre-built universes."""
        loader = get_universe_loader()
        
        # Check that universes were loaded
        assert len(loader.universes) > 0
        print(f"✓ Loaded {len(loader.universes)} universes")
    
    def test_get_gem_classic(self):
        """Test getting GEM classic universe."""
        loader = get_universe_loader()
        
        gem = loader.get_universe('gem_classic')
        assert gem is not None
        assert gem.name == "Global Equity Momentum - Classic"
        assert len(gem.symbols) == 3
        assert 'SPY' in gem.symbols
        print(f"✓ GEM Classic universe: {gem.symbols}")
    
    def test_list_universes_by_asset_class(self):
        """Test filtering universes by asset class."""
        loader = get_universe_loader()
        
        equity_universes = loader.list_universes(asset_class='equity')
        crypto_universes = loader.list_universes(asset_class='crypto')
        
        assert len(equity_universes) > 0
        assert len(crypto_universes) > 0
        print(f"✓ Found {len(equity_universes)} equity universes")
        print(f"✓ Found {len(crypto_universes)} crypto universes")
    
    def test_search_universes(self):
        """Test universe search."""
        loader = get_universe_loader()
        
        results = loader.search_universes('momentum')
        assert len(results) > 0
        print(f"✓ Search 'momentum' found {len(results)} universes")
    
    def test_get_symbols(self):
        """Test getting symbols from universe."""
        loader = get_universe_loader()
        
        symbols = loader.get_symbols('gem_classic')
        assert len(symbols) == 3
        assert 'SPY' in symbols
        print(f"✓ Retrieved symbols: {symbols}")


class TestStrategyLoader:
    """Test strategy loading and management."""
    
    def test_load_strategies(self):
        """Test loading strategies."""
        loader = get_strategy_loader()
        
        # Check that strategies were loaded
        assert len(loader.strategies) > 0
        print(f"✓ Loaded {len(loader.strategies)} strategies")
    
    def test_get_dual_momentum_classic(self):
        """Test getting dual momentum classic strategy."""
        loader = get_strategy_loader()
        
        strategy = loader.get_strategy('dual_momentum_classic')
        assert strategy is not None
        assert strategy.name == "Dual Momentum - Classic"
        assert strategy.parameters['lookback_period'] == 252
        print(f"✓ Dual Momentum Classic: {strategy.description}")
    
    def test_list_strategies_by_category(self):
        """Test filtering strategies by category."""
        loader = get_strategy_loader()
        
        momentum_strategies = loader.list_strategies(category='momentum')
        crypto_strategies = loader.list_strategies(category='crypto')
        
        assert len(momentum_strategies) > 0
        print(f"✓ Found {len(momentum_strategies)} momentum strategies")
        print(f"✓ Found {len(crypto_strategies)} crypto strategies")
    
    def test_list_categories(self):
        """Test listing all categories."""
        loader = get_strategy_loader()
        
        categories = loader.list_categories()
        assert len(categories) > 0
        assert 'momentum' in categories
        print(f"✓ Categories: {categories}")
    
    def test_search_strategies(self):
        """Test strategy search."""
        loader = get_strategy_loader()
        
        results = loader.search_strategies('aggressive')
        assert len(results) > 0
        print(f"✓ Search 'aggressive' found {len(results)} strategies")
    
    def test_parameter_templates(self):
        """Test parameter templates."""
        loader = get_strategy_loader()
        
        conservative = loader.get_parameter_template('conservative')
        assert conservative is not None
        assert 'lookback_period' in conservative
        print(f"✓ Conservative template: {conservative}")
    
    def test_get_compatible_universes(self):
        """Test getting compatible universes for a strategy."""
        loader = get_strategy_loader()
        universe_loader = get_universe_loader()
        
        compatible = loader.get_compatible_universes(
            'dual_momentum_classic',
            universe_loader
        )
        
        assert len(compatible) > 0
        assert 'gem_classic' in compatible
        print(f"✓ Compatible universes: {compatible[:5]}...")


class TestConfigAPI:
    """Test configuration API."""
    
    def test_get_all_universes(self):
        """Test getting all universes via API."""
        api = get_config_api()
        
        universes = api.get_all_universes()
        assert len(universes) > 0
        assert 'gem_classic' in universes
        print(f"✓ API returned {len(universes)} universes")
    
    def test_get_all_strategies(self):
        """Test getting all strategies via API."""
        api = get_config_api()
        
        strategies = api.get_all_strategies()
        assert len(strategies) > 0
        assert 'dual_momentum_classic' in strategies
        print(f"✓ API returned {len(strategies)} strategies")
    
    def test_validate_strategy_universe_pair(self):
        """Test validating strategy-universe compatibility."""
        api = get_config_api()
        
        is_valid, msg = api.validate_strategy_universe_pair(
            'dual_momentum_classic',
            'gem_classic'
        )
        
        assert is_valid
        print(f"✓ Validation passed: {msg}")
    
    def test_create_configured_strategy(self):
        """Test creating a configured strategy."""
        api = get_config_api()
        
        success, strategy, msg = api.create_configured_strategy(
            'dual_momentum_classic',
            'gem_classic'
        )
        
        assert success
        assert strategy is not None
        print(f"✓ Created strategy: {msg}")
    
    def test_get_dashboard_summary(self):
        """Test getting dashboard summary."""
        api = get_config_api()
        
        summary = api.get_dashboard_summary()
        assert 'total_universes' in summary
        assert 'total_strategies' in summary
        assert summary['total_universes'] > 0
        assert summary['total_strategies'] > 0
        print(f"✓ Dashboard summary: {summary}")
    
    def test_get_quick_start_configs(self):
        """Test getting quick-start configurations."""
        api = get_config_api()
        
        configs = api.get_quick_start_configs()
        assert len(configs) > 0
        
        for config in configs:
            assert 'name' in config
            assert 'strategy' in config
            assert 'universe' in config
        
        print(f"✓ Found {len(configs)} quick-start configs")
    
    def test_search_universes(self):
        """Test universe search via API."""
        api = get_config_api()
        
        results = api.search_universes('crypto')
        assert len(results) > 0
        print(f"✓ Search found {len(results)} crypto universes")
    
    def test_search_strategies(self):
        """Test strategy search via API."""
        api = get_config_api()
        
        results = api.search_strategies('momentum')
        assert len(results) > 0
        print(f"✓ Search found {len(results)} momentum strategies")


class TestCustomUniverses:
    """Test custom universe management."""
    
    def test_create_custom_universe(self):
        """Test creating a custom universe."""
        api = get_config_api()
        
        custom_config = {
            'name': 'Test Universe',
            'description': 'A test universe',
            'asset_class': 'equity',
            'symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'benchmark': 'SPY',
            'metadata': {'test': True}
        }
        
        success, msg = api.create_universe('test_universe_temp', custom_config)
        assert success
        print(f"✓ Created custom universe: {msg}")
        
        # Verify it exists
        universe = api.get_universe('test_universe_temp')
        assert universe is not None
        assert universe['name'] == 'Test Universe'
        
        # Clean up
        api.delete_universe('test_universe_temp')
        print("✓ Cleaned up test universe")


class TestConfigManager:
    """Test enhanced config manager."""
    
    def test_list_universes(self):
        """Test listing universes via config manager."""
        manager = get_config_manager()
        
        universes = manager.list_universes()
        assert len(universes) > 0
        print(f"✓ Config manager lists {len(universes)} universes")
    
    def test_list_strategies(self):
        """Test listing strategies via config manager."""
        manager = get_config_manager()
        
        strategies = manager.list_strategies()
        assert len(strategies) > 0
        print(f"✓ Config manager lists {len(strategies)} strategies")
    
    def test_get_universe_symbols(self):
        """Test getting universe symbols via config manager."""
        manager = get_config_manager()
        
        symbols = manager.get_universe_symbols('gem_classic')
        assert len(symbols) == 3
        print(f"✓ Retrieved symbols via config manager: {symbols}")
    
    def test_create_strategy(self):
        """Test creating strategy via config manager."""
        manager = get_config_manager()
        
        strategy = manager.create_strategy('dual_momentum_classic')
        assert strategy is not None
        print("✓ Created strategy via config manager")


def test_yaml_files_exist():
    """Test that YAML configuration files exist."""
    config_dir = Path(__file__).parent.parent / 'config'
    
    assert (config_dir / 'ASSET_UNIVERSES.yaml').exists()
    assert (config_dir / 'STRATEGIES.yaml').exists()
    print("✓ All YAML configuration files exist")


def test_yaml_files_valid():
    """Test that YAML files are valid."""
    config_dir = Path(__file__).parent.parent / 'config'
    
    # Test ASSET_UNIVERSES.yaml
    with open(config_dir / 'ASSET_UNIVERSES.yaml', 'r') as f:
        universes = yaml.safe_load(f)
        assert universes is not None
        assert len(universes) > 0
    print(f"✓ ASSET_UNIVERSES.yaml is valid with {len(universes)} universes")
    
    # Test STRATEGIES.yaml
    with open(config_dir / 'STRATEGIES.yaml', 'r') as f:
        strategies_data = yaml.safe_load(f)
        assert strategies_data is not None
        assert 'strategies' in strategies_data
    print(f"✓ STRATEGIES.yaml is valid with {len(strategies_data['strategies'])} strategies")


if __name__ == '__main__':
    """Run tests manually for verification."""
    print("\n" + "="*70)
    print("RUNNING CONFIGURATION SYSTEM TESTS")
    print("="*70 + "\n")
    
    # Test YAML files
    print("\n--- Testing YAML Files ---")
    test_yaml_files_exist()
    test_yaml_files_valid()
    
    # Test Universe Loader
    print("\n--- Testing Universe Loader ---")
    test_universe = TestUniverseLoader()
    test_universe.test_load_universes()
    test_universe.test_get_gem_classic()
    test_universe.test_list_universes_by_asset_class()
    test_universe.test_search_universes()
    test_universe.test_get_symbols()
    
    # Test Strategy Loader
    print("\n--- Testing Strategy Loader ---")
    test_strategy = TestStrategyLoader()
    test_strategy.test_load_strategies()
    test_strategy.test_get_dual_momentum_classic()
    test_strategy.test_list_strategies_by_category()
    test_strategy.test_list_categories()
    test_strategy.test_search_strategies()
    test_strategy.test_parameter_templates()
    test_strategy.test_get_compatible_universes()
    
    # Test Config API
    print("\n--- Testing Config API ---")
    test_api = TestConfigAPI()
    test_api.test_get_all_universes()
    test_api.test_get_all_strategies()
    test_api.test_validate_strategy_universe_pair()
    test_api.test_create_configured_strategy()
    test_api.test_get_dashboard_summary()
    test_api.test_get_quick_start_configs()
    test_api.test_search_universes()
    test_api.test_search_strategies()
    
    # Test Custom Universes
    print("\n--- Testing Custom Universe Management ---")
    test_custom = TestCustomUniverses()
    test_custom.test_create_custom_universe()
    
    # Test Config Manager
    print("\n--- Testing Enhanced Config Manager ---")
    test_manager = TestConfigManager()
    test_manager.test_list_universes()
    test_manager.test_list_strategies()
    test_manager.test_get_universe_symbols()
    test_manager.test_create_strategy()
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70 + "\n")
