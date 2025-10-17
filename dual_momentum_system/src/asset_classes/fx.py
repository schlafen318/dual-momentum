"""
Foreign Exchange (FX) asset class plugin.

Handles forex-specific logic including currency pairs,
cross rates, and 24/5 trading considerations.
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..core.base_asset import BaseAssetClass
from ..core.types import AssetMetadata, AssetType, PriceData


class FXAsset(BaseAssetClass):
    """
    Asset class for foreign exchange (forex/FX).
    
    Supports major, minor, and exotic currency pairs.
    Handles FX-specific features like:
    - Pip calculations
    - Bid/ask spreads
    - 24/5 trading (24 hours, 5 days)
    - Cross currency rates
    - Major trading sessions (Tokyo, London, New York)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FX asset class.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - brokers: List of supported FX brokers
                   - base_currencies: Major currencies to support
                   - include_exotic: Whether to support exotic pairs
        """
        super().__init__(config)
        
        self.supported_brokers = self.config.get(
            'brokers',
            ['OANDA', 'Interactive Brokers', 'FXCM', 'Saxo Bank']
        )
        
        # Major currencies (G10)
        self.major_currencies = self.config.get(
            'base_currencies',
            ['USD', 'EUR', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']
        )
        
        # Additional currencies for exotic pairs
        self.minor_currencies = [
            'MXN', 'ZAR', 'SGD', 'HKD', 'TRY', 'BRL', 'INR', 'CNY', 'KRW', 'PLN'
        ]
        
        self.include_exotic = self.config.get('include_exotic', True)
        
        # Known currency pair metadata
        self.major_pairs = {
            'EUR/USD': {'name': 'Euro / US Dollar', 'pip_value': 0.0001, 'spread': 0.5},
            'GBP/USD': {'name': 'British Pound / US Dollar', 'pip_value': 0.0001, 'spread': 0.7},
            'USD/JPY': {'name': 'US Dollar / Japanese Yen', 'pip_value': 0.01, 'spread': 0.5},
            'USD/CHF': {'name': 'US Dollar / Swiss Franc', 'pip_value': 0.0001, 'spread': 0.8},
            'AUD/USD': {'name': 'Australian Dollar / US Dollar', 'pip_value': 0.0001, 'spread': 0.6},
            'USD/CAD': {'name': 'US Dollar / Canadian Dollar', 'pip_value': 0.0001, 'spread': 0.7},
            'NZD/USD': {'name': 'New Zealand Dollar / US Dollar', 'pip_value': 0.0001, 'spread': 0.9},
        }
        
        # Trading sessions (UTC times)
        self.trading_sessions = {
            'tokyo': {'open': '00:00', 'close': '09:00'},
            'london': {'open': '08:00', 'close': '17:00'},
            'new_york': {'open': '13:00', 'close': '22:00'},
            'sydney': {'open': '22:00', 'close': '07:00'}
        }
    
    def get_asset_type(self) -> AssetType:
        """Return FX asset type."""
        return AssetType.FX
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate FX symbol format.
        
        Valid formats:
        - 'EUR/USD' (base/quote with slash)
        - 'EURUSD' (no separator)
        - 'EUR-USD' (hyphen separator)
        - Must be 6-7 characters total (3 for base, 3 for quote)
        
        Args:
            symbol: Symbol to validate
        
        Returns:
            True if valid FX symbol format
        """
        if not symbol:
            return False
        
        # Remove separators
        clean_symbol = symbol.replace('/', '').replace('-', '').replace('_', '')
        
        # FX pairs should be 6 characters (3 + 3)
        if len(clean_symbol) != 6:
            return False
        
        # Should be all alphabetic
        if not clean_symbol.isalpha():
            return False
        
        # Extract base and quote
        base = clean_symbol[:3].upper()
        quote = clean_symbol[3:].upper()
        
        # Check if currencies are valid
        all_currencies = self.major_currencies + (self.minor_currencies if self.include_exotic else [])
        
        if base not in all_currencies or quote not in all_currencies:
            return False
        
        # Base and quote should be different
        if base == quote:
            return False
        
        return True
    
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for an FX pair.
        
        Args:
            symbol: FX pair symbol
        
        Returns:
            AssetMetadata with FX pair information
        """
        # Normalize symbol format
        normalized_symbol = self._normalize_symbol(symbol)
        
        # Parse base and quote currencies
        base, quote = self._parse_pair(normalized_symbol)
        
        # Check if it's a major pair
        if normalized_symbol in self.major_pairs:
            info = self.major_pairs[normalized_symbol]
            name = info['name']
            pip_value = info['pip_value']
            typical_spread = info['spread']
        else:
            name = f"{base} / {quote}"
            # JPY pairs have different pip value
            pip_value = 0.01 if quote == 'JPY' else 0.0001
            # Minor and exotic pairs have wider spreads
            typical_spread = 2.0 if base in self.minor_currencies or quote in self.minor_currencies else 1.5
        
        # Determine pair category
        pair_category = self._classify_pair(base, quote)
        
        # Standard lot size is 100,000 units
        lot_size = 100000.0
        
        return AssetMetadata(
            symbol=normalized_symbol,
            name=name,
            asset_type=AssetType.FX,
            exchange='OTC',  # FX is over-the-counter
            currency=quote,  # Quote currency
            multiplier=1.0,
            tick_size=pip_value,
            lot_size=lot_size,
            trading_hours={
                '24/5': True,
                'note': 'FX markets trade 24 hours a day, 5 days a week',
                'sessions': self.trading_sessions,
                'closed': 'Friday 22:00 UTC to Sunday 22:00 UTC'
            },
            additional_info={
                'asset_class': 'fx',
                'base_currency': base,
                'quote_currency': quote,
                'pair_category': pair_category,
                'pip_value': pip_value,
                'typical_spread_pips': typical_spread,
                'standard_lot': lot_size,
                'mini_lot': lot_size / 10,
                'micro_lot': lot_size / 100,
                'leverage_available': True,
                'typical_leverage': '50:1 to 500:1'
            }
        )
    
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize FX data to standard format.
        
        Handles FX-specific data including bid/ask prices.
        
        Args:
            data: Raw price data
            symbol: FX pair symbol
        
        Returns:
            Normalized PriceData
        """
        # Create a copy
        df = data.copy()
        
        # Normalize column names
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower()
            if 'open' in col_lower and 'bid' not in col_lower and 'ask' not in col_lower:
                column_mapping[col] = 'open'
            elif 'high' in col_lower and 'bid' not in col_lower and 'ask' not in col_lower:
                column_mapping[col] = 'high'
            elif 'low' in col_lower and 'bid' not in col_lower and 'ask' not in col_lower:
                column_mapping[col] = 'low'
            elif 'close' in col_lower and 'bid' not in col_lower and 'ask' not in col_lower:
                column_mapping[col] = 'close'
            elif 'volume' in col_lower or 'vol' in col_lower:
                column_mapping[col] = 'volume'
            elif 'bid' in col_lower and 'close' not in col_lower:
                column_mapping[col] = 'bid'
            elif 'ask' in col_lower and 'close' not in col_lower:
                column_mapping[col] = 'ask'
            elif 'spread' in col_lower:
                column_mapping[col] = 'spread'
        
        df = df.rename(columns=column_mapping)
        
        # For FX, volume might not be available (OTC market)
        # Calculate mid price from bid/ask if available
        if 'bid' in df.columns and 'ask' in df.columns and 'close' not in df.columns:
            df['close'] = (df['bid'] + df['ask']) / 2
            if 'open' not in df.columns:
                df['open'] = df['close']
            if 'high' not in df.columns:
                df['high'] = df['ask']
            if 'low' not in df.columns:
                df['low'] = df['bid']
        
        # Ensure required columns
        required = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Add volume if missing (FX often doesn't have volume data)
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # Select required columns (plus optional bid/ask/spread)
        cols_to_keep = ['open', 'high', 'low', 'close', 'volume']
        for optional_col in ['bid', 'ask', 'spread']:
            if optional_col in df.columns:
                cols_to_keep.append(optional_col)
        
        df = df[cols_to_keep]
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns or 'Date' in df.columns or 'timestamp' in df.columns:
                date_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else 'Date')
                df.index = pd.to_datetime(df[date_col])
                df = df.drop(columns=[date_col])
            else:
                df.index = pd.to_datetime(df.index)
        
        # Sort and clean
        df = df.sort_index()
        df = df.dropna(subset=['close'])
        
        # Get metadata
        metadata = self.get_metadata(symbol)
        
        return PriceData(
            symbol=metadata.symbol,  # Use normalized symbol
            data=df,
            metadata=metadata,
            timeframe='1d'
        )
    
    def get_supported_exchanges(self) -> List[str]:
        """
        Get list of supported FX brokers.
        
        Note: FX is traded OTC, so these are brokers rather than exchanges.
        
        Returns:
            List of broker names
        """
        return self.supported_brokers
    
    def get_trading_calendar(self) -> Optional[pd.DatetimeIndex]:
        """
        FX markets trade 24/5, so no specific calendar needed.
        
        Returns:
            None (markets open 24/5)
        """
        return None
    
    def is_trading_day(self, date: pd.Timestamp) -> bool:
        """
        Check if a date is a trading day.
        
        FX markets are open Monday through Friday.
        
        Args:
            date: Date to check
        
        Returns:
            True if weekday (Mon-Fri), False if weekend
        """
        return date.weekday() < 5
    
    def calculate_pip_value(
        self,
        symbol: str,
        lot_size: float = 100000.0,
        account_currency: str = 'USD'
    ) -> float:
        """
        Calculate pip value for a position.
        
        Args:
            symbol: FX pair symbol
            lot_size: Position size in base currency units
            account_currency: Account currency for conversion
        
        Returns:
            Pip value in account currency
        """
        metadata = self.get_metadata(symbol)
        base, quote = self._parse_pair(metadata.symbol)
        
        pip_size = metadata.additional_info['pip_value']
        
        # For pairs quoted in account currency, pip value is straightforward
        if quote == account_currency:
            return pip_size * lot_size
        
        # For other pairs, would need current exchange rate for conversion
        # Simplified: return pip value in quote currency
        return pip_size * lot_size
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float,
        stop_loss_pips: float,
        symbol: str
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            account_balance: Total account balance
            risk_percent: Percentage of account to risk (as decimal, e.g., 0.02 for 2%)
            stop_loss_pips: Stop loss distance in pips
            symbol: FX pair symbol
        
        Returns:
            Position size in lots
        """
        if stop_loss_pips == 0:
            return 0.0
        
        # Calculate risk amount
        risk_amount = account_balance * risk_percent
        
        # Get pip value per standard lot
        pip_value = self.calculate_pip_value(symbol, lot_size=100000.0)
        
        # Calculate position size
        # risk_amount = stop_loss_pips * pip_value * position_size
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        return position_size
    
    def get_cross_rate(self, base: str, quote: str, via: str = 'USD') -> Tuple[str, str]:
        """
        Get the currency pairs needed to calculate a cross rate.
        
        Args:
            base: Base currency
            quote: Quote currency
            via: Intermediate currency (usually USD)
        
        Returns:
            Tuple of (pair1, pair2) to use for cross rate calculation
        """
        # Direct pair
        direct = f"{base}/{quote}"
        if self.validate_symbol(direct):
            return (direct, None)
        
        # Inverted pair
        inverted = f"{quote}/{base}"
        if self.validate_symbol(inverted):
            return (inverted, None)
        
        # Cross rate via intermediate currency
        pair1 = f"{base}/{via}"
        pair2 = f"{via}/{quote}"
        
        return (pair1, pair2)
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize FX symbol to standard format (BASE/QUOTE).
        
        Args:
            symbol: FX symbol in any format
        
        Returns:
            Normalized symbol with slash separator
        """
        # Remove all separators
        clean = symbol.replace('/', '').replace('-', '').replace('_', '').upper()
        
        # Split into base and quote
        base = clean[:3]
        quote = clean[3:]
        
        return f"{base}/{quote}"
    
    def _parse_pair(self, symbol: str) -> Tuple[str, str]:
        """
        Parse FX pair into base and quote currencies.
        
        Args:
            symbol: FX pair symbol
        
        Returns:
            Tuple of (base, quote)
        """
        clean = symbol.replace('/', '').replace('-', '').replace('_', '').upper()
        return (clean[:3], clean[3:])
    
    def _classify_pair(self, base: str, quote: str) -> str:
        """
        Classify currency pair as major, minor, or exotic.
        
        Args:
            base: Base currency
            quote: Quote currency
        
        Returns:
            Pair category
        """
        # Major pairs: involve USD and a G7 currency
        g7_currencies = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
        
        if (base == 'USD' and quote in g7_currencies) or (quote == 'USD' and base in g7_currencies):
            return 'major'
        
        # Minor pairs (crosses): involve two G7 currencies (no USD)
        if base in g7_currencies and quote in g7_currencies and 'USD' not in [base, quote]:
            return 'minor'
        
        # Exotic pairs: involve at least one emerging market currency
        return 'exotic'
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Foreign Exchange (FX) asset class supporting major, minor, and exotic currency pairs. "
            "Handles FX-specific features including pip calculations, position sizing, cross rates, "
            "and 24/5 trading. Supports various symbol formats (EUR/USD, EURUSD) and provides "
            "trading session information for Tokyo, London, and New York markets."
        )
