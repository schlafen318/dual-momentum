"""
Commodity asset class plugin.

Handles commodity-specific logic including futures contracts,
physical vs financial commodities, and expiration handling.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.base_asset import BaseAssetClass
from ..core.types import AssetMetadata, AssetType, PriceData


class CommodityAsset(BaseAssetClass):
    """
    Asset class for commodities.
    
    Supports various commodity types including:
    - Energy (crude oil, natural gas, gasoline)
    - Metals (gold, silver, copper, platinum)
    - Agriculture (corn, wheat, soybeans, coffee)
    - Livestock (cattle, hogs)
    
    Handles commodity-specific features like contract specifications,
    seasonality, and futures rollover.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize commodity asset class.
        
        Args:
            config: Configuration dictionary. Supported keys:
                   - exchanges: List of supported exchanges
                   - commodity_types: List of commodity categories
                   - contract_months: Standard contract month codes
        """
        super().__init__(config)
        
        self.supported_exchanges = self.config.get(
            'exchanges',
            ['NYMEX', 'COMEX', 'CBOT', 'CME', 'ICE']
        )
        
        self.commodity_types = self.config.get(
            'commodity_types',
            ['energy', 'metals', 'agriculture', 'livestock']
        )
        
        # Standard futures contract month codes
        self.contract_months = {
            'F': 'Jan', 'G': 'Feb', 'H': 'Mar', 'J': 'Apr',
            'K': 'May', 'M': 'Jun', 'N': 'Jul', 'Q': 'Aug',
            'U': 'Sep', 'V': 'Oct', 'X': 'Nov', 'Z': 'Dec'
        }
        
        # Common commodity symbols and their metadata
        self.known_commodities = {
            'CL': {'name': 'Crude Oil WTI', 'type': 'energy', 'unit': 'barrel', 'multiplier': 1000},
            'GC': {'name': 'Gold', 'type': 'metals', 'unit': 'troy oz', 'multiplier': 100},
            'SI': {'name': 'Silver', 'type': 'metals', 'unit': 'troy oz', 'multiplier': 5000},
            'NG': {'name': 'Natural Gas', 'type': 'energy', 'unit': 'MMBtu', 'multiplier': 10000},
            'HG': {'name': 'Copper', 'type': 'metals', 'unit': 'pound', 'multiplier': 25000},
            'ZC': {'name': 'Corn', 'type': 'agriculture', 'unit': 'bushel', 'multiplier': 5000},
            'ZW': {'name': 'Wheat', 'type': 'agriculture', 'unit': 'bushel', 'multiplier': 5000},
            'ZS': {'name': 'Soybeans', 'type': 'agriculture', 'unit': 'bushel', 'multiplier': 5000},
            'KC': {'name': 'Coffee', 'type': 'agriculture', 'unit': 'pound', 'multiplier': 37500},
            'HE': {'name': 'Lean Hogs', 'type': 'livestock', 'unit': 'pound', 'multiplier': 40000},
            'LE': {'name': 'Live Cattle', 'type': 'livestock', 'unit': 'pound', 'multiplier': 40000},
        }
    
    def get_asset_type(self) -> AssetType:
        """Return commodity asset type."""
        return AssetType.COMMODITY
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate commodity symbol format.
        
        Valid formats:
        - 'GC' (generic/continuous contract)
        - 'GCZ23' (specific contract: Gold Dec 2023)
        - 'CL=F' (Yahoo Finance futures format)
        - 'GC1!' (continuous contract notation)
        
        Args:
            symbol: Symbol to validate
        
        Returns:
            True if valid commodity symbol format
        """
        if not symbol:
            return False
        
        # Remove common suffixes
        clean_symbol = symbol.replace('=F', '').replace('!', '')
        
        # Check for generic symbol (2-3 letters)
        if len(clean_symbol) in [2, 3] and clean_symbol.isalpha():
            return True
        
        # Check for contract-specific format (symbol + month code + year)
        if len(clean_symbol) >= 4:
            # Extract base symbol (first 2-3 chars)
            if clean_symbol[:2].isalpha():
                base = clean_symbol[:2]
                rest = clean_symbol[2:]
            elif len(clean_symbol) >= 3 and clean_symbol[:3].isalpha():
                base = clean_symbol[:3]
                rest = clean_symbol[3:]
            else:
                return False
            
            # Check if rest contains month code and year
            if len(rest) >= 2:
                month_code = rest[0]
                year_part = rest[1:]
                
                # Month code should be valid
                if month_code in self.contract_months:
                    # Year should be numeric
                    if year_part.isdigit():
                        return True
        
        return False
    
    def get_metadata(self, symbol: str) -> AssetMetadata:
        """
        Get metadata for a commodity.
        
        Args:
            symbol: Commodity symbol
        
        Returns:
            AssetMetadata with commodity information
        """
        # Parse symbol to get base commodity
        clean_symbol = symbol.replace('=F', '').replace('!', '').replace('1', '')
        
        # Extract base symbol (first 2 chars usually)
        base_symbol = clean_symbol[:2] if len(clean_symbol) >= 2 else clean_symbol
        
        # Get commodity info
        if base_symbol in self.known_commodities:
            info = self.known_commodities[base_symbol]
            name = info['name']
            multiplier = info['multiplier']
            commodity_type = info['type']
            unit = info['unit']
        else:
            # Default values for unknown commodities
            name = f"{base_symbol} Commodity"
            multiplier = 1.0
            commodity_type = 'unknown'
            unit = 'contract'
        
        # Determine exchange based on commodity type
        exchange = self._infer_exchange(base_symbol, commodity_type)
        
        # Determine tick size based on commodity
        tick_size = self._get_tick_size(base_symbol)
        
        return AssetMetadata(
            symbol=symbol,
            name=name,
            asset_type=AssetType.COMMODITY,
            exchange=exchange,
            currency="USD",
            multiplier=multiplier,
            tick_size=tick_size,
            lot_size=1.0,
            trading_hours={
                'regular': {'open': '08:00', 'close': '14:30'},
                'electronic': {'open': '18:00', 'close': '17:00'},  # Nearly 24 hours
                'note': 'Commodity trading hours vary by contract'
            },
            additional_info={
                'asset_class': 'commodity',
                'commodity_type': commodity_type,
                'unit': unit,
                'settlement': 'physical' if commodity_type in ['agriculture', 'livestock'] else 'cash',
                'contract_size': multiplier
            }
        )
    
    def normalize_data(self, data: pd.DataFrame, symbol: str) -> PriceData:
        """
        Normalize commodity data to standard format.
        
        Handles futures contract data and various data source formats.
        
        Args:
            data: Raw price data
            symbol: Commodity symbol
        
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
            elif 'close' in col_lower or 'settle' in col_lower:
                # Commodities often use 'settle' price
                column_mapping[col] = 'close'
            elif 'volume' in col_lower or 'vol' in col_lower:
                column_mapping[col] = 'volume'
            elif 'open interest' in col_lower or 'openinterest' in col_lower:
                column_mapping[col] = 'open_interest'
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Select required columns (and open_interest if available)
        cols_to_keep = required.copy()
        if 'open_interest' in df.columns:
            cols_to_keep.append('open_interest')
        
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
    
    def get_contract_month(self, symbol: str) -> Optional[str]:
        """
        Extract contract month from symbol.
        
        Args:
            symbol: Commodity symbol (e.g., 'GCZ23')
        
        Returns:
            Contract month name or None if generic contract
        """
        # Remove suffixes
        clean_symbol = symbol.replace('=F', '').replace('!', '')
        
        # Look for month code
        for char in clean_symbol:
            if char in self.contract_months:
                return self.contract_months[char]
        
        return None
    
    def get_contract_year(self, symbol: str) -> Optional[int]:
        """
        Extract contract year from symbol.
        
        Args:
            symbol: Commodity symbol (e.g., 'GCZ23')
        
        Returns:
            Contract year or None if generic contract
        """
        # Remove suffixes
        clean_symbol = symbol.replace('=F', '').replace('!', '')
        
        # Extract year digits at the end
        year_str = ''
        for char in reversed(clean_symbol):
            if char.isdigit():
                year_str = char + year_str
            else:
                break
        
        if year_str:
            year = int(year_str)
            # Convert 2-digit year to 4-digit (assume 20xx)
            if year < 100:
                year += 2000
            return year
        
        return None
    
    def _infer_exchange(self, base_symbol: str, commodity_type: str) -> str:
        """
        Infer exchange from commodity symbol and type.
        
        Args:
            base_symbol: Base commodity symbol
            commodity_type: Type of commodity
        
        Returns:
            Exchange code
        """
        # Energy and metals mapping
        energy_metals_map = {
            'CL': 'NYMEX',  # Crude Oil
            'NG': 'NYMEX',  # Natural Gas
            'GC': 'COMEX',  # Gold
            'SI': 'COMEX',  # Silver
            'HG': 'COMEX',  # Copper
        }
        
        if base_symbol in energy_metals_map:
            return energy_metals_map[base_symbol]
        
        # Default by type
        if commodity_type == 'energy':
            return 'NYMEX'
        elif commodity_type == 'metals':
            return 'COMEX'
        elif commodity_type in ['agriculture', 'livestock']:
            return 'CBOT'
        else:
            return 'CME'
    
    def _get_tick_size(self, base_symbol: str) -> float:
        """
        Get tick size for a commodity.
        
        Args:
            base_symbol: Base commodity symbol
        
        Returns:
            Tick size
        """
        # Common tick sizes
        tick_sizes = {
            'CL': 0.01,   # $0.01 per barrel
            'GC': 0.10,   # $0.10 per oz
            'SI': 0.005,  # $0.005 per oz
            'NG': 0.001,  # $0.001 per MMBtu
            'HG': 0.0005, # $0.0005 per lb
            'ZC': 0.25,   # 1/4 cent per bushel
            'ZW': 0.25,   # 1/4 cent per bushel
            'ZS': 0.25,   # 1/4 cent per bushel
        }
        
        return tick_sizes.get(base_symbol, 0.01)
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.0.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Commodity asset class supporting energy, metals, agriculture, and livestock. "
            "Handles futures contracts with expiration dates, contract specifications, "
            "and commodity-specific trading rules. Supports both physical and financial settlement."
        )
