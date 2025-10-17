"""
Bond asset class plugin.

Handles bond-specific logic including fixed income instruments,
yield calculations, duration, and maturity handling.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_asset import BaseAssetClass
from ..core.types import AssetMetadata, AssetType, PriceData


class BondAsset(BaseAssetClass):
    """
    Asset class for bonds and fixed income instruments.
    
    Supports various bond types including:
    - Government bonds (Treasury bonds, notes, bills)
    - Corporate bonds (investment grade, high yield)
    - Municipal bonds
    - Bond ETFs and mutual funds
    
    Handles bond-specific features like yield calculations,
    duration, credit ratings, and maturity dates.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bond asset class.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - exchanges: List of supported exchanges
                   - bond_types: List of bond categories
                   - yield_convention: Yield calculation method (default: '30/360')
        """
        super().__init__(config)
        
        self.supported_exchanges = self.config.get(
            'exchanges',
            ['NYSE', 'NASDAQ', 'OTC', 'TreasuryDirect']
        )
        
        self.bond_types = self.config.get(
            'bond_types',
            ['government', 'corporate', 'municipal', 'etf']
        )
        
        self.yield_convention = self.config.get('yield_convention', '30/360')
        
        # Common bond symbols/tickers and their metadata
        self.known_bonds = {
            # Treasury ETFs
            'TLT': {'name': '20+ Year Treasury Bond ETF', 'type': 'etf', 'duration': 17.5},
            'IEF': {'name': '7-10 Year Treasury Bond ETF', 'type': 'etf', 'duration': 8.0},
            'SHY': {'name': '1-3 Year Treasury Bond ETF', 'type': 'etf', 'duration': 1.9},
            'AGG': {'name': 'Core US Aggregate Bond ETF', 'type': 'etf', 'duration': 6.5},
            'BND': {'name': 'Total Bond Market ETF', 'type': 'etf', 'duration': 6.7},
            'LQD': {'name': 'Investment Grade Corporate Bond ETF', 'type': 'etf', 'duration': 8.5},
            'HYG': {'name': 'High Yield Corporate Bond ETF', 'type': 'etf', 'duration': 3.8},
            'MUB': {'name': 'National Muni Bond ETF', 'type': 'etf', 'duration': 6.0},
            # Treasury futures
            'ZN': {'name': '10-Year Treasury Note Futures', 'type': 'government', 'duration': 7.5},
            'ZB': {'name': '30-Year Treasury Bond Futures', 'type': 'government', 'duration': 19.0},
            'ZF': {'name': '5-Year Treasury Note Futures', 'type': 'government', 'duration': 4.5},
        }
        
        # Credit rating tiers
        self.credit_ratings = {
            'investment_grade': ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-'],
            'high_yield': ['BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-', 'CC', 'C'],
            'default': ['D']
        }
    
    def get_asset_type(self) -> AssetType:
        """Return bond asset type."""
        return AssetType.BOND
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate bond symbol format.
        
        Valid formats:
        - 'TLT', 'AGG' (bond ETFs)
        - 'CUSIP123456' (CUSIP format - 9 alphanumeric)
        - 'US912828XY12' (ISIN format for US Treasuries)
        - 'ZN', 'ZB' (Treasury futures)
        
        Args:
            symbol: Symbol to validate
        
        Returns:
            True if valid bond symbol format
        """
        if not symbol:
            return False
        
        # Check for ETF format (2-5 uppercase letters)
        if 1 <= len(symbol) <= 5 and symbol.isalpha() and symbol.isupper():
            return True
        
        # Check for CUSIP format (9 alphanumeric characters)
        if len(symbol) == 9 and symbol.isalnum():
            return True
        
        # Check for ISIN format (12 characters, starts with country code)
        if len(symbol) == 12 and symbol[:2].isalpha() and symbol[2:].isalnum():
            return True
        
        # Check for Treasury futures (2 uppercase letters)
        if len(symbol) == 2 and symbol.isalpha() and symbol.isupper():
            return True
        
        return False
    
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for a bond.
        
        Args:
            symbol: Bond symbol
        
        Returns:
            AssetMetadata with bond information
        """
        # Check if it's a known bond
        if symbol in self.known_bonds:
            info = self.known_bonds[symbol]
            name = info['name']
            bond_type = info['type']
            duration = info.get('duration', 5.0)
        else:
            # Default values
            name = f"{symbol} Bond"
            bond_type = self._infer_bond_type(symbol)
            duration = 5.0
        
        # Determine exchange
        exchange = self._infer_exchange(symbol, bond_type)
        
        # Determine tick size and multiplier
        if bond_type == 'government' and len(symbol) == 2:
            # Treasury futures
            tick_size = 0.015625  # 1/64 of a point
            multiplier = 1000  # $1000 per point
        else:
            # ETFs and others
            tick_size = 0.01
            multiplier = 1.0
        
        # Get credit rating
        credit_rating = self._infer_credit_rating(symbol, bond_type)
        
        return AssetMetadata(
            symbol=symbol,
            name=name,
            asset_type=AssetType.BOND,
            exchange=exchange,
            currency="USD",
            multiplier=multiplier,
            tick_size=tick_size,
            lot_size=1.0,
            trading_hours={
                'regular': {'open': '09:30', 'close': '16:00'},
                'note': 'Bond markets may have extended hours depending on instrument type'
            },
            additional_info={
                'asset_class': 'bond',
                'bond_type': bond_type,
                'duration': duration,
                'credit_rating': credit_rating,
                'yield_convention': self.yield_convention,
                'interest_type': 'fixed',
                'coupon_frequency': 'semi-annual'
            }
        )
    
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize bond data to standard format.
        
        Handles various bond data formats including clean price,
        dirty price, and yield data.
        
        Args:
            data: Raw price data
            symbol: Bond symbol
        
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
            elif 'close' in col_lower or 'price' in col_lower:
                column_mapping[col] = 'close'
            elif 'volume' in col_lower or 'vol' in col_lower:
                column_mapping[col] = 'volume'
            elif 'yield' in col_lower:
                column_mapping[col] = 'yield'
            elif 'duration' in col_lower:
                column_mapping[col] = 'duration'
        
        df = df.rename(columns=column_mapping)
        
        # For bonds, volume might not always be available
        # If volume is missing, create a dummy column
        required = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Add volume if missing (bonds often don't report volume)
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # Select required columns (plus optional yield and duration)
        cols_to_keep = ['open', 'high', 'low', 'close', 'volume']
        for optional_col in ['yield', 'duration']:
            if optional_col in df.columns:
                cols_to_keep.append(optional_col)
        
        df = df[cols_to_keep]
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns or 'Date' in df.columns:
                date_col = 'date' if 'date' in df.columns else 'Date'
                df.index = pd.to_datetime(df[date_col])
                df = df.drop(columns=[date_col])
            else:
                df.index = pd.to_datetime(df.index)
        
        # Sort and clean
        df = df.sort_index()
        df = df.dropna(subset=['close'])  # Only require close to be non-null
        
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
    
    def calculate_yield_to_maturity(
        self,
        price: float,
        face_value: float,
        coupon_rate: float,
        years_to_maturity: float
    ) -> float:
        """
        Calculate approximate yield to maturity.
        
        This is a simplified calculation. For precise YTM, use iterative methods.
        
        Args:
            price: Current bond price
            face_value: Face/par value of bond
            coupon_rate: Annual coupon rate (as decimal)
            years_to_maturity: Years until maturity
        
        Returns:
            Approximate yield to maturity (as decimal)
        """
        if years_to_maturity == 0:
            return 0.0
        
        annual_coupon = face_value * coupon_rate
        capital_gain_per_year = (face_value - price) / years_to_maturity
        
        # Approximate YTM formula
        ytm = (annual_coupon + capital_gain_per_year) / ((face_value + price) / 2)
        
        return ytm
    
    def calculate_duration(
        self,
        price_data: PriceData,
        yield_change: float = 0.01
    ) -> float:
        """
        Calculate modified duration using price sensitivity.
        
        Args:
            price_data: Bond price data
            yield_change: Yield change for calculation (default 1% or 0.01)
        
        Returns:
            Modified duration
        """
        # This is a simplified calculation
        # In production, would use actual cash flows and yields
        
        if len(price_data.data) < 2:
            return self.get_metadata(price_data.symbol).additional_info.get('duration', 5.0)
        
        # Estimate duration from price volatility
        returns = price_data.data['close'].pct_change()
        price_volatility = returns.std()
        
        # Rough approximation: duration ≈ price_volatility / yield_volatility
        # Using typical yield volatility of 0.02 (2%)
        estimated_duration = price_volatility / 0.02
        
        return min(max(estimated_duration, 0.1), 30.0)  # Cap between 0.1 and 30
    
    def calculate_convexity(
        self,
        price: float,
        yield_rate: float,
        duration: float
    ) -> float:
        """
        Calculate bond convexity (simplified).
        
        Args:
            price: Current bond price
            yield_rate: Current yield (as decimal)
            duration: Bond duration
        
        Returns:
            Convexity measure
        """
        # Simplified convexity approximation
        # Actual calculation requires cash flow analysis
        convexity = duration ** 2 + duration
        return convexity
    
    def _infer_bond_type(self, symbol: str) -> str:
        """
        Infer bond type from symbol.
        
        Args:
            symbol: Bond symbol
        
        Returns:
            Bond type
        """
        # Check for known ETFs
        if len(symbol) <= 5 and symbol.isalpha():
            if symbol in self.known_bonds:
                return self.known_bonds[symbol]['type']
            return 'etf'
        
        # Check for Treasury futures
        if len(symbol) == 2 and symbol.startswith('Z'):
            return 'government'
        
        # Check ISIN format
        if len(symbol) == 12 and symbol.startswith('US'):
            return 'government'
        
        # Default
        return 'corporate'
    
    def _infer_exchange(self, symbol: str, bond_type: str) -> str:
        """
        Infer exchange from bond symbol and type.
        
        Args:
            symbol: Bond symbol
            bond_type: Type of bond
        
        Returns:
            Exchange code
        """
        if bond_type == 'government':
            if len(symbol) == 2:
                return 'CBOT'  # Treasury futures
            return 'TreasuryDirect'
        elif bond_type == 'etf':
            return 'NYSE' if len(symbol) == 3 else 'NASDAQ'
        elif bond_type == 'municipal':
            return 'OTC'
        else:  # corporate
            return 'NYSE'
    
    def _infer_credit_rating(self, symbol: str, bond_type: str) -> str:
        """
        Infer credit rating from bond type.
        
        Args:
            symbol: Bond symbol
            bond_type: Type of bond
        
        Returns:
            Credit rating
        """
        # Government bonds
        if bond_type == 'government':
            return 'AAA'
        
        # Known ETFs
        if symbol in self.known_bonds:
            if 'High Yield' in self.known_bonds[symbol]['name']:
                return 'BB'
            elif 'Investment Grade' in self.known_bonds[symbol]['name']:
                return 'A'
            else:
                return 'AA'
        
        # Default to investment grade
        return 'BBB'
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Bond asset class supporting government, corporate, and municipal bonds, "
            "as well as fixed income ETFs. Handles bond-specific calculations including "
            "yield to maturity, duration, and convexity. Supports various bond identifiers "
            "including tickers, CUSIPs, and ISINs."
        )
