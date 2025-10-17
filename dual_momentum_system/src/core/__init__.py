"""
Core module for the dual momentum backtesting framework.

This module exports all base classes, types, and the plugin manager.
"""

from .base_asset import BaseAssetClass
from .base_data_source import BaseDataSource
from .base_risk import BaseRiskManager
from .base_strategy import BaseStrategy
from .plugin_manager import PluginManager, get_plugin_manager, reset_plugin_manager
from .types import (
    AssetMetadata,
    AssetType,
    BacktestResult,
    MomentumType,
    PortfolioState,
    Position,
    PriceData,
    Signal,
    SignalType,
    Trade,
)

__all__ = [
    # Base classes
    'BaseAssetClass',
    'BaseDataSource',
    'BaseRiskManager',
    'BaseStrategy',
    
    # Plugin manager
    'PluginManager',
    'get_plugin_manager',
    'reset_plugin_manager',
    
    # Types and enums
    'AssetMetadata',
    'AssetType',
    'BacktestResult',
    'MomentumType',
    'PortfolioState',
    'Position',
    'PriceData',
    'Signal',
    'SignalType',
    'Trade',
]
