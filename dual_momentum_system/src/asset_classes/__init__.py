"""
Asset class plugins for the dual momentum system.

This package contains implementations of various asset classes that can be
used with the momentum trading framework. Each asset class handles the specific
characteristics and requirements of its respective market.

Available asset classes:
- EquityAsset: Stocks and equity securities
- CryptoAsset: Cryptocurrencies
- CommodityAsset: Physical and financial commodities
- BondAsset: Fixed income securities
- FXAsset: Foreign exchange (forex) currency pairs
"""

from .equity import EquityAsset
from .crypto import CryptoAsset
from .commodity import CommodityAsset
from .bond import BondAsset
from .fx import FXAsset

__all__ = [
    'EquityAsset',
    'CryptoAsset',
    'CommodityAsset',
    'BondAsset',
    'FXAsset',
]
