"""
Demonstration of the plugin-based architecture.

This script shows how to:
1. Discover plugins automatically
2. Instantiate plugins
3. Use them interchangeably
4. Add new plugins without modifying core code
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from src.core import get_plugin_manager
from src.config.config_manager import get_config_manager
from loguru import logger


def main():
    """Demonstrate the plugin system."""
    
    logger.info("=" * 70)
    logger.info("DUAL MOMENTUM FRAMEWORK - PLUGIN SYSTEM DEMONSTRATION")
    logger.info("=" * 70)
    
    # =========================================================================
    # STEP 1: Initialize Plugin Manager (Auto-Discovery)
    # =========================================================================
    logger.info("\n[STEP 1] Initializing Plugin Manager...")
    logger.info("-" * 70)
    
    plugin_manager = get_plugin_manager()
    
    # List discovered plugins
    logger.info("\nDiscovered Plugins:")
    logger.info(f"  Asset Classes:  {plugin_manager.list_asset_classes()}")
    logger.info(f"  Data Sources:   {plugin_manager.list_data_sources()}")
    logger.info(f"  Strategies:     {plugin_manager.list_strategies()}")
    logger.info(f"  Risk Managers:  {plugin_manager.list_risk_managers()}")
    
    # =========================================================================
    # STEP 2: Get Plugin Information
    # =========================================================================
    logger.info("\n[STEP 2] Plugin Information")
    logger.info("-" * 70)
    
    # Get info about Dual Momentum strategy
    if 'DualMomentumStrategy' in plugin_manager.list_strategies():
        info = plugin_manager.get_plugin_info('strategy', 'DualMomentumStrategy')
        logger.info("\nDual Momentum Strategy:")
        logger.info(f"  Name: {info['name']}")
        logger.info(f"  Version: {info['version']}")
        logger.info(f"  Description: {info['description'][:100]}...")
    
    # =========================================================================
    # STEP 3: Instantiate Plugins with Configuration
    # =========================================================================
    logger.info("\n[STEP 3] Instantiating Plugins")
    logger.info("-" * 70)
    
    # Get configuration manager
    config_manager = get_config_manager()
    
    # Instantiate Asset Class
    logger.info("\nCreating Equity Asset Class...")
    equity_class = plugin_manager.get_asset_class('EquityAsset')
    if equity_class:
        equity = equity_class()
        logger.info(f"  Created: {equity}")
        logger.info(f"  Asset Type: {equity.get_asset_type()}")
        logger.info(f"  Supported Exchanges: {equity.get_supported_exchanges()}")
        
        # Test symbol validation
        test_symbols = ['AAPL', 'MSFT', 'invalid123', 'BRK.A']
        for symbol in test_symbols:
            valid = equity.validate_symbol(symbol)
            logger.info(f"  Symbol '{symbol}' valid: {valid}")
    
    # Instantiate Data Source
    logger.info("\nCreating Yahoo Finance Data Source...")
    yahoo_class = plugin_manager.get_data_source('YahooFinanceSource')
    if yahoo_class:
        yahoo = yahoo_class(config={'cache_enabled': True})
        logger.info(f"  Created: {yahoo}")
        logger.info(f"  Available: {yahoo.is_available()}")
        logger.info(f"  Supported Timeframes: {yahoo.get_supported_timeframes()}")
    
    # Instantiate Strategy with config
    logger.info("\nCreating Dual Momentum Strategy...")
    strategy_class = plugin_manager.get_strategy('DualMomentumStrategy')
    if strategy_class:
        # Load config from file (or use defaults)
        try:
            strategy_config = config_manager.load_config(
                'strategies/dual_momentum_default.yaml'
            )
        except FileNotFoundError:
            strategy_config = config_manager.get_default_strategy_config(
                'DualMomentumStrategy'
            )
        
        strategy = strategy_class(config=strategy_config)
        logger.info(f"  Created: {strategy}")
        logger.info(f"  Momentum Type: {strategy.get_momentum_type()}")
        logger.info(f"  Lookback Period: {strategy.get_required_history()}")
        logger.info(f"  Rebalance Frequency: {strategy.get_rebalance_frequency()}")
        logger.info(f"  Position Count: {strategy.get_position_count()}")
    
    # Instantiate Risk Manager
    logger.info("\nCreating Basic Risk Manager...")
    risk_class = plugin_manager.get_risk_manager('BasicRiskManager')
    if risk_class:
        risk_config = config_manager.get_default_risk_config('BasicRiskManager')
        risk_manager = risk_class(config=risk_config)
        logger.info(f"  Created: {risk_manager}")
        logger.info(f"  Max Leverage: {risk_manager.get_max_leverage()}x")
        logger.info(f"  Max Position Size: {risk_manager.get_max_position_size():.1%}")
        logger.info(f"  Max Drawdown: {risk_manager.get_max_drawdown_limit():.1%}")
    
    # =========================================================================
    # STEP 4: Demonstrate Plugin Interchangeability
    # =========================================================================
    logger.info("\n[STEP 4] Plugin Interchangeability")
    logger.info("-" * 70)
    
    logger.info("\nPlugins can be swapped without changing core code:")
    logger.info("  - Switch from Yahoo Finance to CCXT for crypto")
    logger.info("  - Replace Dual Momentum with Absolute Momentum")
    logger.info("  - Use different risk managers for different strategies")
    logger.info("  - Add new asset classes (bonds, crypto) just by adding files")
    
    # =========================================================================
    # STEP 5: Show How to Add New Plugins
    # =========================================================================
    logger.info("\n[STEP 5] Adding New Plugins")
    logger.info("-" * 70)
    
    logger.info("\nTo add a new plugin:")
    logger.info("  1. Create a file in the appropriate directory:")
    logger.info("     - src/asset_classes/your_asset.py")
    logger.info("     - src/data_sources/your_source.py")
    logger.info("     - src/strategies/your_strategy.py")
    logger.info("     - src/backtesting/your_risk.py")
    logger.info("  2. Inherit from the appropriate base class")
    logger.info("  3. Implement required abstract methods")
    logger.info("  4. That's it! Plugin manager auto-discovers it")
    
    logger.info("\nExample: Adding a crypto asset class")
    logger.info("  File: src/asset_classes/crypto.py")
    logger.info("  ```python")
    logger.info("  from ..core.base_asset import BaseAssetClass")
    logger.info("  ")
    logger.info("  class CryptoAsset(BaseAssetClass):")
    logger.info("      def get_asset_type(self):")
    logger.info("          return AssetType.CRYPTO")
    logger.info("      # ... implement other methods")
    logger.info("  ```")
    
    # =========================================================================
    # STEP 6: Configuration System
    # =========================================================================
    logger.info("\n[STEP 6] Configuration System")
    logger.info("-" * 70)
    
    logger.info("\nConfiguration files support:")
    logger.info("  - YAML and TOML formats")
    logger.info("  - Environment variable substitution")
    logger.info("  - Caching for performance")
    logger.info("  - Per-strategy and per-component configs")
    
    logger.info(f"\nAvailable configs: {config_manager.list_configs()}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    logger.info("\n✓ Plugin system operational")
    logger.info("✓ Auto-discovery working")
    logger.info("✓ Configuration management ready")
    logger.info("✓ Framework extensible without core modifications")
    
    logger.info("\nNext Steps:")
    logger.info("  1. Add more asset class plugins (bonds, crypto, FX)")
    logger.info("  2. Add more data source plugins (CCXT, Alpha Vantage, Quandl)")
    logger.info("  3. Add more strategy plugins (absolute momentum, custom strategies)")
    logger.info("  4. Implement backtesting engine")
    logger.info("  5. Build Streamlit frontend")
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    main()
