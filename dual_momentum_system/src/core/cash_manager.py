"""
Cash Management Framework.

Provides explicit distinction between strategic cash (intentional holdings)
and operational cash (temporary buffers for trading), improving clarity
in portfolio reporting and position sizing decisions.
"""

from dataclasses import dataclass
from typing import Optional

from loguru import logger


@dataclass
class CashAllocation:
    """
    Breakdown of cash allocation.
    
    Attributes:
        strategic_cash: Intentionally held cash as part of strategy
        operational_buffer: Cash reserved for rebalancing/emergencies
        available_cash: Actual cash available for new positions
        total_cash: Total cash in portfolio
    """
    strategic_cash: float
    operational_buffer: float
    available_cash: float
    total_cash: float
    
    @property
    def deployment_rate(self) -> float:
        """Calculate how much of total portfolio should be deployed."""
        if self.total_cash == 0:
            return 1.0
        return 1.0 - (self.strategic_cash + self.operational_buffer) / self.total_cash


class CashManager:
    """
    Explicit cash management with strategic vs operational distinction.
    
    This class helps disambiguate different types of cash holdings:
    - Strategic cash: User-defined cash allocation (e.g., "always hold 5% cash")
    - Operational buffer: Cash for rebalancing, commissions, emergencies
    - Available cash: What's actually available for new positions
    
    Benefits:
    1. Clear reporting: Users know if cash is intentional or operational
    2. Better position sizing: Account for reserves in allocation decisions
    3. Risk management: Ensure buffer for unexpected costs
    
    Example:
        >>> cm = CashManager(strategic_cash_pct=0.05, operational_buffer_pct=0.02)
        >>> allocation = cm.calculate_allocation(total_value=100000, current_cash=10000)
        >>> print(allocation.available_cash)
        3000  # 10000 - 5000 (strategic) - 2000 (buffer)
    """
    
    def __init__(
        self,
        strategic_cash_pct: float = 0.0,
        operational_buffer_pct: float = 0.02,
        min_operational_buffer: float = 100.0
    ):
        """
        Initialize cash manager.
        
        Args:
            strategic_cash_pct: Percentage of portfolio to hold in cash (0.0 to 1.0)
            operational_buffer_pct: Percentage to reserve for operations (0.0 to 1.0)
            min_operational_buffer: Minimum absolute buffer amount in dollars
        
        Raises:
            ValueError: If percentages are invalid
        """
        if not 0.0 <= strategic_cash_pct <= 1.0:
            raise ValueError(f"strategic_cash_pct must be 0.0-1.0, got {strategic_cash_pct}")
        
        if not 0.0 <= operational_buffer_pct <= 1.0:
            raise ValueError(f"operational_buffer_pct must be 0.0-1.0, got {operational_buffer_pct}")
        
        if strategic_cash_pct + operational_buffer_pct > 1.0:
            raise ValueError(
                f"strategic_cash_pct ({strategic_cash_pct}) + "
                f"operational_buffer_pct ({operational_buffer_pct}) cannot exceed 1.0"
            )
        
        self.strategic_cash_pct = strategic_cash_pct
        self.operational_buffer_pct = operational_buffer_pct
        self.min_operational_buffer = min_operational_buffer
        
        logger.info(
            f"Initialized CashManager: strategic={strategic_cash_pct:.1%}, "
            f"operational={operational_buffer_pct:.1%}, "
            f"min_buffer=${min_operational_buffer:,.2f}"
        )
    
    def calculate_allocation(
        self,
        total_value: float,
        current_cash: float
    ) -> CashAllocation:
        """
        Calculate cash allocation breakdown.
        
        Args:
            total_value: Total portfolio value (cash + positions)
            current_cash: Current cash available
        
        Returns:
            CashAllocation with breakdown of cash components
        """
        # Calculate strategic cash target
        strategic_cash = total_value * self.strategic_cash_pct
        
        # Calculate operational buffer (at least minimum)
        operational_buffer = max(
            total_value * self.operational_buffer_pct,
            self.min_operational_buffer
        )
        
        # Available cash is what's left after reserves
        available_cash = max(0, current_cash - strategic_cash - operational_buffer)
        
        allocation = CashAllocation(
            strategic_cash=strategic_cash,
            operational_buffer=operational_buffer,
            available_cash=available_cash,
            total_cash=current_cash
        )
        
        logger.debug(
            f"Cash allocation: strategic=${strategic_cash:,.2f}, "
            f"buffer=${operational_buffer:,.2f}, "
            f"available=${available_cash:,.2f} of ${current_cash:,.2f} total"
        )
        
        return allocation
    
    def available_for_investment(self, total_value: float, current_cash: float) -> float:
        """
        Calculate capital available for risky assets.
        
        This is the portfolio value minus strategic cash and operational buffer.
        
        Args:
            total_value: Total portfolio value
            current_cash: Current cash available
        
        Returns:
            Amount available for investment in risky assets
        """
        allocation = self.calculate_allocation(total_value, current_cash)
        return allocation.available_cash
    
    def should_raise_cash(
        self,
        current_cash: float,
        total_value: float,
        required_cash: float
    ) -> bool:
        """
        Determine if positions should be liquidated to raise cash.
        
        Args:
            current_cash: Current cash balance
            total_value: Total portfolio value
            required_cash: Cash needed for new positions
        
        Returns:
            True if need to liquidate positions, False if current cash sufficient
        """
        allocation = self.calculate_allocation(total_value, current_cash)
        
        # Need to raise cash if required exceeds available
        return required_cash > allocation.available_cash
    
    def get_strategic_cash_target(self, total_value: float) -> float:
        """
        Get strategic cash target amount.
        
        Args:
            total_value: Total portfolio value
        
        Returns:
            Target strategic cash amount in dollars
        """
        return total_value * self.strategic_cash_pct
    
    def get_operational_buffer_target(self, total_value: float) -> float:
        """
        Get operational buffer target amount.
        
        Args:
            total_value: Total portfolio value
        
        Returns:
            Target operational buffer amount in dollars
        """
        return max(
            total_value * self.operational_buffer_pct,
            self.min_operational_buffer
        )
    
    def is_cash_adequate(
        self,
        current_cash: float,
        total_value: float,
        tolerance: float = 0.1
    ) -> bool:
        """
        Check if cash levels are adequate (within tolerance of targets).
        
        Args:
            current_cash: Current cash balance
            total_value: Total portfolio value
            tolerance: Tolerance for deviation (e.g., 0.1 = 10%)
        
        Returns:
            True if cash is adequate, False if rebalancing needed
        """
        strategic_target = self.get_strategic_cash_target(total_value)
        buffer_target = self.get_operational_buffer_target(total_value)
        total_target = strategic_target + buffer_target
        
        lower_bound = total_target * (1 - tolerance)
        upper_bound = total_target * (1 + tolerance)
        
        return lower_bound <= current_cash <= upper_bound
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CashManager(strategic={self.strategic_cash_pct:.1%}, "
            f"buffer={self.operational_buffer_pct:.1%})"
        )
