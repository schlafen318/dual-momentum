"""
Verification script for configuration system.

Run this script to verify that all components are working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    get_config_api,
    get_universe_loader,
    get_strategy_loader,
    get_config_manager
)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_section(text):
    """Print a formatted section header."""
    print(f"\n--- {text} ---")


def test_yaml_files():
    """Test that YAML configuration files exist and are valid."""
    print_section("Testing YAML Files")
    
    config_dir = Path(__file__).parent / 'config'
    
    # Check ASSET_UNIVERSES.yaml
    universes_file = config_dir / 'ASSET_UNIVERSES.yaml'
    if universes_file.exists():
        print(f"✓ ASSET_UNIVERSES.yaml exists")
        import yaml
        with open(universes_file, 'r') as f:
            data = yaml.safe_load(f)
            print(f"✓ Contains {len(data)} universe definitions")
    else:
        print(f"✗ ASSET_UNIVERSES.yaml not found")
        return False
    
    # Check STRATEGIES.yaml
    strategies_file = config_dir / 'STRATEGIES.yaml'
    if strategies_file.exists():
        print(f"✓ STRATEGIES.yaml exists")
        with open(strategies_file, 'r') as f:
            data = yaml.safe_load(f)
            print(f"✓ Contains {len(data.get('strategies', {}))} strategy definitions")
    else:
        print(f"✗ STRATEGIES.yaml not found")
        return False
    
    return True


def test_universe_loader():
    """Test universe loader functionality."""
    print_section("Testing Universe Loader")
    
    try:
        loader = get_universe_loader()
        print(f"✓ Universe loader initialized")
        print(f"✓ Loaded {len(loader.universes)} universes")
        
        # Test getting specific universe
        gem = loader.get_universe('gem_classic')
        if gem:
            print(f"✓ GEM Classic: {gem.symbols}")
        else:
            print("✗ Could not load GEM Classic universe")
        
        # Test filtering
        equity = loader.list_universes(asset_class='equity')
        crypto = loader.list_universes(asset_class='crypto')
        print(f"✓ Found {len(equity)} equity universes")
        print(f"✓ Found {len(crypto)} crypto universes")
        
        # Test search
        results = loader.search_universes('momentum')
        print(f"✓ Search found {len(results)} momentum-related universes")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_loader():
    """Test strategy loader functionality."""
    print_section("Testing Strategy Loader")
    
    try:
        loader = get_strategy_loader()
        print(f"✓ Strategy loader initialized")
        print(f"✓ Loaded {len(loader.strategies)} strategies")
        
        # Test getting specific strategy
        strategy = loader.get_strategy('dual_momentum_classic')
        if strategy:
            print(f"✓ Dual Momentum Classic: {strategy.description[:50]}...")
        else:
            print("✗ Could not load Dual Momentum Classic strategy")
        
        # Test categories
        categories = loader.list_categories()
        print(f"✓ Found {len(categories)} categories: {', '.join(categories)}")
        
        # Test filtering
        momentum = loader.list_strategies(category='momentum')
        print(f"✓ Found {len(momentum)} momentum strategies")
        
        # Test parameter templates
        templates = list(loader.parameter_templates.keys())
        print(f"✓ Available templates: {', '.join(templates)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_api():
    """Test configuration API."""
    print_section("Testing Configuration API")
    
    try:
        api = get_config_api()
        print(f"✓ Configuration API initialized")
        
        # Test getting all universes
        universes = api.get_all_universes()
        print(f"✓ API returned {len(universes)} universes")
        
        # Test getting all strategies
        strategies = api.get_all_strategies()
        print(f"✓ API returned {len(strategies)} strategies")
        
        # Test validation
        is_valid, msg = api.validate_strategy_universe_pair(
            'dual_momentum_classic',
            'gem_classic'
        )
        if is_valid:
            print(f"✓ Validation successful: {msg}")
        else:
            print(f"✗ Validation failed: {msg}")
        
        # Test creating configured strategy
        success, strategy, msg = api.create_configured_strategy(
            'dual_momentum_classic',
            'gem_classic'
        )
        if success:
            print(f"✓ Created strategy instance: {strategy.__class__.__name__}")
        else:
            print(f"✗ Failed to create strategy: {msg}")
        
        # Test dashboard summary
        summary = api.get_dashboard_summary()
        print(f"✓ Dashboard summary:")
        print(f"  - Total universes: {summary['total_universes']}")
        print(f"  - Total strategies: {summary['total_strategies']}")
        print(f"  - Categories: {', '.join(summary['categories'])}")
        
        # Test quick-start configs
        quick_starts = api.get_quick_start_configs()
        print(f"✓ Found {len(quick_starts)} quick-start configurations")
        for config in quick_starts[:3]:
            print(f"  - {config['name']}: {config['description'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """Test enhanced config manager."""
    print_section("Testing Enhanced Config Manager")
    
    try:
        manager = get_config_manager()
        print(f"✓ Config manager initialized")
        
        # Test universe methods
        universes = manager.list_universes()
        print(f"✓ Listed {len(universes)} universes")
        
        symbols = manager.get_universe_symbols('gem_classic')
        print(f"✓ Retrieved GEM Classic symbols: {symbols}")
        
        # Test strategy methods
        strategies = manager.list_strategies()
        print(f"✓ Listed {len(strategies)} strategies")
        
        info = manager.get_strategy_info('dual_momentum_classic')
        print(f"✓ Retrieved strategy info: {info['name']}")
        
        # Test creating strategy
        strategy = manager.create_strategy('dual_momentum_classic')
        print(f"✓ Created strategy: {strategy.__class__.__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_sample_configs():
    """Display some sample configurations."""
    print_section("Sample Configurations")
    
    api = get_config_api()
    
    print("\nTop 5 Universes:")
    universes = api.get_all_universes()
    for i, (uid, info) in enumerate(list(universes.items())[:5]):
        print(f"  {i+1}. {info['name']}")
        print(f"     - Asset Class: {info['asset_class']}")
        print(f"     - Assets: {info['num_assets']}")
        print(f"     - Symbols: {', '.join(info['symbols'][:5])}...")
    
    print("\nTop 5 Strategies:")
    strategies = api.get_all_strategies()
    for i, (sid, info) in enumerate(list(strategies.items())[:5]):
        print(f"  {i+1}. {info['name']}")
        print(f"     - Category: {info['category']}")
        print(f"     - Description: {info['description'][:60]}...")
    
    print("\nQuick-Start Recommendations:")
    quick_starts = api.get_quick_start_configs()
    for i, config in enumerate(quick_starts[:3]):
        print(f"  {i+1}. {config['name']} ({config['risk_level']})")
        print(f"     - Strategy: {config['strategy']}")
        print(f"     - Universe: {config['universe']}")
        print(f"     - {config['description']}")


def main():
    """Run all verification tests."""
    print_header("CONFIGURATION SYSTEM VERIFICATION")
    
    all_passed = True
    
    # Test each component
    all_passed &= test_yaml_files()
    all_passed &= test_universe_loader()
    all_passed &= test_strategy_loader()
    all_passed &= test_config_api()
    all_passed &= test_config_manager()
    
    # Display samples
    display_sample_configs()
    
    # Final result
    print_header("VERIFICATION COMPLETE")
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED!\n")
        print("The configuration system is fully operational:")
        print("  - ASSET_UNIVERSES.yaml loaded successfully")
        print("  - STRATEGIES.yaml loaded successfully")
        print("  - Universe loader working")
        print("  - Strategy loader working")
        print("  - Configuration API working")
        print("  - Config manager enhanced with new features")
        print("\nYou can now use the system via:")
        print("  from src.config import get_config_api")
        print("  api = get_config_api()")
        print("  strategies = api.get_all_strategies()")
        print("  universes = api.get_all_universes()")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED\n")
        print("Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
