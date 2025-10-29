"""
Base classes for portfolio optimization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime

import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class OptimizationResult:
    """
    Results from portfolio optimization.
    
    Attributes:
        weights: Dictionary mapping asset symbols to weights
        method: Optimization method used
        expected_return: Expected portfolio return (if applicable)
        expected_volatility: Expected portfolio volatility
        sharpe_ratio: Expected Sharpe ratio (if applicable)
        diversification_ratio: Diversification ratio (if applicable)
        risk_contributions: Risk contribution by asset (if applicable)
        metadata: Additional method-specific information
    """
    weights: Dict[str, float]
    method: str
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    diversification_ratio: Optional[float] = None
    risk_contributions: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'weights': self.weights,
            'method': self.method,
            'expected_return': self.expected_return,
            'expected_volatility': self.expected_volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'diversification_ratio': self.diversification_ratio,
            'risk_contributions': self.risk_contributions,
            'metadata': self.metadata,
        }
    
    def to_series(self) -> pd.Series:
        """Convert weights to pandas Series."""
        return pd.Series(self.weights)


class PortfolioOptimizer(ABC):
    """
    Base class for portfolio optimization methods.
    
    All portfolio optimizers must implement the optimize() method.
    """
    
    def __init__(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        risk_free_rate: float = 0.0,
    ):
        """
        Initialize portfolio optimizer.
        
        Args:
            min_weight: Minimum weight per asset (default: 0.0, no shorts)
            max_weight: Maximum weight per asset (default: 1.0, full allocation)
            risk_free_rate: Risk-free rate for Sharpe ratio calculations
        """
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.risk_free_rate = risk_free_rate
        
        logger.debug(
            f"Initialized {self.__class__.__name__}: "
            f"min_weight={min_weight}, max_weight={max_weight}"
        )
    
    @abstractmethod
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Optimize portfolio weights.
        
        Args:
            returns: DataFrame of asset returns (each column is an asset)
            **kwargs: Additional method-specific parameters
        
        Returns:
            OptimizationResult with optimal weights and metrics
        """
        pass
    
    def _validate_returns(self, returns: pd.DataFrame) -> None:
        """Validate returns DataFrame."""
        if returns.empty:
            raise ValueError("Returns DataFrame is empty")
        
        if returns.isnull().any().any():
            logger.warning("Returns contain NaN values, will be handled by optimizer")
        
        if len(returns.columns) < 2:
            raise ValueError("Need at least 2 assets for portfolio optimization")
    
    def _normalize_weights(self, weights: np.ndarray) -> np.ndarray:
        """Normalize weights to sum to 1.0."""
        total = np.sum(weights)
        if total <= 0:
            raise ValueError("Total weight is zero or negative")
        return weights / total
    
    def _apply_constraints(self, weights: np.ndarray) -> np.ndarray:
        """Apply min/max weight constraints."""
        weights = np.clip(weights, self.min_weight, self.max_weight)
        return self._normalize_weights(weights)
    
    def _calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        returns: pd.DataFrame,
        cov_matrix: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics.
        
        Args:
            weights: Portfolio weights
            returns: Asset returns DataFrame
            cov_matrix: Covariance matrix (will be calculated if not provided)
        
        Returns:
            Dictionary with portfolio metrics
        """
        if cov_matrix is None:
            cov_matrix = returns.cov()
        
        mean_returns = returns.mean()
        
        # Portfolio return and volatility
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe ratio
        sharpe_ratio = (
            (portfolio_return - self.risk_free_rate) / portfolio_volatility
            if portfolio_volatility > 0 else 0.0
        )
        
        # Diversification ratio
        asset_volatilities = np.sqrt(np.diag(cov_matrix))
        weighted_volatilities = np.dot(weights, asset_volatilities)
        diversification_ratio = (
            weighted_volatilities / portfolio_volatility
            if portfolio_volatility > 0 else 1.0
        )
        
        # Risk contributions
        marginal_contrib = np.dot(cov_matrix, weights)
        risk_contrib = weights * marginal_contrib
        risk_contrib_pct = risk_contrib / np.sum(risk_contrib) if np.sum(risk_contrib) > 0 else weights
        
        return {
            'return': float(portfolio_return),
            'volatility': float(portfolio_volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'diversification_ratio': float(diversification_ratio),
            'risk_contributions': risk_contrib_pct,
        }
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"min_weight={self.min_weight}, "
            f"max_weight={self.max_weight}, "
            f"risk_free_rate={self.risk_free_rate})"
        )
