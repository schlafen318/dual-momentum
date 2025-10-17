"""
Cryptocurrency asset class plugin.

Handles crypto-specific logic including symbol validation,
exchange handling, and 24/7 trading considerations.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_asset import BaseAssetClass
from ..core.types import AssetMetadata, AssetType, PriceData


class CryptoAsset(BaseAssetClass):
    """
    Asset class for cryptocurrencies.
    
    Supports various cryptocurrency formats and handles
    crypto-specific features like 24/7 trading.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize crypto asset class.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - exchanges: List of supported exchanges
                   - base_currencies: List of base currencies (default: ['USD', 'USDT'])
        """
        super().__init__(config)
        
        self.supported_exchanges = self.config.get(
            'exchanges',
            ['Binance', 'Coinbase', 'Kraken', 'Bitfinex']
        )
        
        self.base_currencies = self.config.get(
            'base_currencies',
            ['USD', 'USDT', 'BTC', 'ETH']
        )
    
    def get_asset_type(self) -> AssetType:
        """Return crypto asset type."""
        return AssetType.CRYPTO
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate crypto symbol format.
        
        Valid formats:
        - 'BTC/USD' (base/quote pair)
        - 'BTC-USD' (alternative separator)
        - 'BTCUSD' (no separator, must end with known quote currency)
        
        Args:
            symbol: Symbol to validate
        
        Returns:
            True if valid crypto symbol format
        """
        if not symbol:
            return False
        
        # Check for pair format with separators
        if '/' in symbol or '-' in symbol:
            parts = symbol.replace('-', '/').split('/')
            if len(parts) != 2:
                return False
            
            base, quote = parts
            
            # Base should be 2-6 uppercase letters/numbers
            if not (2 <= len(base) <= 6 and base.isalnum()):
                return False
            
            # Quote should be in known base currencies
            if quote not in self.base_currencies:
                return False
            
            return True
        
        # Check for format without separator
        # Must end with a known base currency
        for quote in self.base_currencies:
            if symbol.endswith(quote) and len(symbol) > len(quote):
                base = symbol[:-len(quote)]
                if 2 <= len(base) <= 6 and base.isalnum():
                    return True
        
        return False
    
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for a cryptocurrency.
        
        Args:
            symbol: Crypto symbol
        
        Returns:
            AssetMetadata with crypto information
        """
        # Parse symbol to get base and quote
        if '/' in symbol:
            base, quote = symbol.split('/')
        elif '-' in symbol:
            base, quote = symbol.split('-')
        else:
            # Find quote currency
            quote = None
            for curr in self.base_currencies:
                if symbol.endswith(curr):
                    quote = curr
                    base = symbol[:-len(curr)]
                    break
            
            if quote is None:
                # Default to USD if can't parse
                base = symbol
                quote = 'USD'
        
        return AssetMetadata(
            symbol=symbol,
            name=f"{base} Cryptocurrency",
            asset_type=AssetType.CRYPTO,
            exchange=self._infer_exchange(symbol),
            currency=quote,
            multiplier=1.0,
            tick_size=0.01,  # Most cryptos quote to 2 decimals minimum
            lot_size=0.001,  # Can trade fractional amounts
            trading_hours={
                '24/7': True,
                'note': 'Crypto markets trade continuously'
            },
            additional_info={
                'asset_class': 'cryptocurrency',
                'base_currency': base,
                'quote_currency': quote,
                'decimal_places': 8  # Most cryptos support 8 decimal places
            }
        )
    
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize crypto data to standard format.
        
        Handles various exchange data formats.
        
        Args:
            data: Raw price data
            symbol: Crypto symbol
        
        Returns:
            Normalized PriceData
        """
        # Create a copy
        df = data.copy()
        
        # Normalize column names
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower()
            if 'open' in col_lower:
                column_mapping[col] = 'open'
            elif 'high' in col_lower:
                column_mapping[col] = 'high'
            elif 'low' in col_lower:
                column_mapping[col] = 'low'
            elif 'close' in col_lower:
                column_mapping[col] = 'close'
            elif 'volume' in col_lower or 'vol' in col_lower:
                column_mapping[col] = 'volume'
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Select only required columns
        df = df[required]
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns or 'date' in df.columns:
                date_col = 'timestamp' if 'timestamp' in df.columns else 'date'
                df.index = pd.to_datetime(df[date_col])
                df = df.drop(columns=[date_col])
            else:
                df.index = pd.to_datetime(df.index)
        
        # Sort and clean
        df = df.sort_index()
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
    
    def get_trading_calendar(self) -> Optional[pd.DatetimeIndex]:
        """
        Crypto markets trade 24/7, so no specific calendar.
        
        Returns:
            None (markets always open)
        """
        return None
    
    def is_trading_day(self, date: pd.Timestamp) -> bool:
        """
        Check if a date is a trading day.
        
        For crypto, every day is a trading day.
        
        Args:
            date: Date to check
        
        Returns:
            Always True for crypto
        """
        return True
    
    def _infer_exchange(self, symbol: str) -> str:
        """
        Infer exchange from symbol characteristics.
        
        Args:
            symbol: Crypto symbol
        
        Returns:
            Exchange name (default 'Binance')
        """
        # This is simplified. In production, would track which exchange
        # each symbol comes from
        return 'Binance'
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Cryptocurrency asset class supporting various crypto exchanges. "
            "Handles crypto-specific features like 24/7 trading, fractional shares, "
            "and various symbol formats (BTC/USD, BTC-USD, BTCUSD)."
        )
