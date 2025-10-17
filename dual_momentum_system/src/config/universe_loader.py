"""
Asset Universe Loader.

Handles loading and management of pre-built and custom asset universes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from loguru import logger
from dataclasses import dataclass


@dataclass
class AssetUniverse:
    """Asset universe configuration."""
    
    name: str
    description: str
    asset_class: str
    benchmark: str
    symbols: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate universe configuration."""
        if not self.symbols:
            raise ValueError(f"Universe '{self.name}' has no symbols")
        
        if self.asset_class not in ['equity', 'bond', 'commodity', 'crypto', 'fx', 'multi_asset']:
            logger.warning(f"Unknown asset class '{self.asset_class}' for universe '{self.name}'")
    
    @property
    def num_assets(self) -> int:
        """Get number of assets in universe."""
        return len(self.symbols)
    
    @property
    def recommended_rebalance(self) -> str:
        """Get recommended rebalancing frequency."""
        return self.metadata.get('rebalance_recommended', 'monthly')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'asset_class': self.asset_class,
            'benchmark': self.benchmark,
            'symbols': self.symbols,
            'metadata': self.metadata
        }


class UniverseLoader:
    """
    Asset universe loader and manager.
    
    Loads pre-built universes from ASSET_UNIVERSES.yaml and supports
    custom user-defined universes.
    
    Example:
        >>> loader = UniverseLoader()
        >>> gem = loader.get_universe('gem_classic')
        >>> print(gem.symbols)
        ['SPY', 'VEU', 'BND']
        
        >>> # Add custom universe
        >>> loader.add_custom_universe('my_universe', {
        ...     'name': 'My Custom Universe',
        ...     'asset_class': 'equity',
        ...     'symbols': ['AAPL', 'MSFT', 'GOOGL']
        ... })
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize universe loader.
        
        Args:
            config_dir: Directory containing config files
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.universes_file = self.config_dir / "ASSET_UNIVERSES.yaml"
        self.custom_universes_file = self.config_dir / "custom_universes.yaml"
        
        # Load pre-built universes
        self.universes: Dict[str, AssetUniverse] = {}
        self._load_universes()
        
        # Load custom universes if they exist
        self._load_custom_universes()
        
        logger.info(f"Loaded {len(self.universes)} asset universes")
    
    def _load_universes(self) -> None:
        """Load pre-built universes from YAML file."""
        if not self.universes_file.exists():
            logger.warning(f"Universe file not found: {self.universes_file}")
            return
        
        with open(self.universes_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.warning("Universe file is empty")
            return
        
        for universe_id, config in data.items():
            # Skip template and comments
            if universe_id.startswith('_'):
                continue
            
            try:
                universe = AssetUniverse(
                    name=config.get('name', universe_id),
                    description=config.get('description', ''),
                    asset_class=config.get('asset_class', 'equity'),
                    benchmark=config.get('benchmark', config['symbols'][0] if config.get('symbols') else ''),
                    symbols=config.get('symbols', []),
                    metadata=config.get('metadata', {})
                )
                
                self.universes[universe_id] = universe
                
            except Exception as e:
                logger.error(f"Error loading universe '{universe_id}': {e}")
    
    def _load_custom_universes(self) -> None:
        """Load custom user-defined universes."""
        if not self.custom_universes_file.exists():
            return
        
        try:
            with open(self.custom_universes_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return
            
            for universe_id, config in data.items():
                try:
                    universe = AssetUniverse(
                        name=config.get('name', universe_id),
                        description=config.get('description', ''),
                        asset_class=config.get('asset_class', 'equity'),
                        benchmark=config.get('benchmark', config['symbols'][0] if config.get('symbols') else ''),
                        symbols=config.get('symbols', []),
                        metadata=config.get('metadata', {})
                    )
                    
                    self.universes[universe_id] = universe
                    logger.info(f"Loaded custom universe: {universe_id}")
                    
                except Exception as e:
                    logger.error(f"Error loading custom universe '{universe_id}': {e}")
                    
        except Exception as e:
            logger.error(f"Error loading custom universes file: {e}")
    
    def get_universe(self, universe_id: str) -> Optional[AssetUniverse]:
        """
        Get universe by ID.
        
        Args:
            universe_id: Universe identifier
        
        Returns:
            AssetUniverse object or None if not found
        """
        return self.universes.get(universe_id)
    
    def get_symbols(self, universe_id: str) -> List[str]:
        """
        Get symbols for a universe.
        
        Args:
            universe_id: Universe identifier
        
        Returns:
            List of symbols
        """
        universe = self.get_universe(universe_id)
        return universe.symbols if universe else []
    
    def list_universes(
        self,
        asset_class: Optional[str] = None,
        min_assets: Optional[int] = None
    ) -> List[str]:
        """
        List available universes with optional filters.
        
        Args:
            asset_class: Filter by asset class
            min_assets: Minimum number of assets
        
        Returns:
            List of universe IDs
        """
        universes = []
        
        for universe_id, universe in self.universes.items():
            # Apply filters
            if asset_class and universe.asset_class != asset_class:
                continue
            
            if min_assets and universe.num_assets < min_assets:
                continue
            
            universes.append(universe_id)
        
        return sorted(universes)
    
    def search_universes(self, query: str) -> List[str]:
        """
        Search universes by name or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching universe IDs
        """
        query_lower = query.lower()
        matches = []
        
        for universe_id, universe in self.universes.items():
            if (query_lower in universe.name.lower() or
                query_lower in universe.description.lower() or
                query_lower in universe_id.lower()):
                matches.append(universe_id)
        
        return sorted(matches)
    
    def add_custom_universe(
        self,
        universe_id: str,
        config: Dict[str, Any],
        save: bool = True
    ) -> AssetUniverse:
        """
        Add a custom universe.
        
        Args:
            universe_id: Unique identifier for universe
            config: Universe configuration
            save: Whether to persist to file
        
        Returns:
            Created AssetUniverse object
        
        Raises:
            ValueError: If universe_id already exists
        """
        if universe_id in self.universes:
            raise ValueError(f"Universe '{universe_id}' already exists")
        
        # Create universe object
        universe = AssetUniverse(
            name=config.get('name', universe_id),
            description=config.get('description', ''),
            asset_class=config.get('asset_class', 'equity'),
            benchmark=config.get('benchmark', config['symbols'][0] if config.get('symbols') else ''),
            symbols=config.get('symbols', []),
            metadata=config.get('metadata', {})
        )
        
        self.universes[universe_id] = universe
        
        if save:
            self._save_custom_universe(universe_id, config)
        
        logger.info(f"Added custom universe: {universe_id}")
        return universe
    
    def update_custom_universe(
        self,
        universe_id: str,
        config: Dict[str, Any],
        save: bool = True
    ) -> AssetUniverse:
        """
        Update an existing custom universe.
        
        Args:
            universe_id: Universe identifier
            config: Updated configuration
            save: Whether to persist changes
        
        Returns:
            Updated AssetUniverse object
        
        Raises:
            ValueError: If universe not found
        """
        if universe_id not in self.universes:
            raise ValueError(f"Universe '{universe_id}' not found")
        
        # Create updated universe
        universe = AssetUniverse(
            name=config.get('name', universe_id),
            description=config.get('description', ''),
            asset_class=config.get('asset_class', 'equity'),
            benchmark=config.get('benchmark', config['symbols'][0] if config.get('symbols') else ''),
            symbols=config.get('symbols', []),
            metadata=config.get('metadata', {})
        )
        
        self.universes[universe_id] = universe
        
        if save:
            self._save_custom_universe(universe_id, config)
        
        logger.info(f"Updated custom universe: {universe_id}")
        return universe
    
    def delete_custom_universe(
        self,
        universe_id: str,
        save: bool = True
    ) -> None:
        """
        Delete a custom universe.
        
        Args:
            universe_id: Universe identifier
            save: Whether to persist deletion
        
        Raises:
            ValueError: If universe not found
        """
        if universe_id not in self.universes:
            raise ValueError(f"Universe '{universe_id}' not found")
        
        del self.universes[universe_id]
        
        if save:
            self._delete_saved_universe(universe_id)
        
        logger.info(f"Deleted custom universe: {universe_id}")
    
    def _save_custom_universe(self, universe_id: str, config: Dict[str, Any]) -> None:
        """Save custom universe to file."""
        # Load existing custom universes
        custom_universes = {}
        if self.custom_universes_file.exists():
            with open(self.custom_universes_file, 'r') as f:
                custom_universes = yaml.safe_load(f) or {}
        
        # Add/update universe
        custom_universes[universe_id] = config
        
        # Save back to file
        self.custom_universes_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.custom_universes_file, 'w') as f:
            yaml.dump(custom_universes, f, default_flow_style=False, sort_keys=False)
    
    def _delete_saved_universe(self, universe_id: str) -> None:
        """Delete universe from saved file."""
        if not self.custom_universes_file.exists():
            return
        
        with open(self.custom_universes_file, 'r') as f:
            custom_universes = yaml.safe_load(f) or {}
        
        if universe_id in custom_universes:
            del custom_universes[universe_id]
            
            with open(self.custom_universes_file, 'w') as f:
                yaml.dump(custom_universes, f, default_flow_style=False, sort_keys=False)
    
    def get_universe_info(self, universe_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a universe.
        
        Args:
            universe_id: Universe identifier
        
        Returns:
            Dictionary with universe information
        """
        universe = self.get_universe(universe_id)
        if not universe:
            return {}
        
        return {
            'id': universe_id,
            'name': universe.name,
            'description': universe.description,
            'asset_class': universe.asset_class,
            'benchmark': universe.benchmark,
            'num_assets': universe.num_assets,
            'symbols': universe.symbols,
            'recommended_rebalance': universe.recommended_rebalance,
            'metadata': universe.metadata
        }
    
    def export_universe(self, universe_id: str, filepath: Path) -> None:
        """
        Export universe to YAML file.
        
        Args:
            universe_id: Universe identifier
            filepath: Output file path
        """
        universe = self.get_universe(universe_id)
        if not universe:
            raise ValueError(f"Universe '{universe_id}' not found")
        
        with open(filepath, 'w') as f:
            yaml.dump({universe_id: universe.to_dict()}, f, default_flow_style=False)
        
        logger.info(f"Exported universe '{universe_id}' to {filepath}")
    
    def import_universe(
        self,
        filepath: Path,
        universe_id: Optional[str] = None,
        save: bool = True
    ) -> List[str]:
        """
        Import universe(s) from YAML file.
        
        Args:
            filepath: Input file path
            universe_id: Specific universe to import (None = all)
            save: Whether to persist imported universes
        
        Returns:
            List of imported universe IDs
        """
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        imported = []
        
        for uid, config in data.items():
            if universe_id and uid != universe_id:
                continue
            
            try:
                self.add_custom_universe(uid, config, save=save)
                imported.append(uid)
            except ValueError as e:
                logger.warning(f"Skipping universe '{uid}': {e}")
        
        logger.info(f"Imported {len(imported)} universes from {filepath}")
        return imported


# Global universe loader instance
_global_universe_loader: Optional[UniverseLoader] = None


def get_universe_loader() -> UniverseLoader:
    """
    Get the global universe loader instance.
    
    Returns:
        Global UniverseLoader instance
    """
    global _global_universe_loader
    
    if _global_universe_loader is None:
        _global_universe_loader = UniverseLoader()
    
    return _global_universe_loader
