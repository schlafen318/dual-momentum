"""
Base class for asset class plugins.

This module defines the abstract interface that all asset class implementations
must follow. Asset classes handle asset-specific logic like validation,
metadata retrieval, and data normalization.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from .types import AssetMetadata, AssetType, PriceData


class BaseAssetClass(ABC):
    """
    Abstract base class for asset class plugins.
    
    Each asset class (equity, bond, crypto, etc.) should inherit from this class
    and implement the required methods. This enables a plugin architecture where
    new asset classes can be added by simply creating a new file in the
    asset_classes/ directory.
    
    Example:
        >>> class EquityAsset(BaseAssetClass):
        ...     def get_asset_type(self) -> AssetType:
        ...         return AssetType.EQUITY
        ...     
        ...     def validate_symbol(self, symbol: str) -> bool:
        ...         return symbol.isalpha() and symbol.isupper()
        ...     
        ...     # ... implement other required methods
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the asset class.
        
        Args:
            config: Configuration dictionary for the asset class.
                   Can include asset-specific settings like exchanges,
                   market hours, trading rules, etc.
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self._validate_config()
        self._initialized = True
    
    @abstractmethod
    def get_asset_type(self) -> AssetType:
        """
        Return the asset type this class handles.
        
        Returns:
            AssetType enum value
            
        Example:
            >>> asset_class.get_asset_type()
            AssetType.EQUITY
        """
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is valid for this asset class.
        
        Different asset classes have different symbol formats:
        - Equities: Usually uppercase letters (e.g., 'AAPL')
        - Crypto: Often includes separators (e.g., 'BTC/USD')
        - Futures: May include month/year codes (e.g., 'ESZ23')
        
        Args:
            symbol: Asset symbol to validate
            
        Returns:
            True if symbol is valid for this asset class, False otherwise
            
        Example:
            >>> equity_asset.validate_symbol('AAPL')
            True
            >>> equity_asset.validate_symbol('btc/usd')
            False
        """
        pass
    
    @abstractmethod
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for an asset.
        
        This method should return comprehensive information about the asset,
        including exchange, currency, trading specifications, etc.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            AssetMetadata object with asset information
            
        Raises:
            ValueError: If symbol is invalid or metadata cannot be retrieved
            
        Example:
            >>> metadata = asset_class.get_metadata('AAPL')
            >>> print(metadata.name)
            'Apple Inc.'
        """
        pass
    
    @abstractmethod
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize raw data to the standard PriceData format.
        
        Different data sources may provide data in different formats.
        This method standardizes the data to ensure consistent processing
        throughout the system.
        
        Required columns in output: open, high, low, close, volume
        Required index: DatetimeIndex
        
        Args:
            data: Raw price data (may have various column names/formats)
            symbol: Asset symbol
            
        Returns:
            Normalized PriceData object
            
        Raises:
            ValueError: If data cannot be normalized or is missing required fields
            
        Example:
            >>> raw_data = pd.DataFrame(...)  # Data from Yahoo Finance
            >>> price_data = asset_class.normalize_data(raw_data, 'AAPL')
            >>> print(price_data.data.columns)
            Index(['open', 'high', 'low', 'close', 'volume'])
        """
        pass
    
    def get_supported_exchanges(self) -> List[str]:
        """
        Get list of supported exchanges for this asset class.
        
        Returns:
            List of exchange codes/names
            
        Example:
            >>> asset_class.get_supported_exchanges()
            ['NYSE', 'NASDAQ', 'AMEX']
        """
        return []
    
    def calculate_returns(
        self,
        price_data: PriceData,
        method: str = 'simple'
    ) -> pd.Series:
        """
        Calculate returns from price data.
        
        Args:
            price_data: Price data object
            method: Return calculation method ('simple' or 'log')
            
        Returns:
            Series of returns
            
        Raises:
            ValueError: If method is not recognized
            
        Example:
            >>> returns = asset_class.calculate_returns(price_data)
            >>> print(returns.mean())
            0.0012
        """
        if method == 'simple':
            return price_data.data['close'].pct_change()
        elif method == 'log':
            return pd.Series(
                pd.np.log(price_data.data['close'] / price_data.data['close'].shift(1)),
                index=price_data.data.index
            )
        else:
            raise ValueError(f"Unknown return method: {method}. Use 'simple' or 'log'")
    
    def calculate_volatility(
        self,
        price_data: PriceData,
        window: int = 20,
        annualization_factor: int = 252
    ) -> pd.Series:
        """
        Calculate rolling volatility.
        
        Args:
            price_data: Price data object
            window: Rolling window size
            annualization_factor: Factor for annualization (252 for daily, 12 for monthly)
            
        Returns:
            Series of annualized volatility
            
        Example:
            >>> vol = asset_class.calculate_volatility(price_data, window=30)
            >>> print(vol.iloc[-1])
            0.25
        """
        returns = self.calculate_returns(price_data)
        return returns.rolling(window=window).std() * (annualization_factor ** 0.5)
    
    def adjust_for_splits_dividends(
        self,
        price_data: PriceData,
        corporate_actions: Optional[pd.DataFrame] = None
    ) -> PriceData:
        """
        Adjust price data for splits and dividends.
        
        Note: This is a default implementation. Override for asset-specific logic.
        
        Args:
            price_data: Original price data
            corporate_actions: DataFrame with corporate action information
            
        Returns:
            Adjusted PriceData object
        """
        # Default implementation returns unadjusted data
        # Override this method for assets that need adjustment (e.g., equities)
        return price_data
    
    def get_trading_calendar(self) -> Optional[pd.DatetimeIndex]:
        """
        Get trading calendar for this asset class.
        
        Returns:
            DatetimeIndex of valid trading days, or None if not applicable
            
        Example:
            >>> calendar = asset_class.get_trading_calendar()
            >>> print(calendar[-5:])
            DatetimeIndex(['2023-10-13', '2023-10-16', '2023-10-17', ...])
        """
        return None
    
    def is_trading_day(self, date: pd.Timestamp) -> bool:
        """
        Check if a given date is a valid trading day.
        
        Args:
            date: Date to check
            
        Returns:
            True if trading day, False otherwise
        """
        calendar = self.get_trading_calendar()
        if calendar is None:
            # If no calendar specified, assume all weekdays are trading days
            return date.weekday() < 5
        return date in calendar
    
    def get_minimum_trade_size(self, symbol: str) -> float:
        """
        Get minimum trade size for an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Minimum trade size (lot size)
            
        Example:
            >>> min_size = asset_class.get_minimum_trade_size('AAPL')
            >>> print(min_size)
            1.0
        """
        metadata = self.get_metadata(symbol)
        return metadata.lot_size
    
    def get_tick_size(self, symbol: str) -> float:
        """
        Get minimum price increment for an asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Tick size
            
        Example:
            >>> tick = asset_class.get_tick_size('AAPL')
            >>> print(tick)
            0.01
        """
        metadata = self.get_metadata(symbol)
        return metadata.tick_size
    
    def validate_price(self, symbol: str, price: float) -> bool:
        """
        Validate if a price is valid (respects tick size).
        
        Args:
            symbol: Asset symbol
            price: Price to validate
            
        Returns:
            True if price is valid, False otherwise
        """
        tick_size = self.get_tick_size(symbol)
        if tick_size == 0:
            return True
        
        # Check if price is a multiple of tick size (with small tolerance for floating point)
        remainder = abs(price % tick_size)
        return remainder < 1e-8 or abs(remainder - tick_size) < 1e-8
    
    def round_price(self, symbol: str, price: float) -> float:
        """
        Round price to valid tick size.
        
        Args:
            symbol: Asset symbol
            price: Price to round
            
        Returns:
            Rounded price
            
        Example:
            >>> rounded = asset_class.round_price('AAPL', 150.234)
            >>> print(rounded)
            150.23
        """
        tick_size = self.get_tick_size(symbol)
        if tick_size == 0:
            return price
        return round(price / tick_size) * tick_size
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Override this method to add custom validation logic.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Default implementation does nothing
        # Override in subclasses for custom validation
        pass
    
    @classmethod
    def get_name(cls) -> str:
        """
        Return the plugin name.
        
        Returns:
            Class name as string
            
        Example:
            >>> EquityAsset.get_name()
            'EquityAsset'
        """
        return cls.__name__
    
    @classmethod
    def get_version(cls) -> str:
        """
        Return the plugin version.
        
        Override this method to provide version information.
        
        Returns:
            Version string
        """
        return "1.0.0"
    
    def __repr__(self) -> str:
        """String representation of the asset class."""
        return f"{self.get_name()}(asset_type={self.get_asset_type().value})"
