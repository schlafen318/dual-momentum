"""
Configuration System Usage Examples.

Demonstrates how to use the new configuration system in various scenarios.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config_api


def example_1_list_all_configs():
    """Example 1: List all available configurations."""
    print("\n" + "="*70)
    print("EXAMPLE 1: List All Configurations")
    print("="*70)
    
    api = get_config_api()
    
    # Get dashboard summary
    summary = api.get_dashboard_summary()
    print(f"\n📊 Dashboard Summary:")
    print(f"   Total Universes: {summary['total_universes']}")
    print(f"   Total Strategies: {summary['total_strategies']}")
    print(f"   Categories: {', '.join(summary['categories'])}")
    print(f"   Asset Classes: {', '.join(summary['asset_classes'])}")
    
    # List categories
    print(f"\n📁 Strategy Categories:")
    for category in api.list_categories():
        strategies = api.get_strategies_by_category(category)
        print(f"   {category}: {len(strategies)} strategies")


def example_2_search_and_filter():
    """Example 2: Search and filter configurations."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Search and Filter")
    print("="*70)
    
    api = get_config_api()
    
    # Search universes
    print("\n🔍 Searching universes for 'crypto':")
    crypto_universes = api.search_universes('crypto')
    for universe in crypto_universes[:3]:
        print(f"   - {universe['name']}: {len(universe['symbols'])} assets")
    
    # Search strategies
    print("\n🔍 Searching strategies for 'momentum':")
    momentum_strategies = api.search_strategies('momentum')
    for strategy in momentum_strategies[:3]:
        print(f"   - {strategy['name']}: {strategy['category']}")
    
    # Filter by asset class
    print("\n🔍 Equity universes:")
    equity_universes = api.get_universes_by_asset_class('equity')
    print(f"   Found {len(equity_universes)} equity universes")


def example_3_get_universe_details():
    """Example 3: Get detailed information about a universe."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Universe Details")
    print("="*70)
    
    api = get_config_api()
    
    # Get GEM Classic universe
    universe = api.get_universe('gem_classic')
    
    print(f"\n🌐 {universe['name']}")
    print(f"   Description: {universe['description']}")
    print(f"   Asset Class: {universe['asset_class']}")
    print(f"   Benchmark: {universe['benchmark']}")
    print(f"   Number of Assets: {universe['num_assets']}")
    print(f"   Symbols: {', '.join(universe['symbols'])}")
    print(f"   Recommended Rebalance: {universe['recommended_rebalance']}")


def example_4_get_strategy_details():
    """Example 4: Get detailed information about a strategy."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Strategy Details")
    print("="*70)
    
    api = get_config_api()
    
    # Get Dual Momentum Classic strategy
    strategy = api.get_strategy('dual_momentum_classic')
    
    print(f"\n⚙️  {strategy['name']}")
    print(f"   Description: {strategy['description']}")
    print(f"   Category: {strategy['category']}")
    print(f"   Min Assets: {strategy['min_assets']}")
    print(f"   Tags: {', '.join(strategy['tags'])}")
    
    print(f"\n   Parameters:")
    for key, value in strategy['parameters'].items():
        print(f"      {key}: {value}")
    
    print(f"\n   Recommended Universes:")
    for universe_id in strategy['recommended_universes']:
        print(f"      - {universe_id}")


def example_5_validate_compatibility():
    """Example 5: Validate strategy-universe compatibility."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Validate Compatibility")
    print("="*70)
    
    api = get_config_api()
    
    # Test valid pair
    print("\n✅ Testing: dual_momentum_classic + gem_classic")
    is_valid, msg = api.validate_strategy_universe_pair(
        'dual_momentum_classic',
        'gem_classic'
    )
    print(f"   Result: {msg}")
    
    # Test another valid pair
    print("\n✅ Testing: crypto_momentum_weekly + crypto_major")
    is_valid, msg = api.validate_strategy_universe_pair(
        'crypto_momentum_weekly',
        'crypto_major'
    )
    print(f"   Result: {msg}")


def example_6_quick_start_configs():
    """Example 6: Get quick-start configurations."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Quick-Start Configurations")
    print("="*70)
    
    api = get_config_api()
    
    recommendations = api.get_quick_start_configs()
    
    print(f"\n🚀 Quick-Start Recommendations:")
    for i, config in enumerate(recommendations, 1):
        print(f"\n   {i}. {config['name']} ({config['risk_level']})")
        print(f"      Category: {config['category']}")
        print(f"      Strategy: {config['strategy']}")
        print(f"      Universe: {config['universe']}")
        print(f"      {config['description']}")


def example_7_create_custom_universe():
    """Example 7: Create a custom universe."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Create Custom Universe")
    print("="*70)
    
    api = get_config_api()
    
    # Create custom FAANG universe
    custom_config = {
        'name': 'FAANG Stocks (Example)',
        'description': 'Facebook, Apple, Amazon, Netflix, Google',
        'asset_class': 'equity',
        'symbols': ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL'],
        'benchmark': 'QQQ',
        'metadata': {
            'created_by': 'example_script',
            'sector': 'technology'
        }
    }
    
    print("\n📝 Creating custom universe: 'example_faang'")
    success, msg = api.create_universe('example_faang_temp', custom_config)
    
    if success:
        print(f"   ✓ {msg}")
        
        # Verify it was created
        universe = api.get_universe('example_faang_temp')
        print(f"   Symbols: {', '.join(universe['symbols'])}")
        
        # Clean up
        api.delete_universe('example_faang_temp')
        print("   ✓ Cleaned up example universe")
    else:
        print(f"   ✗ {msg}")


def example_8_parameter_templates():
    """Example 8: Use parameter templates."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Parameter Templates")
    print("="*70)
    
    api = get_config_api()
    
    templates = api.get_parameter_templates()
    
    print("\n📋 Available Parameter Templates:")
    for name, params in templates.items():
        print(f"\n   {name.upper()}: {params.get('description', '')}")
        for key, value in params.items():
            if key != 'description':
                print(f"      {key}: {value}")


def example_9_rebalancing_frequencies():
    """Example 9: Get rebalancing frequency information."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Rebalancing Frequencies")
    print("="*70)
    
    api = get_config_api()
    
    frequencies = api.get_rebalancing_frequencies()
    
    print("\n📅 Rebalancing Frequency Options:")
    for freq, info in frequencies.items():
        print(f"\n   {freq.upper()}:")
        print(f"      Description: {info['description']}")
        print(f"      Days: {info['days']}")
        print(f"      Use Cases: {', '.join(info['use_cases'])}")
        print(f"      Considerations: {info['considerations']}")


def example_10_safe_assets():
    """Example 10: Get safe asset information."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Safe Asset Options")
    print("="*70)
    
    api = get_config_api()
    
    safe_assets = api.get_safe_assets()
    
    print("\n🛡️  Safe Asset Options:")
    for symbol, info in safe_assets.items():
        print(f"\n   {symbol}: {info['name']}")
        print(f"      Description: {info['description']}")
        print(f"      Asset Class: {info['asset_class']}")
        if 'typical_yield' in info:
            print(f"      Typical Yield: {info['typical_yield']}")


def example_11_complete_workflow():
    """Example 11: Complete workflow - select, validate, configure."""
    print("\n" + "="*70)
    print("EXAMPLE 11: Complete Workflow")
    print("="*70)
    
    api = get_config_api()
    
    # Step 1: Choose a strategy
    strategy_id = 'dual_momentum_classic'
    strategy = api.get_strategy(strategy_id)
    print(f"\n1️⃣  Selected Strategy: {strategy['name']}")
    
    # Step 2: Choose a universe
    universe_id = 'gem_classic'
    universe = api.get_universe(universe_id)
    print(f"2️⃣  Selected Universe: {universe['name']}")
    print(f"   Symbols: {', '.join(universe['symbols'])}")
    
    # Step 3: Validate compatibility
    is_valid, msg = api.validate_strategy_universe_pair(strategy_id, universe_id)
    print(f"3️⃣  Validation: {msg}")
    
    if is_valid:
        # Step 4: Validate complete config
        is_valid, errors, warnings = api.validate_config(
            strategy_id,
            universe_id,
            {'lookback_period': 252}
        )
        print(f"4️⃣  Config Validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
        if errors:
            print(f"   Errors: {', '.join(errors)}")
        if warnings:
            print(f"   Warnings: {', '.join(warnings)}")
        
        # Note: Creating actual strategy instance requires pandas
        print(f"\n5️⃣  Ready to create strategy instance")
        print(f"   (Requires pandas and other dependencies)")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("  CONFIGURATION SYSTEM USAGE EXAMPLES")
    print("="*70)
    
    example_1_list_all_configs()
    example_2_search_and_filter()
    example_3_get_universe_details()
    example_4_get_strategy_details()
    example_5_validate_compatibility()
    example_6_quick_start_configs()
    example_7_create_custom_universe()
    example_8_parameter_templates()
    example_9_rebalancing_frequencies()
    example_10_safe_assets()
    example_11_complete_workflow()
    
    print("\n" + "="*70)
    print("  ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
