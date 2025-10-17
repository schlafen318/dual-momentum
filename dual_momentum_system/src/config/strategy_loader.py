"""
Strategy Loader.

Handles loading and management of strategy configurations from registry.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import yaml
from loguru import logger
from dataclasses import dataclass
import importlib


@dataclass
class StrategyConfig:
    """Strategy configuration."""
    
    strategy_id: str
    name: str
    description: str
    class_name: str
    module: str
    version: str
    category: str
    parameters: Dict[str, Any]
    recommended_universes: List[str]
    min_assets: int
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'class': self.class_name,
            'module': self.module,
            'version': self.version,
            'category': self.category,
            'parameters': self.parameters,
            'recommended_universes': self.recommended_universes,
            'min_assets': self.min_assets,
            'tags': self.tags
        }
    
    def get_strategy_class(self) -> Type:
        """
        Dynamically import and return strategy class.
        
        Returns:
            Strategy class
        """
        module_path = self.module.replace('src.', '')
        module = importlib.import_module(f"src.{module_path}")
        return getattr(module, self.class_name)
    
    def create_instance(self, custom_params: Optional[Dict[str, Any]] = None):
        """
        Create strategy instance with parameters.
        
        Args:
            custom_params: Custom parameters to override defaults
        
        Returns:
            Strategy instance
        """
        strategy_class = self.get_strategy_class()
        
        # Merge parameters
        params = self.parameters.copy()
        if custom_params:
            params.update(custom_params)
        
        return strategy_class(config=params)


class StrategyLoader:
    """
    Strategy loader and registry manager.
    
    Loads strategy configurations from STRATEGIES.yaml and provides
    access to strategy metadata and instantiation.
    
    Example:
        >>> loader = StrategyLoader()
        >>> strategy_config = loader.get_strategy('dual_momentum_classic')
        >>> strategy = strategy_config.create_instance()
        
        >>> # List strategies by category
        >>> momentum_strategies = loader.list_strategies(category='momentum')
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize strategy loader.
        
        Args:
            config_dir: Directory containing config files
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.strategies_file = self.config_dir / "STRATEGIES.yaml"
        
        # Load strategies
        self.strategies: Dict[str, StrategyConfig] = {}
        self.parameter_templates: Dict[str, Dict[str, Any]] = {}
        self.rebalancing_info: Dict[str, Dict[str, Any]] = {}
        self.safe_assets: Dict[str, Dict[str, Any]] = {}
        
        self._load_strategies()
        
        logger.info(f"Loaded {len(self.strategies)} strategy configurations")
    
    def _load_strategies(self) -> None:
        """Load strategies from YAML file."""
        if not self.strategies_file.exists():
            logger.warning(f"Strategies file not found: {self.strategies_file}")
            return
        
        with open(self.strategies_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.warning("Strategies file is empty")
            return
        
        # Load strategies
        strategies_data = data.get('strategies', {})
        for strategy_id, config in strategies_data.items():
            try:
                strategy_config = StrategyConfig(
                    strategy_id=strategy_id,
                    name=config.get('name', strategy_id),
                    description=config.get('description', ''),
                    class_name=config.get('class', ''),
                    module=config.get('module', ''),
                    version=config.get('version', '1.0.0'),
                    category=config.get('category', 'unknown'),
                    parameters=config.get('parameters', {}),
                    recommended_universes=config.get('recommended_universes', []),
                    min_assets=config.get('min_assets', 1),
                    tags=config.get('tags', [])
                )
                
                self.strategies[strategy_id] = strategy_config
                
            except Exception as e:
                logger.error(f"Error loading strategy '{strategy_id}': {e}")
        
        # Load parameter templates
        self.parameter_templates = data.get('parameter_templates', {})
        
        # Load rebalancing info
        self.rebalancing_info = data.get('rebalancing', {})
        
        # Load safe assets
        self.safe_assets = data.get('safe_assets', {})
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """
        Get strategy configuration by ID.
        
        Args:
            strategy_id: Strategy identifier
        
        Returns:
            StrategyConfig object or None if not found
        """
        return self.strategies.get(strategy_id)
    
    def list_strategies(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        min_assets: Optional[int] = None
    ) -> List[str]:
        """
        List available strategies with optional filters.
        
        Args:
            category: Filter by category
            tag: Filter by tag
            min_assets: Minimum number of required assets
        
        Returns:
            List of strategy IDs
        """
        strategies = []
        
        for strategy_id, config in self.strategies.items():
            # Apply filters
            if category and config.category != category:
                continue
            
            if tag and tag not in config.tags:
                continue
            
            if min_assets and config.min_assets < min_assets:
                continue
            
            strategies.append(strategy_id)
        
        return sorted(strategies)
    
    def search_strategies(self, query: str) -> List[str]:
        """
        Search strategies by name or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching strategy IDs
        """
        query_lower = query.lower()
        matches = []
        
        for strategy_id, config in self.strategies.items():
            if (query_lower in config.name.lower() or
                query_lower in config.description.lower() or
                query_lower in strategy_id.lower() or
                any(query_lower in tag.lower() for tag in config.tags)):
                matches.append(strategy_id)
        
        return sorted(matches)
    
    def get_strategies_by_category(self) -> Dict[str, List[str]]:
        """
        Get strategies grouped by category.
        
        Returns:
            Dictionary mapping categories to strategy IDs
        """
        categories: Dict[str, List[str]] = {}
        
        for strategy_id, config in self.strategies.items():
            category = config.category
            if category not in categories:
                categories[category] = []
            categories[category].append(strategy_id)
        
        return categories
    
    def get_parameter_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get parameter template by name.
        
        Args:
            template_name: Template name (e.g., 'conservative', 'aggressive')
        
        Returns:
            Parameter dictionary or None if not found
        """
        return self.parameter_templates.get(template_name)
    
    def create_strategy(
        self,
        strategy_id: str,
        custom_params: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None
    ):
        """
        Create strategy instance.
        
        Args:
            strategy_id: Strategy identifier
            custom_params: Custom parameters to override defaults
            template: Parameter template to apply ('conservative', 'aggressive', etc.)
        
        Returns:
            Strategy instance
        
        Raises:
            ValueError: If strategy not found
        """
        config = self.get_strategy(strategy_id)
        if not config:
            raise ValueError(f"Strategy '{strategy_id}' not found")
        
        # Start with default parameters
        params = config.parameters.copy()
        
        # Apply template if specified
        if template:
            template_params = self.get_parameter_template(template)
            if template_params:
                params.update(template_params)
            else:
                logger.warning(f"Template '{template}' not found")
        
        # Apply custom parameters
        if custom_params:
            params.update(custom_params)
        
        return config.create_instance(params)
    
    def get_strategy_info(self, strategy_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a strategy.
        
        Args:
            strategy_id: Strategy identifier
        
        Returns:
            Dictionary with strategy information
        """
        config = self.get_strategy(strategy_id)
        if not config:
            return {}
        
        return {
            'id': strategy_id,
            'name': config.name,
            'description': config.description,
            'class': config.class_name,
            'module': config.module,
            'version': config.version,
            'category': config.category,
            'parameters': config.parameters,
            'recommended_universes': config.recommended_universes,
            'min_assets': config.min_assets,
            'tags': config.tags
        }
    
    def get_compatible_universes(
        self,
        strategy_id: str,
        universe_loader: Any = None
    ) -> List[str]:
        """
        Get universes compatible with a strategy.
        
        Args:
            strategy_id: Strategy identifier
            universe_loader: UniverseLoader instance (optional)
        
        Returns:
            List of compatible universe IDs
        """
        config = self.get_strategy(strategy_id)
        if not config:
            return []
        
        # Start with recommended universes
        compatible = config.recommended_universes.copy()
        
        # If universe loader provided, add other compatible universes
        if universe_loader:
            all_universes = universe_loader.list_universes()
            for universe_id in all_universes:
                universe = universe_loader.get_universe(universe_id)
                if universe and universe.num_assets >= config.min_assets:
                    if universe_id not in compatible:
                        compatible.append(universe_id)
        
        return compatible
    
    def validate_strategy_universe(
        self,
        strategy_id: str,
        universe_id: str,
        universe_loader: Any = None
    ) -> tuple[bool, str]:
        """
        Validate if a universe is compatible with a strategy.
        
        Args:
            strategy_id: Strategy identifier
            universe_id: Universe identifier
            universe_loader: UniverseLoader instance
        
        Returns:
            Tuple of (is_valid, message)
        """
        config = self.get_strategy(strategy_id)
        if not config:
            return False, f"Strategy '{strategy_id}' not found"
        
        if not universe_loader:
            return True, "No universe loader provided, skipping validation"
        
        universe = universe_loader.get_universe(universe_id)
        if not universe:
            return False, f"Universe '{universe_id}' not found"
        
        if universe.num_assets < config.min_assets:
            return False, (
                f"Universe has {universe.num_assets} assets but strategy requires "
                f"minimum {config.min_assets}"
            )
        
        return True, "Compatible"
    
    def get_rebalancing_info(self, frequency: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a rebalancing frequency.
        
        Args:
            frequency: Rebalancing frequency (e.g., 'monthly', 'weekly')
        
        Returns:
            Rebalancing info dictionary or None
        """
        return self.rebalancing_info.get(frequency)
    
    def get_safe_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a safe asset.
        
        Args:
            symbol: Safe asset symbol (e.g., 'SHY', 'AGG')
        
        Returns:
            Safe asset info dictionary or None
        """
        return self.safe_assets.get(symbol)
    
    def list_categories(self) -> List[str]:
        """
        List all strategy categories.
        
        Returns:
            List of category names
        """
        return sorted(set(config.category for config in self.strategies.values()))
    
    def list_tags(self) -> List[str]:
        """
        List all strategy tags.
        
        Returns:
            List of unique tags
        """
        tags = set()
        for config in self.strategies.values():
            tags.update(config.tags)
        return sorted(tags)
    
    def export_strategy_config(
        self,
        strategy_id: str,
        filepath: Path,
        include_universe: bool = False
    ) -> None:
        """
        Export strategy configuration to YAML file.
        
        Args:
            strategy_id: Strategy identifier
            filepath: Output file path
            include_universe: Include universe definition
        """
        config = self.get_strategy(strategy_id)
        if not config:
            raise ValueError(f"Strategy '{strategy_id}' not found")
        
        export_data = config.to_dict()
        
        with open(filepath, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False)
        
        logger.info(f"Exported strategy '{strategy_id}' to {filepath}")


# Global strategy loader instance
_global_strategy_loader: Optional[StrategyLoader] = None


def get_strategy_loader() -> StrategyLoader:
    """
    Get the global strategy loader instance.
    
    Returns:
        Global StrategyLoader instance
    """
    global _global_strategy_loader
    
    if _global_strategy_loader is None:
        _global_strategy_loader = StrategyLoader()
    
    return _global_strategy_loader
