"""
Equity asset class plugin.

Handles equity-specific logic including symbol validation,
metadata retrieval, and data normalization.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_asset import BaseAssetClass
from ..core.types import AssetMetadata, AssetType, PriceData


class EquityAsset(BaseAssetClass):
    """
    Asset class for equities (stocks).
    
    Supports major equity exchanges and handles stock-specific
    features like splits and dividends.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize equity asset class.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - exchanges: List of supported exchanges (default: major US exchanges)
                   - adjust_for_splits: Whether to adjust for stock splits (default: True)
                   - adjust_for_dividends: Whether to adjust for dividends (default: True)
        """
        super().__init__(config)
        
        self.supported_exchanges = self.config.get(
            'exchanges',
            ['NYSE', 'NASDAQ', 'AMEX', 'ARCA']
        )
        
        self.adjust_splits = self.config.get('adjust_for_splits', True)
        self.adjust_dividends = self.config.get('adjust_for_dividends', True)
    
    def get_asset_type(self) -> AssetType:
        """Return equity asset type."""
        return AssetType.EQUITY
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate equity symbol format.
        
        Valid formats:
        - 1-5 uppercase letters (e.g., 'AAPL', 'MSFT')
        - May include dots for class shares (e.g., 'BRK.A')
        - May include hyphens for preferred shares (e.g., 'BAC-PL')
        
        Args:
            symbol: Symbol to validate
        
        Returns:
            True if valid equity symbol format
        """
        if not symbol:
            return False
        
        # Remove dots and hyphens for validation
        clean_symbol = symbol.replace('.', '').replace('-', '')
        
        # Check if alphanumeric and reasonable length
        if not clean_symbol.isalnum():
            return False
        
        if len(clean_symbol) < 1 or len(clean_symbol) > 6:
            return False
        
        # Should be mostly uppercase letters
        if not clean_symbol[0].isalpha():
            return False
        
        return True
    
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for an equity.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            AssetMetadata with equity information
        """
        # In production, this would fetch from a data source
        # For now, return default metadata
        
        return AssetMetadata(
            symbol=symbol,
            name=f"{symbol} Stock",  # Would be replaced with actual company name
            asset_type=AssetType.EQUITY,
            exchange=self._infer_exchange(symbol),
            currency="USD",
            multiplier=1.0,
            tick_size=0.01,  # $0.01 for most stocks
            lot_size=1.0,
            trading_hours={
                'regular': {'open': '09:30', 'close': '16:00'},
                'extended': {'pre_market': '04:00', 'after_hours': '20:00'}
            },
            additional_info={
                'asset_class': 'equity',
                'country': 'US'
            }
        )
    
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize equity data to standard format.
        
        Handles various column naming conventions from different data sources.
        
        Args:
            data: Raw price data
            symbol: Stock symbol
        
        Returns:
            Normalized PriceData
        """
        # Create a copy to avoid modifying original
        df = data.copy()
        
        # Normalize column names (handle various naming conventions)
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower()
            if 'open' in col_lower:
                column_mapping[col] = 'open'
            elif 'high' in col_lower:
                column_mapping[col] = 'high'
            elif 'low' in col_lower:
                column_mapping[col] = 'low'
            elif 'close' in col_lower or 'adj' in col_lower:
                column_mapping[col] = 'close'
            elif 'volume' in col_lower or 'vol' in col_lower:
                column_mapping[col] = 'volume'
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Select only required columns
        df = df[required]
        
        # Ensure index is DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns or 'Date' in df.columns:
                date_col = 'date' if 'date' in df.columns else 'Date'
                df.index = pd.to_datetime(df[date_col])
                df = df.drop(columns=[date_col])
            else:
                df.index = pd.to_datetime(df.index)
        
        # Sort by date
        df = df.sort_index()
        
        # Remove any NaN rows
        df = df.dropna()
        
        # Get metadata
        metadata = self.get_metadata(symbol)
        
        return PriceData(
            symbol=symbol,
            data=df,
            metadata=metadata,
            timeframe='1d'
        )
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges."""
        return self.supported_exchanges
    
    def adjust_for_splits_dividends(
        self,
        price_data: PriceData,
        corporate_actions: Optional[pd.DataFrame] = None
    ) -> PriceData:
        """
        Adjust price data for splits and dividends.
        
        Args:
            price_data: Original price data
            corporate_actions: DataFrame with split/dividend information
        
        Returns:
            Adjusted PriceData
        """
        # This is a simplified implementation
        # In production, would use actual corporate action data
        
        if not (self.adjust_splits or self.adjust_dividends):
            return price_data
        
        # Most data sources (like Yahoo Finance) provide adjusted data already
        # This method is here for custom data sources that provide unadjusted data
        
        return price_data
    
    def _infer_exchange(self, symbol: str) -> str:
        """
        Infer exchange from symbol.
        
        This is a simplified heuristic. In production, would use
        actual exchange data.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Exchange code
        """
        # Simple heuristic based on symbol characteristics
        if len(symbol) <= 3:
            return 'NYSE'
        elif len(symbol) == 4:
            return 'NASDAQ'
        else:
            return 'NYSE'
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Equity asset class for stocks traded on major exchanges. "
            "Supports symbol validation, metadata retrieval, and data normalization "
            "with automatic handling of various data source formats."
        )
