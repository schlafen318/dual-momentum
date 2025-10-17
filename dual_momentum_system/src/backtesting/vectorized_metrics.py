"""
Vectorized performance metrics calculator for backtesting results.

Provides comprehensive calculation of standard and advanced performance metrics
using vectorized operations for maximum efficiency.
"""

from typing import Dict, Optional, Union

import pandas as pd
import numpy as np
from loguru import logger

try:
    import empyrical as ep
except ImportError:
    ep = None
    logger.warning("empyrical not available, using fallback calculations")


class VectorizedMetricsCalculator:
    """
    Calculate comprehensive performance metrics using vectorized operations.
    
    Computes all standard metrics including:
    - Return metrics: CAGR, total return, annual return
    - Risk metrics: Volatility, max drawdown, VaR, CVaR
    - Risk-adjusted: Sharpe, Sortino, Calmar, Omega
    - Trade metrics: Win rate, profit factor, payoff ratio
    - Timing metrics: Best/worst periods, recovery time
    
    Example:
        >>> calc = VectorizedMetricsCalculator(freq='D')
        >>> metrics = calc.calculate_all_metrics(
        ...     returns=returns_series,
        ...     equity_curve=equity_series,
        ...     trades=trades_df
        ... )
        >>> print(metrics['sharpe_ratio'])
    """
    
    def __init__(
        self,
        freq: str = 'D',
        periods_per_year: Optional[int] = None
    ):
        """
        Initialize metrics calculator.
        
        Args:
            freq: Data frequency ('D', 'H', 'T', 'S')
            periods_per_year: Override automatic period calculation
        """
        self.freq = freq
        
        # Determine periods per year
        if periods_per_year is not None:
            self.periods_per_year = periods_per_year
        else:
            freq_map = {
                'D': 252,  # Trading days
                'H': 252 * 6.5,  # Trading hours
                'T': 252 * 6.5 * 60,  # Trading minutes
                'S': 252 * 6.5 * 60 * 60,  # Trading seconds
                'W': 52,  # Weeks
                'M': 12,  # Months
                'Q': 4,  # Quarters
                'Y': 1  # Years
            }
            self.periods_per_year = freq_map.get(freq, 252)
    
    def calculate_all_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series,
        trades: Optional[pd.DataFrame] = None,
        risk_free_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics.
        
        Args:
            returns: Series of period returns
            equity_curve: Series of portfolio values
            trades: DataFrame of trade records (optional)
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Dictionary of all metrics
        """
        if len(returns) == 0:
            return self._empty_metrics()
        
        metrics = {}
        
        # Return metrics
        metrics.update(self.calculate_return_metrics(returns, equity_curve))
        
        # Risk metrics
        metrics.update(self.calculate_risk_metrics(returns, equity_curve))
        
        # Risk-adjusted metrics
        metrics.update(self.calculate_risk_adjusted_metrics(returns, risk_free_rate))
        
        # Trade metrics
        if trades is not None and len(trades) > 0:
            metrics.update(self.calculate_trade_metrics(trades))
        
        # Timing metrics
        metrics.update(self.calculate_timing_metrics(returns, equity_curve))
        
        return metrics
    
    def calculate_return_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate return-based metrics.
        
        Args:
            returns: Period returns
            equity_curve: Portfolio values
        
        Returns:
            Dict with return metrics
        """
        metrics = {}
        
        # Total return
        if len(equity_curve) > 0:
            metrics['total_return'] = (
                equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
            )
        else:
            metrics['total_return'] = 0.0
        
        # CAGR
        metrics['cagr'] = self.calculate_cagr(equity_curve)
        
        # Annual return (using returns)
        if len(returns) > 0:
            metrics['annual_return'] = (
                (1 + returns).prod() ** (self.periods_per_year / len(returns)) - 1
            )
        else:
            metrics['annual_return'] = 0.0
        
        # Cumulative return
        metrics['cumulative_return'] = float((1 + returns).prod() - 1) if len(returns) > 0 else 0.0
        
        # Average return
        metrics['avg_return'] = float(returns.mean()) if len(returns) > 0 else 0.0
        metrics['median_return'] = float(returns.median()) if len(returns) > 0 else 0.0
        
        return metrics
    
    def calculate_risk_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate risk metrics.
        
        Args:
            returns: Period returns
            equity_curve: Portfolio values
        
        Returns:
            Dict with risk metrics
        """
        metrics = {}
        
        # Volatility
        metrics['annual_volatility'] = self.calculate_annual_volatility(returns)
        metrics['downside_volatility'] = self.calculate_downside_volatility(returns)
        
        # Drawdown metrics
        dd_info = self.calculate_drawdown_metrics(equity_curve)
        metrics.update(dd_info)
        
        # Value at Risk
        metrics['var_95'] = self.calculate_var(returns, confidence=0.95)
        metrics['var_99'] = self.calculate_var(returns, confidence=0.99)
        
        # Conditional VaR (Expected Shortfall)
        metrics['cvar_95'] = self.calculate_cvar(returns, confidence=0.95)
        metrics['cvar_99'] = self.calculate_cvar(returns, confidence=0.99)
        
        # Skewness and Kurtosis
        if len(returns) > 0:
            metrics['skewness'] = float(returns.skew())
            metrics['kurtosis'] = float(returns.kurtosis())
        else:
            metrics['skewness'] = 0.0
            metrics['kurtosis'] = 0.0
        
        return metrics
    
    def calculate_risk_adjusted_metrics(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate risk-adjusted performance metrics.
        
        Args:
            returns: Period returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Dict with risk-adjusted metrics
        """
        metrics = {}
        
        # Sharpe ratio
        metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(returns, risk_free_rate)
        
        # Sortino ratio
        metrics['sortino_ratio'] = self.calculate_sortino_ratio(returns, risk_free_rate)
        
        # Calmar ratio
        metrics['calmar_ratio'] = self.calculate_calmar_ratio(returns)
        
        # Omega ratio
        metrics['omega_ratio'] = self.calculate_omega_ratio(returns, threshold=0.0)
        
        # Information ratio (using empyrical if available)
        if ep is not None and len(returns) > 0:
            try:
                metrics['information_ratio'] = float(
                    ep.excess_sharpe(returns, risk_free_rate)
                )
            except:
                metrics['information_ratio'] = metrics['sharpe_ratio']
        else:
            metrics['information_ratio'] = metrics['sharpe_ratio']
        
        return metrics
    
    def calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate trade-based metrics.
        
        Args:
            trades: DataFrame with trade records
        
        Returns:
            Dict with trade metrics
        """
        metrics = {}
        
        if len(trades) == 0:
            return {
                'num_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_win_loss_ratio': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration': 0.0,
            }
        
        # Determine PnL column
        pnl_col = None
        for col in ['PnL', 'pnl', 'return', 'Return']:
            if col in trades.columns:
                pnl_col = col
                break
        
        if pnl_col is None:
            logger.warning("No PnL column found in trades")
            return {}
        
        pnl_values = trades[pnl_col]
        
        # Number of trades
        metrics['num_trades'] = len(trades)
        
        # Win/loss statistics
        winning_trades = pnl_values[pnl_values > 0]
        losing_trades = pnl_values[pnl_values < 0]
        
        metrics['num_winning_trades'] = len(winning_trades)
        metrics['num_losing_trades'] = len(losing_trades)
        
        # Win rate
        if len(trades) > 0:
            metrics['win_rate'] = len(winning_trades) / len(trades)
        else:
            metrics['win_rate'] = 0.0
        
        # Average win/loss
        metrics['avg_win'] = float(winning_trades.mean()) if len(winning_trades) > 0 else 0.0
        metrics['avg_loss'] = float(abs(losing_trades.mean())) if len(losing_trades) > 0 else 0.0
        
        # Win/loss ratio
        if metrics['avg_loss'] > 0:
            metrics['avg_win_loss_ratio'] = metrics['avg_win'] / metrics['avg_loss']
        else:
            metrics['avg_win_loss_ratio'] = 0.0
        
        # Profit factor
        total_wins = winning_trades.sum() if len(winning_trades) > 0 else 0.0
        total_losses = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0.0
        
        if total_losses > 0:
            metrics['profit_factor'] = total_wins / total_losses
        else:
            metrics['profit_factor'] = float('inf') if total_wins > 0 else 0.0
        
        # Largest win/loss
        metrics['largest_win'] = float(pnl_values.max()) if len(pnl_values) > 0 else 0.0
        metrics['largest_loss'] = float(pnl_values.min()) if len(pnl_values) > 0 else 0.0
        
        # Trade duration
        if 'Duration' in trades.columns:
            # Duration might be in various formats
            duration_col = trades['Duration']
            if pd.api.types.is_timedelta64_dtype(duration_col):
                avg_duration_days = duration_col.mean().total_seconds() / 86400
                metrics['avg_trade_duration'] = float(avg_duration_days)
            else:
                metrics['avg_trade_duration'] = float(duration_col.mean())
        else:
            metrics['avg_trade_duration'] = 0.0
        
        # Expectancy
        metrics['expectancy'] = (
            metrics['win_rate'] * metrics['avg_win'] -
            (1 - metrics['win_rate']) * metrics['avg_loss']
        )
        
        return metrics
    
    def calculate_timing_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate timing and extreme value metrics.
        
        Args:
            returns: Period returns
            equity_curve: Portfolio values
        
        Returns:
            Dict with timing metrics
        """
        metrics = {}
        
        # Best/worst periods
        if len(returns) > 0:
            metrics['best_day'] = float(returns.max())
            metrics['worst_day'] = float(returns.min())
            
            # Best/worst month (if enough data)
            if len(returns) > 20:
                monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
                metrics['best_month'] = float(monthly_returns.max())
                metrics['worst_month'] = float(monthly_returns.min())
            else:
                metrics['best_month'] = 0.0
                metrics['worst_month'] = 0.0
            
            # Positive/negative periods
            metrics['positive_periods'] = int((returns > 0).sum())
            metrics['negative_periods'] = int((returns < 0).sum())
            metrics['positive_period_ratio'] = metrics['positive_periods'] / len(returns)
        else:
            metrics['best_day'] = 0.0
            metrics['worst_day'] = 0.0
            metrics['best_month'] = 0.0
            metrics['worst_month'] = 0.0
            metrics['positive_periods'] = 0
            metrics['negative_periods'] = 0
            metrics['positive_period_ratio'] = 0.0
        
        # Drawdown recovery
        metrics['max_drawdown_recovery_days'] = self.calculate_recovery_time(equity_curve)
        
        return metrics
    
    def calculate_cagr(self, equity_curve: pd.Series) -> float:
        """
        Calculate Compound Annual Growth Rate.
        
        Args:
            equity_curve: Portfolio values over time
        
        Returns:
            CAGR as decimal
        """
        if len(equity_curve) < 2:
            return 0.0
        
        start_value = equity_curve.iloc[0]
        end_value = equity_curve.iloc[-1]
        
        if start_value <= 0:
            return 0.0
        
        # Calculate number of years
        time_diff = equity_curve.index[-1] - equity_curve.index[0]
        years = time_diff.total_seconds() / (365.25 * 24 * 3600)
        
        if years == 0:
            return 0.0
        
        cagr = (end_value / start_value) ** (1 / years) - 1
        return float(cagr)
    
    def calculate_annual_volatility(self, returns: pd.Series) -> float:
        """
        Calculate annualized volatility.
        
        Args:
            returns: Period returns
        
        Returns:
            Annualized standard deviation
        """
        if len(returns) < 2:
            return 0.0
        
        return float(returns.std() * np.sqrt(self.periods_per_year))
    
    def calculate_downside_volatility(
        self,
        returns: pd.Series,
        threshold: float = 0.0
    ) -> float:
        """
        Calculate downside volatility (semi-deviation).
        
        Args:
            returns: Period returns
            threshold: Threshold for downside (default 0)
        
        Returns:
            Annualized downside volatility
        """
        if len(returns) < 2:
            return 0.0
        
        downside_returns = returns[returns < threshold]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_vol = downside_returns.std() * np.sqrt(self.periods_per_year)
        return float(downside_vol)
    
    def calculate_drawdown_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate comprehensive drawdown metrics.
        
        Args:
            equity_curve: Portfolio values
        
        Returns:
            Dict with drawdown metrics
        """
        if len(equity_curve) == 0:
            return {
                'max_drawdown': 0.0,
                'avg_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'num_drawdowns': 0
            }
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown series
        drawdown = (equity_curve - running_max) / running_max
        
        # Maximum drawdown
        max_dd = float(drawdown.min())
        
        # Average drawdown (of all drawdown periods)
        in_drawdown = drawdown < 0
        if in_drawdown.any():
            avg_dd = float(drawdown[in_drawdown].mean())
        else:
            avg_dd = 0.0
        
        # Count number of distinct drawdown periods
        dd_groups = (in_drawdown != in_drawdown.shift()).cumsum()
        num_drawdowns = len(dd_groups[in_drawdown].unique())
        
        # Maximum drawdown duration
        if in_drawdown.any():
            dd_durations = in_drawdown.groupby(dd_groups).sum()
            max_dd_duration = int(dd_durations.max())
        else:
            max_dd_duration = 0
        
        return {
            'max_drawdown': max_dd,
            'avg_drawdown': avg_dd,
            'max_drawdown_duration': max_dd_duration,
            'num_drawdowns': num_drawdowns
        }
    
    def calculate_recovery_time(self, equity_curve: pd.Series) -> int:
        """
        Calculate time to recover from maximum drawdown.
        
        Args:
            equity_curve: Portfolio values
        
        Returns:
            Number of periods to recover, or 0 if still in drawdown
        """
        if len(equity_curve) < 2:
            return 0
        
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        
        # Find maximum drawdown point
        max_dd_idx = drawdown.idxmin()
        max_dd_loc = equity_curve.index.get_loc(max_dd_idx)
        
        # Find recovery point (when equity reaches new high)
        recovery_curve = equity_curve.iloc[max_dd_loc:]
        peak_value = equity_curve.iloc[:max_dd_loc].max()
        
        recovery_points = recovery_curve[recovery_curve >= peak_value]
        
        if len(recovery_points) > 0:
            recovery_idx = recovery_points.index[0]
            recovery_loc = equity_curve.index.get_loc(recovery_idx)
            return recovery_loc - max_dd_loc
        else:
            # Still in drawdown
            return 0
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Period returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        # Convert annual risk-free rate to period rate
        period_rf = (1 + risk_free_rate) ** (1 / self.periods_per_year) - 1
        
        excess_returns = returns - period_rf
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = (
            excess_returns.mean() / excess_returns.std() *
            np.sqrt(self.periods_per_year)
        )
        
        return float(sharpe)
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        target: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio.
        
        Args:
            returns: Period returns
            risk_free_rate: Annual risk-free rate
            target: Target return threshold
        
        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0
        
        period_rf = (1 + risk_free_rate) ** (1 / self.periods_per_year) - 1
        excess_returns = returns - period_rf
        
        downside_returns = excess_returns[excess_returns < target]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        sortino = (
            excess_returns.mean() / downside_returns.std() *
            np.sqrt(self.periods_per_year)
        )
        
        return float(sortino)
    
    def calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Calmar ratio (CAGR / max drawdown).
        
        Args:
            returns: Period returns
        
        Returns:
            Calmar ratio
        """
        if len(returns) < 2:
            return 0.0
        
        # Create equity curve
        equity = (1 + returns).cumprod()
        
        cagr = self.calculate_cagr(equity)
        max_dd = abs(self.calculate_drawdown_metrics(equity)['max_drawdown'])
        
        if max_dd == 0:
            return 0.0
        
        return float(cagr / max_dd)
    
    def calculate_omega_ratio(
        self,
        returns: pd.Series,
        threshold: float = 0.0
    ) -> float:
        """
        Calculate Omega ratio.
        
        Args:
            returns: Period returns
            threshold: Return threshold
        
        Returns:
            Omega ratio
        """
        if len(returns) == 0:
            return 0.0
        
        returns_above = returns[returns > threshold] - threshold
        returns_below = threshold - returns[returns < threshold]
        
        gains = returns_above.sum() if len(returns_above) > 0 else 0.0
        losses = returns_below.sum() if len(returns_below) > 0 else 0.0
        
        if losses == 0:
            return float('inf') if gains > 0 else 0.0
        
        return float(gains / losses)
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk.
        
        Args:
            returns: Period returns
            confidence: Confidence level (e.g., 0.95 for 95%)
        
        Returns:
            VaR as negative value
        """
        if len(returns) == 0:
            return 0.0
        
        return float(returns.quantile(1 - confidence))
    
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).
        
        Args:
            returns: Period returns
            confidence: Confidence level
        
        Returns:
            CVaR as negative value
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        return float(tail_returns.mean())
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary."""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'annual_return': 0.0,
            'annual_volatility': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
        }
