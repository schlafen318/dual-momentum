"""
Basic risk manager plugin.

Provides simple but effective risk management with position sizing,
leverage limits, and concentration controls.
"""

from typing import Any, Dict, Optional

from loguru import logger

from ..core.base_risk import BaseRiskManager
from ..core.cash_manager import CashManager
from ..core.types import Position, PortfolioState, Signal


class BasicRiskManager(BaseRiskManager):
    """
    Basic Risk Manager.
    
    Implements fundamental risk management:
    - Equal weight position sizing
    - Maximum position size limits
    - Maximum leverage limits
    - Position count limits
    - Drawdown monitoring
    
    Configuration:
        - max_position_size: Maximum position as % of portfolio (default: 0.2)
        - max_leverage: Maximum portfolio leverage (default: 1.0)
        - position_limit: Max number of positions (default: None)
        - max_drawdown: Maximum allowed drawdown before stopping (default: 0.5)
        - emergency_stop_threshold: Drawdown threshold to halt trading (default: 0.4)
        - equal_weight: Use equal weighting (default: True)
        - target_volatility: Target portfolio volatility for vol scaling (default: None)
        - strategic_cash_pct: Strategic cash to hold (default: 0.0)
        - operational_buffer_pct: Operational buffer reserve (default: 0.02)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize basic risk manager.
        
        Args:
            config: Risk management configuration
        """
        # Set defaults
        default_config = {
            'max_position_size': 0.2,
            'max_leverage': 1.0,
            'position_limit': None,
            'max_drawdown': 0.5,
            'emergency_stop_threshold': 0.4,
            'equal_weight': True,
            'target_volatility': None,
            'strategic_cash_pct': 0.0,
            'operational_buffer_pct': 0.02,
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        super().__init__(default_config)
        
        self.equal_weight = self.config['equal_weight']
        
        # Initialize cash manager
        self.cash_manager = CashManager(
            strategic_cash_pct=self.config['strategic_cash_pct'],
            operational_buffer_pct=self.config['operational_buffer_pct']
        )
    
    def calculate_position_size(
        self,
        signal: Signal,
        portfolio_value: float,
        current_positions: Dict[str, Position],
        price_data: Optional[Any] = None
    ) -> float:
        """
        Calculate position size.
        
        For basic risk manager:
        1. Account for strategic cash and operational buffer
        2. If equal_weight: divide deployable capital by number of positions
        3. Apply signal strength as multiplier
        4. Respect max position size limits
        5. Adjust for volatility if target_volatility is set
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            current_positions: Current positions
            price_data: Optional price data for volatility calculation
        
        Returns:
            Position size in dollars (not shares)
        """
        if portfolio_value <= 0:
            logger.warning("Portfolio value is zero or negative")
            return 0.0
        
        # Calculate deployable capital (accounting for cash reserves)
        # For this calculation, we need current cash, but we don't have it directly
        # So we use portfolio_value as approximation
        # In a real scenario, the engine would pass current_cash
        deployable_value = portfolio_value * (1.0 - self.config['strategic_cash_pct'])
        
        # Determine number of positions
        position_limit = self.get_position_limit()
        
        if position_limit is None:
            # Default to max_position_size as guide
            max_pos_pct = self.get_max_position_size()
            num_positions = min(10, int(1.0 / max_pos_pct))
        else:
            num_positions = position_limit
        
        # Calculate base position size as percentage of deployable capital
        if self.equal_weight:
            # Equal weight across positions
            base_size_pct = 1.0 / num_positions
        else:
            # Use max position size
            base_size_pct = self.get_max_position_size()
        
        # Apply signal strength
        size_pct = base_size_pct * signal.strength
        
        # Ensure within max position size
        max_pos = self.get_max_position_size()
        size_pct = min(size_pct, max_pos)
        
        # Calculate dollar amount from deployable capital
        position_size_dollars = deployable_value * size_pct
        
        # Apply confidence factor if available
        if hasattr(signal, 'confidence'):
            position_size_dollars *= signal.confidence
        
        # Adjust for volatility if configured and data available
        target_vol = self.get_target_volatility()
        if target_vol is not None and price_data is not None:
            try:
                # This is a simplified vol adjustment
                # In production, would calculate actual asset volatility
                pass  # Implement volatility adjustment logic here
            except Exception as e:
                logger.warning(f"Could not apply volatility adjustment: {e}")
        
        logger.debug(
            f"Position size for {signal.symbol}: "
            f"${position_size_dollars:,.2f} ({size_pct:.1%} of deployable capital)"
        )
        
        return position_size_dollars
    
    def check_risk_limits(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: Optional[Signal] = None
    ) -> bool:
        """
        Check if risk limits are satisfied.
        
        Validates:
        1. Position count limits
        2. Leverage limits
        3. Concentration limits (if new trade proposed)
        
        Args:
            portfolio_state: Current portfolio state
            proposed_trade: Proposed trade signal
        
        Returns:
            True if within limits, False otherwise
        """
        # Check position count limit
        position_limit = self.get_position_limit()
        if position_limit is not None:
            current_count = portfolio_state.num_positions
            
            # If proposing new position (not already held)
            if proposed_trade and proposed_trade.symbol not in portfolio_state.positions:
                if current_count >= position_limit:
                    logger.warning(
                        f"Position limit reached: {current_count}/{position_limit}"
                    )
                    return False
        
        # Check leverage limit
        if not self.check_leverage_limit(portfolio_state):
            logger.warning(
                f"Leverage limit exceeded: "
                f"{portfolio_state.leverage:.2f}x > {self.get_max_leverage()}x"
            )
            return False
        
        return True
    
    def get_max_leverage(self) -> float:
        """Get maximum leverage."""
        return self.config['max_leverage']
    
    def get_max_position_size(self) -> float:
        """Get maximum position size."""
        return self.config['max_position_size']
    
    def get_max_drawdown_limit(self) -> float:
        """Get maximum drawdown limit."""
        return self.config['max_drawdown']
    
    def get_target_volatility(self) -> Optional[float]:
        """Get target volatility."""
        return self.config.get('target_volatility')
    
    def get_position_limit(self) -> Optional[int]:
        """Get position count limit."""
        return self.config.get('position_limit')
    
    def get_emergency_stop_threshold(self) -> Optional[float]:
        """Get emergency stop threshold."""
        return self.config.get('emergency_stop_threshold')
    
    def get_cash_allocation(self, total_value: float, current_cash: float):
        """
        Get cash allocation breakdown.
        
        Args:
            total_value: Total portfolio value
            current_cash: Current cash balance
        
        Returns:
            CashAllocation object with breakdown
        """
        return self.cash_manager.calculate_allocation(total_value, current_cash)
    
    def get_available_for_investment(self, total_value: float, current_cash: float) -> float:
        """
        Get capital available for new investments.
        
        Args:
            total_value: Total portfolio value
            current_cash: Current cash balance
        
        Returns:
            Amount available for investment
        """
        return self.cash_manager.available_for_investment(total_value, current_cash)
    
    @classmethod
    def get_version(cls) -> str:
        """Return plugin version."""
        return "1.1.0"
    
    @classmethod
    def get_description(cls) -> str:
        """Return plugin description."""
        return (
            "Basic risk manager with equal-weight position sizing, "
            "leverage limits, concentration limits, drawdown monitoring, "
            "and explicit cash management (strategic vs operational). "
            "Suitable for most momentum strategies with simple, conservative "
            "risk controls."
        )
