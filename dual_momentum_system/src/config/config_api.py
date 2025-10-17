"""
Configuration API for Frontend.

Provides high-level API for frontend to interact with universes and strategies.
"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger

from .universe_loader import UniverseLoader, get_universe_loader
from .strategy_loader import StrategyLoader, get_strategy_loader
from .config_manager import ConfigManager, get_config_manager


class ConfigAPI:
    """
    High-level API for configuration management.
    
    Provides easy-to-use methods for frontend to interact with
    asset universes and strategies.
    
    Example:
        >>> api = ConfigAPI()
        >>> 
        >>> # Get all universes
        >>> universes = api.get_all_universes()
        >>> 
        >>> # Create custom universe
        >>> api.create_universe('my_tech_stocks', {
        ...     'name': 'My Tech Stocks',
        ...     'symbols': ['AAPL', 'MSFT', 'GOOGL']
        ... })
        >>> 
        >>> # Get strategy with universe
        >>> strategy = api.create_configured_strategy(
        ...     'dual_momentum_classic',
        ...     'gem_classic'
        ... )
    """
    
    def __init__(self):
        """Initialize configuration API."""
        self.universe_loader = get_universe_loader()
        self.strategy_loader = get_strategy_loader()
        self.config_manager = get_config_manager()
    
    # ========================================================================
    # UNIVERSE OPERATIONS
    # ========================================================================
    
    def get_all_universes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available universes.
        
        Returns:
            Dictionary mapping universe IDs to their info
        """
        universe_ids = self.universe_loader.list_universes()
        return {
            uid: self.universe_loader.get_universe_info(uid)
            for uid in universe_ids
        }
    
    def get_universes_by_asset_class(self, asset_class: str) -> Dict[str, Dict[str, Any]]:
        """
        Get universes filtered by asset class.
        
        Args:
            asset_class: Asset class filter
        
        Returns:
            Dictionary of matching universes
        """
        universe_ids = self.universe_loader.list_universes(asset_class=asset_class)
        return {
            uid: self.universe_loader.get_universe_info(uid)
            for uid in universe_ids
        }
    
    def get_universe(self, universe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get universe by ID.
        
        Args:
            universe_id: Universe identifier
        
        Returns:
            Universe info dictionary or None
        """
        return self.universe_loader.get_universe_info(universe_id)
    
    def search_universes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search universes by name or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching universes
        """
        universe_ids = self.universe_loader.search_universes(query)
        return [
            self.universe_loader.get_universe_info(uid)
            for uid in universe_ids
        ]
    
    def create_universe(
        self,
        universe_id: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Create a new custom universe.
        
        Args:
            universe_id: Unique identifier
            config: Universe configuration
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate config
            if 'symbols' not in config or not config['symbols']:
                return False, "No symbols provided"
            
            if 'asset_class' not in config:
                config['asset_class'] = 'equity'
            
            if 'name' not in config:
                config['name'] = universe_id
            
            if 'description' not in config:
                config['description'] = ''
            
            if 'benchmark' not in config:
                config['benchmark'] = config['symbols'][0] if config['symbols'] else ''
            
            if 'metadata' not in config:
                config['metadata'] = {}
            
            # Create universe
            self.universe_loader.add_custom_universe(universe_id, config, save=True)
            
            return True, f"Successfully created universe '{universe_id}'"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Error creating universe: {e}")
            return False, f"Error: {str(e)}"
    
    def update_universe(
        self,
        universe_id: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Update an existing universe.
        
        Args:
            universe_id: Universe identifier
            config: Updated configuration
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate config
            if 'symbols' not in config or not config['symbols']:
                return False, "No symbols provided"
            
            # Update universe
            self.universe_loader.update_custom_universe(universe_id, config, save=True)
            
            return True, f"Successfully updated universe '{universe_id}'"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Error updating universe: {e}")
            return False, f"Error: {str(e)}"
    
    def delete_universe(self, universe_id: str) -> Tuple[bool, str]:
        """
        Delete a custom universe.
        
        Args:
            universe_id: Universe identifier
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self.universe_loader.delete_custom_universe(universe_id, save=True)
            return True, f"Successfully deleted universe '{universe_id}'"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Error deleting universe: {e}")
            return False, f"Error: {str(e)}"
    
    def import_universes_from_file(
        self,
        filepath: Path
    ) -> Tuple[bool, str, List[str]]:
        """
        Import universes from YAML file.
        
        Args:
            filepath: Path to YAML file
        
        Returns:
            Tuple of (success, message, imported_ids)
        """
        try:
            imported = self.universe_loader.import_universe(filepath, save=True)
            return True, f"Imported {len(imported)} universes", imported
        except Exception as e:
            logger.error(f"Error importing universes: {e}")
            return False, f"Error: {str(e)}", []
    
    def export_universe_to_file(
        self,
        universe_id: str,
        filepath: Path
    ) -> Tuple[bool, str]:
        """
        Export universe to YAML file.
        
        Args:
            universe_id: Universe identifier
            filepath: Output file path
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self.universe_loader.export_universe(universe_id, filepath)
            return True, f"Exported universe to {filepath}"
        except Exception as e:
            logger.error(f"Error exporting universe: {e}")
            return False, f"Error: {str(e)}"
    
    # ========================================================================
    # STRATEGY OPERATIONS
    # ========================================================================
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available strategies.
        
        Returns:
            Dictionary mapping strategy IDs to their info
        """
        strategy_ids = self.strategy_loader.list_strategies()
        return {
            sid: self.strategy_loader.get_strategy_info(sid)
            for sid in strategy_ids
        }
    
    def get_strategies_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Get strategies filtered by category.
        
        Args:
            category: Strategy category
        
        Returns:
            Dictionary of matching strategies
        """
        strategy_ids = self.strategy_loader.list_strategies(category=category)
        return {
            sid: self.strategy_loader.get_strategy_info(sid)
            for sid in strategy_ids
        }
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy by ID.
        
        Args:
            strategy_id: Strategy identifier
        
        Returns:
            Strategy info dictionary or None
        """
        return self.strategy_loader.get_strategy_info(strategy_id)
    
    def search_strategies(self, query: str) -> List[Dict[str, Any]]:
        """
        Search strategies by name, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            List of matching strategies
        """
        strategy_ids = self.strategy_loader.search_strategies(query)
        return [
            self.strategy_loader.get_strategy_info(sid)
            for sid in strategy_ids
        ]
    
    def list_categories(self) -> List[str]:
        """
        List all strategy categories.
        
        Returns:
            List of category names
        """
        return self.strategy_loader.list_categories()
    
    def list_tags(self) -> List[str]:
        """
        List all strategy tags.
        
        Returns:
            List of tag names
        """
        return self.strategy_loader.list_tags()
    
    def get_compatible_universes(self, strategy_id: str) -> List[str]:
        """
        Get universes compatible with a strategy.
        
        Args:
            strategy_id: Strategy identifier
        
        Returns:
            List of compatible universe IDs
        """
        return self.strategy_loader.get_compatible_universes(
            strategy_id,
            self.universe_loader
        )
    
    def validate_strategy_universe_pair(
        self,
        strategy_id: str,
        universe_id: str
    ) -> Tuple[bool, str]:
        """
        Validate if strategy and universe are compatible.
        
        Args:
            strategy_id: Strategy identifier
            universe_id: Universe identifier
        
        Returns:
            Tuple of (is_valid, message)
        """
        return self.strategy_loader.validate_strategy_universe(
            strategy_id,
            universe_id,
            self.universe_loader
        )
    
    def create_configured_strategy(
        self,
        strategy_id: str,
        universe_id: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any, str]:
        """
        Create a fully configured strategy instance.
        
        Args:
            strategy_id: Strategy identifier
            universe_id: Universe to use (optional)
            custom_params: Custom parameters (optional)
        
        Returns:
            Tuple of (success, strategy_instance, message)
        """
        try:
            # Validate strategy exists
            strategy_config = self.strategy_loader.get_strategy(strategy_id)
            if not strategy_config:
                return False, None, f"Strategy '{strategy_id}' not found"
            
            # If universe specified, add it to params and validate
            params = custom_params.copy() if custom_params else {}
            
            if universe_id:
                # Validate compatibility
                is_valid, msg = self.validate_strategy_universe_pair(
                    strategy_id,
                    universe_id
                )
                if not is_valid:
                    return False, None, msg
                
                # Get universe symbols
                symbols = self.universe_loader.get_symbols(universe_id)
                params['universe'] = symbols
            
            # Create strategy
            strategy = self.strategy_loader.create_strategy(strategy_id, params)
            
            return True, strategy, "Strategy created successfully"
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return False, None, f"Error: {str(e)}"
    
    def get_parameter_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available parameter templates.
        
        Returns:
            Dictionary of parameter templates
        """
        return self.strategy_loader.parameter_templates
    
    def get_rebalancing_frequencies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available rebalancing frequencies.
        
        Returns:
            Dictionary of rebalancing options
        """
        return self.strategy_loader.rebalancing_info
    
    def get_safe_assets(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available safe assets.
        
        Returns:
            Dictionary of safe asset options
        """
        return self.strategy_loader.safe_assets
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for dashboard.
        
        Returns:
            Summary dictionary
        """
        return {
            'total_universes': len(self.universe_loader.list_universes()),
            'total_strategies': len(self.strategy_loader.list_strategies()),
            'categories': self.list_categories(),
            'asset_classes': list(set(
                u.asset_class
                for u in self.universe_loader.universes.values()
            ))
        }
    
    def get_quick_start_configs(self) -> List[Dict[str, Any]]:
        """
        Get recommended quick-start configurations.
        
        Returns:
            List of recommended strategy-universe pairs
        """
        recommendations = [
            {
                'name': 'Classic GEM',
                'strategy': 'dual_momentum_classic',
                'universe': 'gem_classic',
                'description': 'Gary Antonacci\'s classic Global Equity Momentum',
                'risk_level': 'Moderate',
                'category': 'Global Tactical'
            },
            {
                'name': 'US Sector Rotation',
                'strategy': 'sector_rotation_monthly',
                'universe': 'global_sectors_us',
                'description': 'Monthly rotation across US sectors',
                'risk_level': 'Moderate',
                'category': 'Sector Rotation'
            },
            {
                'name': 'Crypto Momentum',
                'strategy': 'crypto_momentum_weekly',
                'universe': 'crypto_major',
                'description': 'High-frequency crypto momentum',
                'risk_level': 'Aggressive',
                'category': 'Cryptocurrency'
            },
            {
                'name': 'Multi-Asset Tactical',
                'strategy': 'multi_asset_tactical',
                'universe': 'multi_asset_balanced',
                'description': 'Balanced multi-asset allocation',
                'risk_level': 'Moderate',
                'category': 'Multi-Asset'
            },
            {
                'name': 'Aggressive Growth',
                'strategy': 'dual_momentum_aggressive',
                'universe': 'multi_asset_aggressive',
                'description': 'Aggressive growth with top 3 assets',
                'risk_level': 'Aggressive',
                'category': 'Growth'
            },
            {
                'name': 'Conservative Income',
                'strategy': 'dividend_momentum',
                'universe': 'dividend_aristocrats',
                'description': 'Dividend-focused momentum',
                'risk_level': 'Conservative',
                'category': 'Income'
            }
        ]
        
        return recommendations
    
    def validate_config(
        self,
        strategy_id: str,
        universe_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a complete configuration.
        
        Args:
            strategy_id: Strategy identifier
            universe_id: Universe identifier (optional)
            params: Strategy parameters (optional)
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate strategy exists
        if not self.strategy_loader.get_strategy(strategy_id):
            errors.append(f"Strategy '{strategy_id}' not found")
            return False, errors, warnings
        
        # Validate universe if specified
        if universe_id:
            if not self.universe_loader.get_universe(universe_id):
                errors.append(f"Universe '{universe_id}' not found")
            else:
                is_valid, msg = self.validate_strategy_universe_pair(
                    strategy_id,
                    universe_id
                )
                if not is_valid:
                    errors.append(msg)
        
        # Validate parameters if specified
        if params:
            strategy_config = self.strategy_loader.get_strategy(strategy_id)
            if strategy_config:
                default_params = strategy_config.parameters
                
                # Check for unknown parameters
                for key in params:
                    if key not in default_params:
                        warnings.append(f"Unknown parameter: {key}")
                
                # Check for missing required parameters
                # (In this system, all parameters have defaults)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings


# Global API instance
_global_config_api: Optional[ConfigAPI] = None


def get_config_api() -> ConfigAPI:
    """
    Get the global configuration API instance.
    
    Returns:
        Global ConfigAPI instance
    """
    global _global_config_api
    
    if _global_config_api is None:
        _global_config_api = ConfigAPI()
    
    return _global_config_api
