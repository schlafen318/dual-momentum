"""
Plugin Manager for auto-discovery and registration of plugins.

This module provides a centralized system for discovering, registering,
and managing plugins (asset classes, data sources, strategies, risk managers).

The plugin system enables extensibility without modifying core code.
Simply drop a new plugin file in the appropriate directory and it will
be automatically discovered and registered.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union

from loguru import logger

from .base_asset import BaseAssetClass
from .base_data_source import BaseDataSource
from .base_risk import BaseRiskManager
from .base_strategy import BaseStrategy

# Type variables for generic plugin handling
T = TypeVar('T')


class PluginRegistry:
    """
    Registry for managing discovered plugins.
    
    Maintains separate registries for each plugin type.
    """
    
    def __init__(self):
        """Initialize empty registries."""
        self.asset_classes: Dict[str, Type[BaseAssetClass]] = {}
        self.data_sources: Dict[str, Type[BaseDataSource]] = {}
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.risk_managers: Dict[str, Type[BaseRiskManager]] = {}
        
        # Track registered plugin files to avoid duplicates
        self._registered_files: Set[str] = set()
    
    def register_asset_class(self, name: str, cls: Type[BaseAssetClass]) -> None:
        """Register an asset class plugin."""
        if name in self.asset_classes:
            logger.warning(f"Asset class '{name}' already registered, overwriting")
        self.asset_classes[name] = cls
        logger.info(f"Registered asset class: {name}")
    
    def register_data_source(self, name: str, cls: Type[BaseDataSource]) -> None:
        """Register a data source plugin."""
        if name in self.data_sources:
            logger.warning(f"Data source '{name}' already registered, overwriting")
        self.data_sources[name] = cls
        logger.info(f"Registered data source: {name}")
    
    def register_strategy(self, name: str, cls: Type[BaseStrategy]) -> None:
        """Register a strategy plugin."""
        if name in self.strategies:
            logger.warning(f"Strategy '{name}' already registered, overwriting")
        self.strategies[name] = cls
        logger.info(f"Registered strategy: {name}")
    
    def register_risk_manager(self, name: str, cls: Type[BaseRiskManager]) -> None:
        """Register a risk manager plugin."""
        if name in self.risk_managers:
            logger.warning(f"Risk manager '{name}' already registered, overwriting")
        self.risk_managers[name] = cls
        logger.info(f"Registered risk manager: {name}")
    
    def get_asset_class(self, name: str) -> Optional[Type[BaseAssetClass]]:
        """Get an asset class by name."""
        return self.asset_classes.get(name)
    
    def get_data_source(self, name: str) -> Optional[Type[BaseDataSource]]:
        """Get a data source by name."""
        return self.data_sources.get(name)
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """Get a strategy by name."""
        return self.strategies.get(name)
    
    def get_risk_manager(self, name: str) -> Optional[Type[BaseRiskManager]]:
        """Get a risk manager by name."""
        return self.risk_managers.get(name)
    
    def list_asset_classes(self) -> List[str]:
        """List all registered asset class names."""
        return list(self.asset_classes.keys())
    
    def list_data_sources(self) -> List[str]:
        """List all registered data source names."""
        return list(self.data_sources.keys())
    
    def list_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return list(self.strategies.keys())
    
    def list_risk_managers(self) -> List[str]:
        """List all registered risk manager names."""
        return list(self.risk_managers.keys())
    
    def get_all_plugins(self) -> Dict[str, Dict[str, Type]]:
        """Get all registered plugins organized by type."""
        return {
            'asset_classes': self.asset_classes,
            'data_sources': self.data_sources,
            'strategies': self.strategies,
            'risk_managers': self.risk_managers,
        }
    
    def clear(self) -> None:
        """Clear all registered plugins."""
        self.asset_classes.clear()
        self.data_sources.clear()
        self.strategies.clear()
        self.risk_managers.clear()
        self._registered_files.clear()
        logger.info("Cleared all plugin registrations")


class PluginManager:
    """
    Plugin manager for auto-discovery and registration.
    
    Discovers plugins by scanning specified directories and automatically
    registering any classes that inherit from the base plugin classes.
    
    Example:
        >>> manager = PluginManager()
        >>> manager.discover_all()
        >>> 
        >>> # List available plugins
        >>> print(manager.list_strategies())
        ['DualMomentumStrategy', 'AbsoluteMomentumStrategy', ...]
        >>> 
        >>> # Create instance of a plugin
        >>> strategy_class = manager.get_strategy('DualMomentumStrategy')
        >>> strategy = strategy_class(config={'lookback_period': 252})
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the plugin manager.
        
        Args:
            base_path: Base path for the src directory. If None, auto-detects.
        """
        self.registry = PluginRegistry()
        
        if base_path is None:
            # Auto-detect base path (assumes we're in src/core/)
            base_path = Path(__file__).parent.parent
        
        self.base_path = Path(base_path)
        self.asset_classes_path = self.base_path / "asset_classes"
        self.data_sources_path = self.base_path / "data_sources"
        self.strategies_path = self.base_path / "strategies"
        self.risk_managers_path = self.base_path / "backtesting"  # Risk managers in backtesting
        
        logger.info(f"Initialized PluginManager with base path: {self.base_path}")
    
    def discover_all(self) -> None:
        """
        Discover and register all plugins.
        
        Scans all plugin directories and registers found plugins.
        """
        logger.info("Starting plugin discovery...")
        
        self.discover_asset_classes()
        self.discover_data_sources()
        self.discover_strategies()
        self.discover_risk_managers()
        
        logger.info("Plugin discovery complete")
        self._log_summary()
    
    def discover_asset_classes(self) -> None:
        """Discover and register asset class plugins."""
        logger.info(f"Discovering asset classes in: {self.asset_classes_path}")
        
        if not self.asset_classes_path.exists():
            logger.warning(f"Asset classes directory not found: {self.asset_classes_path}")
            return
        
        plugins = self._discover_plugins_in_directory(
            self.asset_classes_path,
            BaseAssetClass
        )
        
        for name, cls in plugins.items():
            self.registry.register_asset_class(name, cls)
    
    def discover_data_sources(self) -> None:
        """Discover and register data source plugins."""
        logger.info(f"Discovering data sources in: {self.data_sources_path}")
        
        if not self.data_sources_path.exists():
            logger.warning(f"Data sources directory not found: {self.data_sources_path}")
            return
        
        plugins = self._discover_plugins_in_directory(
            self.data_sources_path,
            BaseDataSource
        )
        
        for name, cls in plugins.items():
            self.registry.register_data_source(name, cls)
    
    def discover_strategies(self) -> None:
        """Discover and register strategy plugins."""
        logger.info(f"Discovering strategies in: {self.strategies_path}")
        
        if not self.strategies_path.exists():
            logger.warning(f"Strategies directory not found: {self.strategies_path}")
            return
        
        plugins = self._discover_plugins_in_directory(
            self.strategies_path,
            BaseStrategy
        )
        
        for name, cls in plugins.items():
            self.registry.register_strategy(name, cls)
    
    def discover_risk_managers(self) -> None:
        """Discover and register risk manager plugins."""
        logger.info(f"Discovering risk managers in: {self.risk_managers_path}")
        
        if not self.risk_managers_path.exists():
            logger.warning(f"Risk managers directory not found: {self.risk_managers_path}")
            return
        
        plugins = self._discover_plugins_in_directory(
            self.risk_managers_path,
            BaseRiskManager
        )
        
        for name, cls in plugins.items():
            self.registry.register_risk_manager(name, cls)
    
    def _discover_plugins_in_directory(
        self,
        directory: Path,
        base_class: Type[T]
    ) -> Dict[str, Type[T]]:
        """
        Discover plugins in a specific directory.
        
        Args:
            directory: Directory to scan
            base_class: Base class that plugins must inherit from
        
        Returns:
            Dictionary mapping plugin names to classes
        """
        plugins = {}
        
        # Get all Python files in directory
        python_files = list(directory.glob("*.py"))
        
        for file_path in python_files:
            # Skip __init__.py and private files
            if file_path.name.startswith("_"):
                continue
            
            # Skip if already registered
            if str(file_path) in self.registry._registered_files:
                continue
            
            try:
                # Import module
                module = self._import_module_from_file(file_path, directory)
                
                if module is None:
                    continue
                
                # Find all classes in module that inherit from base_class
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip if it's the base class itself
                    if obj is base_class:
                        continue
                    
                    # Check if it inherits from base_class and is not abstract
                    if issubclass(obj, base_class) and not inspect.isabstract(obj):
                        plugin_name = obj.get_name() if hasattr(obj, 'get_name') else name
                        plugins[plugin_name] = obj
                        logger.debug(f"Found plugin: {plugin_name} in {file_path.name}")
                
                # Mark file as registered
                self.registry._registered_files.add(str(file_path))
                
            except Exception as e:
                logger.error(f"Error loading plugin from {file_path}: {e}")
                continue
        
        return plugins
    
    def _import_module_from_file(
        self,
        file_path: Path,
        base_dir: Path
    ) -> Optional[Any]:
        """
        Import a module from a file path.
        
        Args:
            file_path: Path to Python file
            base_dir: Base directory for relative imports
        
        Returns:
            Imported module or None
        """
        try:
            # Calculate module name relative to base_path
            relative_path = file_path.relative_to(self.base_path)
            module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
            module_name = ".".join(module_parts)
            
            # Ensure base path is in sys.path
            base_path_str = str(self.base_path.parent)
            if base_path_str not in sys.path:
                sys.path.insert(0, base_path_str)
            
            # Import with full module path
            full_module_name = f"src.{module_name}"
            
            # Try to import
            if full_module_name in sys.modules:
                # Reload if already imported
                module = importlib.reload(sys.modules[full_module_name])
            else:
                module = importlib.import_module(full_module_name)
            
            return module
            
        except Exception as e:
            logger.error(f"Failed to import module from {file_path}: {e}")
            return None
    
    def register_plugin(
        self,
        plugin_class: Type,
        plugin_type: str,
        name: Optional[str] = None
    ) -> None:
        """
        Manually register a plugin.
        
        Args:
            plugin_class: Plugin class to register
            plugin_type: Type of plugin ('asset_class', 'data_source', 'strategy', 'risk_manager')
            name: Optional custom name (uses class name if None)
        
        Example:
            >>> manager.register_plugin(MyCustomStrategy, 'strategy')
        """
        if name is None:
            name = plugin_class.get_name() if hasattr(plugin_class, 'get_name') else plugin_class.__name__
        
        if plugin_type == 'asset_class':
            self.registry.register_asset_class(name, plugin_class)
        elif plugin_type == 'data_source':
            self.registry.register_data_source(name, plugin_class)
        elif plugin_type == 'strategy':
            self.registry.register_strategy(name, plugin_class)
        elif plugin_type == 'risk_manager':
            self.registry.register_risk_manager(name, plugin_class)
        else:
            raise ValueError(f"Unknown plugin type: {plugin_type}")
    
    def get_asset_class(self, name: str) -> Optional[Type[BaseAssetClass]]:
        """Get asset class by name."""
        return self.registry.get_asset_class(name)
    
    def get_data_source(self, name: str) -> Optional[Type[BaseDataSource]]:
        """Get data source by name."""
        return self.registry.get_data_source(name)
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """Get strategy by name."""
        return self.registry.get_strategy(name)
    
    def get_risk_manager(self, name: str) -> Optional[Type[BaseRiskManager]]:
        """Get risk manager by name."""
        return self.registry.get_risk_manager(name)
    
    def list_asset_classes(self) -> List[str]:
        """List all available asset classes."""
        return self.registry.list_asset_classes()
    
    def list_data_sources(self) -> List[str]:
        """List all available data sources."""
        return self.registry.list_data_sources()
    
    def list_strategies(self) -> List[str]:
        """List all available strategies."""
        return self.registry.list_strategies()
    
    def list_risk_managers(self) -> List[str]:
        """List all available risk managers."""
        return self.registry.list_risk_managers()
    
    def get_plugin_info(
        self,
        plugin_type: str,
        name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific plugin.
        
        Args:
            plugin_type: Type of plugin
            name: Plugin name
        
        Returns:
            Dictionary with plugin information
        """
        plugin_class = None
        
        if plugin_type == 'asset_class':
            plugin_class = self.registry.get_asset_class(name)
        elif plugin_type == 'data_source':
            plugin_class = self.registry.get_data_source(name)
        elif plugin_type == 'strategy':
            plugin_class = self.registry.get_strategy(name)
        elif plugin_type == 'risk_manager':
            plugin_class = self.registry.get_risk_manager(name)
        
        if plugin_class is None:
            return None
        
        info = {
            'name': name,
            'type': plugin_type,
            'class_name': plugin_class.__name__,
            'version': plugin_class.get_version() if hasattr(plugin_class, 'get_version') else 'unknown',
            'description': plugin_class.__doc__ or 'No description available',
        }
        
        # Add type-specific info
        if hasattr(plugin_class, 'get_description'):
            info['full_description'] = plugin_class.get_description()
        
        return info
    
    def _log_summary(self) -> None:
        """Log summary of discovered plugins."""
        logger.info("=" * 60)
        logger.info("PLUGIN DISCOVERY SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Asset Classes:  {len(self.registry.asset_classes)}")
        logger.info(f"Data Sources:   {len(self.registry.data_sources)}")
        logger.info(f"Strategies:     {len(self.registry.strategies)}")
        logger.info(f"Risk Managers:  {len(self.registry.risk_managers)}")
        logger.info("=" * 60)
        
        if self.registry.asset_classes:
            logger.info(f"Asset Classes: {', '.join(self.registry.list_asset_classes())}")
        if self.registry.data_sources:
            logger.info(f"Data Sources: {', '.join(self.registry.list_data_sources())}")
        if self.registry.strategies:
            logger.info(f"Strategies: {', '.join(self.registry.list_strategies())}")
        if self.registry.risk_managers:
            logger.info(f"Risk Managers: {', '.join(self.registry.list_risk_managers())}")


# Global plugin manager instance
_global_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    
    Creates and initializes the plugin manager on first call.
    
    Returns:
        Global PluginManager instance
    
    Example:
        >>> manager = get_plugin_manager()
        >>> strategies = manager.list_strategies()
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = PluginManager()
        _global_manager.discover_all()
    
    return _global_manager


def reset_plugin_manager() -> None:
    """Reset the global plugin manager (useful for testing)."""
    global _global_manager
    _global_manager = None
