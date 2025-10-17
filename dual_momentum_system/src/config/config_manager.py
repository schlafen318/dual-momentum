"""
Configuration management system.

Handles loading, validation, and management of configuration files
for strategies, data sources, and system settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
import toml
from loguru import logger


class ConfigManager:
    """
    Configuration manager for the backtesting framework.
    
    Supports YAML and TOML configuration files with environment
    variable substitution and validation.
    
    Example:
        >>> config_mgr = ConfigManager()
        >>> strategy_config = config_mgr.load_config('strategies/dual_momentum.yaml')
        >>> print(strategy_config['lookback_period'])
        252
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing config files. If None, uses
                       default config directory relative to project root.
        """
        if config_dir is None:
            # Auto-detect config directory
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Initialized ConfigManager with directory: {self.config_dir}")
    
    def load_config(
        self,
        config_path: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Supports both absolute paths and paths relative to config_dir.
        Automatically detects file format (YAML or TOML) from extension.
        
        Args:
            config_path: Path to config file (relative or absolute)
            use_cache: Whether to use cached config
        
        Returns:
            Configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is not supported
        """
        # Check cache first
        if use_cache and config_path in self._cache:
            logger.debug(f"Using cached config: {config_path}")
            return self._cache[config_path].copy()
        
        # Resolve path
        path = Path(config_path)
        if not path.is_absolute():
            path = self.config_dir / path
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        # Load based on extension
        suffix = path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            config = self._load_yaml(path)
        elif suffix in ['.toml']:
            config = self._load_toml(path)
        else:
            raise ValueError(f"Unsupported config format: {suffix}")
        
        # Substitute environment variables
        config = self._substitute_env_vars(config)
        
        # Cache the config
        self._cache[config_path] = config.copy()
        
        logger.info(f"Loaded config: {config_path}")
        return config
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_toml(self, path: Path) -> Dict[str, Any]:
        """Load TOML configuration file."""
        with open(path, 'r') as f:
            return toml.load(f)
    
    def _substitute_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute environment variables in config values.
        
        Supports ${VAR_NAME} syntax in string values.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            Config with substituted values
        """
        def substitute_value(value: Any) -> Any:
            if isinstance(value, str):
                # Replace ${VAR_NAME} with environment variable
                if '${' in value and '}' in value:
                    import re
                    pattern = r'\$\{([^}]+)\}'
                    
                    def replacer(match):
                        var_name = match.group(1)
                        return os.environ.get(var_name, match.group(0))
                    
                    return re.sub(pattern, replacer, value)
                return value
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            else:
                return value
        
        return substitute_value(config)
    
    def save_config(
        self,
        config: Dict[str, Any],
        config_path: str,
        format: str = 'yaml'
    ) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            config_path: Path to save config (relative or absolute)
            format: File format ('yaml' or 'toml')
        
        Raises:
            ValueError: If format is not supported
        """
        # Resolve path
        path = Path(config_path)
        if not path.is_absolute():
            path = self.config_dir / path
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save based on format
        if format == 'yaml':
            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        elif format == 'toml':
            with open(path, 'w') as f:
                toml.dump(config, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved config: {path}")
        
        # Update cache
        self._cache[config_path] = config.copy()
    
    def get_default_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get default configuration for a strategy.
        
        Args:
            strategy_name: Name of the strategy
        
        Returns:
            Default configuration dictionary
        """
        defaults = {
            'DualMomentumStrategy': {
                'lookback_period': 252,
                'rebalance_frequency': 'monthly',
                'position_count': 1,
                'absolute_threshold': 0.0,
                'use_volatility_adjustment': False,
                'safe_asset': 'SHY',  # Short-term Treasury ETF
                'signal_threshold': 0.0,
            },
        }
        
        return defaults.get(strategy_name, {})
    
    def get_default_risk_config(self, risk_manager_name: str) -> Dict[str, Any]:
        """
        Get default configuration for a risk manager.
        
        Args:
            risk_manager_name: Name of the risk manager
        
        Returns:
            Default configuration dictionary
        """
        defaults = {
            'BasicRiskManager': {
                'max_position_size': 0.2,
                'max_leverage': 1.0,
                'position_limit': None,
                'max_drawdown': 0.5,
                'emergency_stop_threshold': 0.4,
                'equal_weight': True,
                'target_volatility': None,
            },
        }
        
        return defaults.get(risk_manager_name, {})
    
    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._cache.clear()
        logger.info("Cleared config cache")
    
    def list_configs(self, subdirectory: Optional[str] = None) -> list[str]:
        """
        List available configuration files.
        
        Args:
            subdirectory: Optional subdirectory to search in
        
        Returns:
            List of config file paths
        """
        search_dir = self.config_dir
        if subdirectory:
            search_dir = search_dir / subdirectory
        
        if not search_dir.exists():
            return []
        
        configs = []
        for ext in ['.yaml', '.yml', '.toml']:
            configs.extend([
                str(p.relative_to(self.config_dir))
                for p in search_dir.rglob(f'*{ext}')
            ])
        
        return sorted(configs)


# Global config manager instance
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global config manager instance.
    
    Returns:
        Global ConfigManager instance
    """
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    
    return _global_config_manager
