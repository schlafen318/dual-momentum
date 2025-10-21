"""
Performance metrics calculation module.

Provides comprehensive performance metrics for backtest results including
returns, risk, and risk-adjusted performance measures.
"""

from typing import Dict, Optional

import pandas as pd
import numpy as np
from loguru import logger


class PerformanceCalculator:
    """
    Calculate performance metrics for backtesting results.
    
    Computes standard metrics like Sharpe ratio, maximum drawdown,
    Sortino ratio, Calmar ratio, and various return statistics.
    """
    
    def __init__(self, periods_per_year: int = 252):
        """
        Initialize performance calculator.
        self.periods_per_year = periods_per_year
        Args:
            periods_per_year: Number of periods per year for annualization
                             (252 for daily, 12 for monthly, 52 for weekly)
        """
        self.periods_per_year = periods_per_year
    
    def calculate_metrics(
        self,
        returns: pd.Series,
        equity_curve: pd.Series,
        risk_free_rate: float = 0.0,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics.
        
        Args:
            returns: Series of period returns
            equity_curve: Series of portfolio values
            risk_free_rate: Annual risk-free rate
            benchmark_returns: Benchmark returns for comparison (optional)
        
        Returns:
            Dictionary of performance metrics
        """
        if len(returns) == 0:
            logger.warning("No returns data to calculate metrics")
            return self._empty_metrics()
        
        metrics = {}
        
        # Return metrics
        metrics['total_return'] = self.total_return(equity_curve)
        metrics['annual_return'] = self.annual_return(returns)
        # Alias used by dashboard
        metrics['annualized_return'] = metrics['annual_return']
        # CAGR using equity curve span
        metrics['cagr'] = self.cagr(equity_curve)
        metrics['annual_volatility'] = self.annual_volatility(returns)
        # Alias used by dashboard
        metrics['volatility'] = metrics['annual_volatility']
        
        # Risk metrics
        metrics['max_drawdown'] = self.max_drawdown(equity_curve)
        metrics['max_drawdown_duration'] = self.max_drawdown_duration(equity_curve)
        
        # Risk-adjusted metrics
        metrics['sharpe_ratio'] = self.sharpe_ratio(returns, risk_free_rate)
        metrics['sortino_ratio'] = self.sortino_ratio(returns, risk_free_rate)
        metrics['calmar_ratio'] = self.calmar_ratio(returns, equity_curve)
        
        # Win rate metrics
        metrics['win_rate'] = self.win_rate(returns)
        metrics['avg_win'] = self.average_win(returns)
        metrics['avg_loss'] = self.average_loss(returns)
        metrics['win_loss_ratio'] = self.win_loss_ratio(returns)
        
        # Additional metrics
        metrics['best_day'] = float(returns.max()) if len(returns) > 0 else 0.0
        metrics['worst_day'] = float(returns.min()) if len(returns) > 0 else 0.0
        metrics['num_periods'] = len(returns)
        
        # Monthly metrics (best/worst/positive months)
        monthly = self.monthly_metrics(returns)
        metrics.update(monthly)
        
        # Benchmark comparison metrics
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            metrics.update(self.calculate_benchmark_metrics(returns, benchmark_returns, risk_free_rate))
        
        return metrics
    
    def total_return(self, equity_curve: pd.Series) -> float:
        """
        Calculate total return.
        
        Args:
            equity_curve: Portfolio value over time
        
        Returns:
            Total return as decimal (e.g., 0.25 = 25%)
        """
        if len(equity_curve) == 0:
            return 0.0
        
        start_value = equity_curve.iloc[0]
        end_value = equity_curve.iloc[-1]
        
        if start_value == 0:
            return 0.0
        
        return (end_value - start_value) / start_value
    
    def annual_return(self, returns: pd.Series) -> float:
        """
        Calculate annualized return.
        
        Args:
            returns: Series of period returns
        
        Returns:
            Annualized return
        """
        if len(returns) == 0:
            return 0.0
        
        cumulative_return = (1 + returns).prod() - 1
        num_years = len(returns) / self.periods_per_year
        
        if num_years == 0:
            return 0.0
        
        annual_return = (1 + cumulative_return) ** (1 / num_years) - 1
        return annual_return

    def cagr(self, equity_curve: pd.Series) -> float:
        """
        Calculate Compound Annual Growth Rate from equity curve.
        """
        if len(equity_curve) < 2:
            return 0.0
        start_value = equity_curve.iloc[0]
        end_value = equity_curve.iloc[-1]
        if start_value <= 0 or end_value <= 0:
            return 0.0
        try:
            time_diff = equity_curve.index[-1] - equity_curve.index[0]
            years = time_diff.total_seconds() / (365.25 * 24 * 3600)
            if years <= 0:
                return 0.0
            return float((end_value / start_value) ** (1 / years) - 1)
        except Exception:
            return 0.0

    def monthly_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate monthly best/worst returns and % positive months.
        Returns:
            Dict with keys: best_month, worst_month, positive_months
            - best_month/worst_month are decimals (e.g., 0.05 for +5%)
            - positive_months is a percentage value (0-100)
        """
        out = {
            'best_month': 0.0,
            'worst_month': 0.0,
            'positive_months': 0.0,
        }
        if len(returns) == 0:
            return out
        try:
            # Only compute if index supports resampling and we have enough points
            if hasattr(returns.index, 'to_period') and len(returns) > 20:
                monthly = returns.resample('ME').apply(lambda x: (1 + x).prod() - 1 if len(x) > 0 else 0)
                if len(monthly) > 0:
                    out['best_month'] = float(monthly.max())
                    out['worst_month'] = float(monthly.min())
                    out['positive_months'] = float((monthly > 0).sum() / len(monthly) * 100)
        except Exception:
            # Keep defaults on any failure
            pass
        return out
    
    def annual_volatility(self, returns: pd.Series) -> float:
        """
        Calculate annualized volatility.
        
        Args:
            returns: Series of period returns
        
        Returns:
            Annualized volatility
        """
        if len(returns) == 0:
            return 0.0
        
        return returns.std() * np.sqrt(self.periods_per_year)
    
    def sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Convert annual risk-free rate to period rate
        period_rf_rate = (1 + risk_free_rate) ** (1 / self.periods_per_year) - 1
        
        excess_returns = returns - period_rf_rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        return np.sqrt(self.periods_per_year) * excess_returns.mean() / excess_returns.std()
    
    def sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio.
        
        Similar to Sharpe but only penalizes downside volatility.
        
        Args:
            returns: Series of period returns
            risk_free_rate: Annual risk-free rate
            target_return: Target return (default 0)
        
        Returns:
            Sortino ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Convert annual risk-free rate to period rate
        period_rf_rate = (1 + risk_free_rate) ** (1 / self.periods_per_year) - 1
        
        excess_returns = returns - period_rf_rate
        
        # Calculate downside deviation
        downside_returns = excess_returns[excess_returns < target_return]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        return np.sqrt(self.periods_per_year) * excess_returns.mean() / downside_std
    
    def max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: Portfolio value over time
        
        Returns:
            Maximum drawdown as negative decimal (e.g., -0.25 = -25%)
        """
        if len(equity_curve) == 0:
            return 0.0
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        return float(drawdown.min())
    
    def max_drawdown_duration(self, equity_curve: pd.Series) -> int:
        """
        Calculate maximum drawdown duration in periods.
        
        Args:
            equity_curve: Portfolio value over time
        
        Returns:
            Maximum drawdown duration
        """
        if len(equity_curve) == 0:
            return 0
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Find drawdown periods
        is_drawdown = equity_curve < running_max
        
        # Calculate duration of each drawdown
        drawdown_groups = (is_drawdown != is_drawdown.shift()).cumsum()
        
        if not is_drawdown.any():
            return 0
        
        durations = is_drawdown.groupby(drawdown_groups).sum()
        
        return int(durations.max())
    
    def calmar_ratio(
        self,
        returns: pd.Series,
        equity_curve: pd.Series
    ) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).
        
        Args:
            returns: Series of period returns
            equity_curve: Portfolio value over time
        
        Returns:
            Calmar ratio
        """
        annual_ret = self.annual_return(returns)
        max_dd = abs(self.max_drawdown(equity_curve))
        
        if max_dd == 0:
            return 0.0
        
        return annual_ret / max_dd
    
    def win_rate(self, returns: pd.Series) -> float:
        """
        Calculate win rate (percentage of positive periods).
        
        Args:
            returns: Series of period returns
        
        Returns:
            Win rate as decimal (e.g., 0.55 = 55%)
        """
        if len(returns) == 0:
            return 0.0
        
        winning_periods = (returns > 0).sum()
        return winning_periods / len(returns)
    
    def average_win(self, returns: pd.Series) -> float:
        """
        Calculate average winning return.
        
        Args:
            returns: Series of period returns
        
        Returns:
            Average win
        """
        wins = returns[returns > 0]
        
        if len(wins) == 0:
            return 0.0
        
        return float(wins.mean())
    
    def average_loss(self, returns: pd.Series) -> float:
        """
        Calculate average losing return.
        
        Args:
            returns: Series of period returns
        
        Returns:
            Average loss (positive number)
        """
        losses = returns[returns < 0]
        
        if len(losses) == 0:
            return 0.0
        
        return float(abs(losses.mean()))
    
    def win_loss_ratio(self, returns: pd.Series) -> float:
        """
        Calculate win/loss ratio.
        
        Args:
            returns: Series of period returns
        
        Returns:
            Win/loss ratio
        """
        avg_win = self.average_win(returns)
        avg_loss = self.average_loss(returns)
        
        if avg_loss == 0:
            return 0.0
        
        return avg_win / avg_loss
    
    def value_at_risk(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Series of period returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
        
        Returns:
            VaR as negative value
        """
        if len(returns) == 0:
            return 0.0
        
        return float(returns.quantile(1 - confidence_level))
    
    def conditional_value_at_risk(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        
        Average of returns below VaR threshold.
        
        Args:
            returns: Series of period returns
            confidence_level: Confidence level
        
        Returns:
            CVaR as negative value
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.value_at_risk(returns, confidence_level)
        
        # Get returns below VaR
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        return float(tail_returns.mean())
    
    def calculate_benchmark_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate benchmark comparison metrics.
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns
            risk_free_rate: Annual risk-free rate
        
        Returns:
            Dict with benchmark comparison metrics
        """
        metrics = {}
        
        # Align returns with benchmark
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        
        if len(aligned_returns) == 0 or len(aligned_benchmark) == 0:
            return {
                'alpha': 0.0,
                'beta': 0.0,
                'tracking_error': 0.0,
                'information_ratio': 0.0,
                'benchmark_correlation': 0.0,
                'excess_return': 0.0,
                'active_return': 0.0,
            }
        
        # Calculate benchmark metrics
        period_rf = (1 + risk_free_rate) ** (1 / self.periods_per_year) - 1
        
        # Excess returns (strategy and benchmark vs risk-free)
        excess_returns = aligned_returns - period_rf
        excess_benchmark = aligned_benchmark - period_rf
        
        # Beta (sensitivity to benchmark)
        if excess_benchmark.std() > 0:
            covariance = aligned_returns.cov(aligned_benchmark)
            benchmark_variance = aligned_benchmark.var()
            metrics['beta'] = float(covariance / benchmark_variance) if benchmark_variance > 0 else 0.0
        else:
            metrics['beta'] = 0.0
        
        # Alpha (excess return over what beta would predict)
        annual_strategy_return = (1 + aligned_returns).prod() ** (self.periods_per_year / len(aligned_returns)) - 1
        annual_benchmark_return = (1 + aligned_benchmark).prod() ** (self.periods_per_year / len(aligned_benchmark)) - 1
        
        expected_return = risk_free_rate + metrics['beta'] * (annual_benchmark_return - risk_free_rate)
        metrics['alpha'] = float(annual_strategy_return - expected_return)
        
        # Tracking error (volatility of excess returns)
        active_returns = aligned_returns - aligned_benchmark
        metrics['tracking_error'] = float(active_returns.std() * np.sqrt(self.periods_per_year))
        
        # Information ratio (risk-adjusted active return)
        if metrics['tracking_error'] > 0:
            metrics['information_ratio'] = float(
                active_returns.mean() * self.periods_per_year / metrics['tracking_error']
            )
        else:
            metrics['information_ratio'] = 0.0
        
        # Correlation with benchmark
        if aligned_returns.std() > 0 and aligned_benchmark.std() > 0:
            metrics['benchmark_correlation'] = float(aligned_returns.corr(aligned_benchmark))
        else:
            metrics['benchmark_correlation'] = 0.0
        
        # Excess return (cumulative)
        metrics['excess_return'] = float((1 + aligned_returns).prod() - (1 + aligned_benchmark).prod())
        
        # Active return (annualized difference)
        metrics['active_return'] = float(annual_strategy_return - annual_benchmark_return)
        
        # Up/down capture ratios
        up_periods = aligned_benchmark > 0
        down_periods = aligned_benchmark < 0
        
        if up_periods.sum() > 0:
            up_strategy = aligned_returns[up_periods].mean()
            up_benchmark = aligned_benchmark[up_periods].mean()
            metrics['up_capture'] = float(up_strategy / up_benchmark) if up_benchmark != 0 else 0.0
        else:
            metrics['up_capture'] = 0.0
        
        if down_periods.sum() > 0:
            down_strategy = aligned_returns[down_periods].mean()
            down_benchmark = aligned_benchmark[down_periods].mean()
            metrics['down_capture'] = float(down_strategy / down_benchmark) if down_benchmark != 0 else 0.0
        else:
            metrics['down_capture'] = 0.0
        
        return metrics
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary."""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'annual_volatility': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_duration': 0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'win_loss_ratio': 0.0,
            'best_day': 0.0,
            'worst_day': 0.0,
            'num_periods': 0,
        }
    
    def print_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Print metrics in a formatted way.
        
        Args:
            metrics: Dictionary of metrics
        """
        print("\n" + "=" * 60)
        print("PERFORMANCE METRICS")
        print("=" * 60)
        
        print("\nReturn Metrics:")
        print(f"  Total Return:        {metrics['total_return']:>10.2%}")
        print(f"  Annual Return:       {metrics['annual_return']:>10.2%}")
        print(f"  Annual Volatility:   {metrics['annual_volatility']:>10.2%}")
        
        print("\nRisk Metrics:")
        print(f"  Maximum Drawdown:    {metrics['max_drawdown']:>10.2%}")
        print(f"  Max DD Duration:     {metrics['max_drawdown_duration']:>10.0f} periods")
        
        print("\nRisk-Adjusted Metrics:")
        print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:>10.2f}")
        print(f"  Sortino Ratio:       {metrics['sortino_ratio']:>10.2f}")
        print(f"  Calmar Ratio:        {metrics['calmar_ratio']:>10.2f}")
        
        print("\nWin Rate Metrics:")
        print(f"  Win Rate:            {metrics['win_rate']:>10.2%}")
        print(f"  Average Win:         {metrics['avg_win']:>10.2%}")
        print(f"  Average Loss:        {metrics['avg_loss']:>10.2%}")
        print(f"  Win/Loss Ratio:      {metrics['win_loss_ratio']:>10.2f}")
        
        print("\nExtreme Values:")
        print(f"  Best Period:         {metrics['best_day']:>10.2%}")
        print(f"  Worst Period:        {metrics['worst_day']:>10.2%}")
        
        print("\n" + "=" * 60)
