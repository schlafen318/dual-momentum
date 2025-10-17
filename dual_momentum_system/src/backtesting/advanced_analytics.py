"""
Advanced analytics for backtesting results.

Provides sophisticated analysis including:
- Rolling performance statistics
- Monte Carlo simulation
- Regime analysis
- Factor exposure
- Correlation analysis
"""

from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from scipy import stats
from loguru import logger

try:
    import vectorbt as vbt
except ImportError:
    vbt = None
    logger.warning("vectorbt not available")


class AdvancedAnalytics:
    """
    Advanced analytics suite for backtest results.
    
    Provides comprehensive analysis tools including:
    - Rolling statistics and metrics
    - Monte Carlo simulation for strategy robustness
    - Regime detection and analysis
    - Drawdown analysis
    - Risk decomposition
    
    Example:
        >>> analytics = AdvancedAnalytics()
        >>> rolling_stats = analytics.calculate_rolling_metrics(
        ...     returns=returns,
        ...     window=252
        ... )
        >>> mc_results = analytics.monte_carlo_simulation(
        ...     returns=returns,
        ...     num_simulations=1000
        ... )
    """
    
    def __init__(self, freq: str = 'D'):
        """
        Initialize analytics.
        
        Args:
            freq: Data frequency ('D', 'H', 'T', 'S')
        """
        self.freq = freq
        
        # Determine periods per year
        freq_map = {
            'D': 252, 'H': 252 * 6.5, 'T': 252 * 6.5 * 60,
            'S': 252 * 6.5 * 60 * 60, 'W': 52, 'M': 12, 'Q': 4, 'Y': 1
        }
        self.periods_per_year = freq_map.get(freq, 252)
    
    def calculate_rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 252,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            returns: Series of period returns
            window: Rolling window size
            metrics: List of metrics to calculate. If None, calculates all.
                    Options: 'return', 'volatility', 'sharpe', 'sortino',
                    'max_drawdown', 'win_rate', 'skewness', 'kurtosis'
        
        Returns:
            DataFrame with rolling metrics
        """
        logger.info(f"Calculating rolling metrics with window={window}")
        
        if metrics is None:
            metrics = [
                'return', 'volatility', 'sharpe', 'sortino',
                'max_drawdown', 'win_rate', 'skewness', 'kurtosis'
            ]
        
        rolling_data = {}
        
        if 'return' in metrics:
            # Rolling annualized return
            rolling_return = (
                (1 + returns).rolling(window).apply(lambda x: x.prod(), raw=True)
                ** (self.periods_per_year / window) - 1
            )
            rolling_data['rolling_return'] = rolling_return
        
        if 'volatility' in metrics:
            # Rolling annualized volatility
            rolling_vol = (
                returns.rolling(window).std() * np.sqrt(self.periods_per_year)
            )
            rolling_data['rolling_volatility'] = rolling_vol
        
        if 'sharpe' in metrics:
            # Rolling Sharpe ratio
            rolling_mean = returns.rolling(window).mean()
            rolling_std = returns.rolling(window).std()
            rolling_sharpe = (
                rolling_mean / rolling_std * np.sqrt(self.periods_per_year)
            )
            rolling_data['rolling_sharpe'] = rolling_sharpe
        
        if 'sortino' in metrics:
            # Rolling Sortino ratio
            def sortino_calc(x):
                if len(x) < 2:
                    return np.nan
                downside = x[x < 0]
                if len(downside) == 0 or downside.std() == 0:
                    return np.nan
                return x.mean() / downside.std() * np.sqrt(self.periods_per_year)
            
            rolling_sortino = returns.rolling(window).apply(sortino_calc, raw=False)
            rolling_data['rolling_sortino'] = rolling_sortino
        
        if 'max_drawdown' in metrics:
            # Rolling maximum drawdown
            def max_dd_calc(x):
                if len(x) < 2:
                    return np.nan
                cum_returns = (1 + x).cumprod()
                running_max = np.maximum.accumulate(cum_returns)
                drawdown = (cum_returns - running_max) / running_max
                return drawdown.min()
            
            rolling_mdd = returns.rolling(window).apply(max_dd_calc, raw=False)
            rolling_data['rolling_max_drawdown'] = rolling_mdd
        
        if 'win_rate' in metrics:
            # Rolling win rate
            rolling_win_rate = (
                (returns > 0).rolling(window).mean()
            )
            rolling_data['rolling_win_rate'] = rolling_win_rate
        
        if 'skewness' in metrics:
            # Rolling skewness
            rolling_skew = returns.rolling(window).skew()
            rolling_data['rolling_skewness'] = rolling_skew
        
        if 'kurtosis' in metrics:
            # Rolling kurtosis
            rolling_kurt = returns.rolling(window).kurt()
            rolling_data['rolling_kurtosis'] = rolling_kurt
        
        return pd.DataFrame(rolling_data)
    
    def monte_carlo_simulation(
        self,
        returns: pd.Series,
        num_simulations: int = 1000,
        num_periods: Optional[int] = None,
        method: str = 'bootstrap',
        confidence_levels: List[float] = [0.05, 0.25, 0.50, 0.75, 0.95]
    ) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        Perform Monte Carlo simulation on returns.
        
        Args:
            returns: Historical returns
            num_simulations: Number of simulation paths
            num_periods: Number of periods to simulate (default: same as returns)
            method: Simulation method:
                   - 'bootstrap': Resample from historical returns
                   - 'parametric': Use normal distribution with historical mean/std
                   - 'parametric_t': Use t-distribution
            confidence_levels: Confidence levels for percentile calculation
        
        Returns:
            Dictionary containing:
            - 'paths': DataFrame of simulated equity curves
            - 'final_values': Array of final portfolio values
            - 'percentiles': Dict of percentile paths
            - 'statistics': Summary statistics
        """
        logger.info(
            f"Running Monte Carlo simulation: {num_simulations} paths, "
            f"method={method}"
        )
        
        if num_periods is None:
            num_periods = len(returns)
        
        # Initialize array for simulated returns
        simulated_returns = np.zeros((num_periods, num_simulations))
        
        if method == 'bootstrap':
            # Bootstrap resampling
            for i in range(num_simulations):
                simulated_returns[:, i] = np.random.choice(
                    returns.values,
                    size=num_periods,
                    replace=True
                )
        
        elif method == 'parametric':
            # Parametric simulation using normal distribution
            mean_return = returns.mean()
            std_return = returns.std()
            
            simulated_returns = np.random.normal(
                mean_return,
                std_return,
                size=(num_periods, num_simulations)
            )
        
        elif method == 'parametric_t':
            # Parametric simulation using t-distribution
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Fit t-distribution
            params = stats.t.fit(returns.values)
            df, loc, scale = params
            
            simulated_returns = stats.t.rvs(
                df,
                loc=loc,
                scale=scale,
                size=(num_periods, num_simulations)
            )
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Calculate equity curves
        equity_curves = np.cumprod(1 + simulated_returns, axis=0)
        
        # Create DataFrame for paths
        paths_df = pd.DataFrame(
            equity_curves,
            columns=[f'sim_{i}' for i in range(num_simulations)]
        )
        
        # Calculate percentiles
        percentiles = {}
        for conf in confidence_levels:
            percentiles[f'p{int(conf*100)}'] = np.percentile(
                equity_curves,
                conf * 100,
                axis=1
            )
        
        percentiles_df = pd.DataFrame(percentiles)
        
        # Calculate final values
        final_values = equity_curves[-1, :]
        
        # Calculate statistics
        statistics = {
            'mean_final_value': float(np.mean(final_values)),
            'median_final_value': float(np.median(final_values)),
            'std_final_value': float(np.std(final_values)),
            'min_final_value': float(np.min(final_values)),
            'max_final_value': float(np.max(final_values)),
            'probability_positive': float(np.mean(final_values > 1.0)),
            'expected_return': float(np.mean(final_values) - 1.0),
            'expected_cagr': float(np.mean(final_values) ** (
                self.periods_per_year / num_periods
            ) - 1),
        }
        
        # Calculate VaR and CVaR
        for conf in [0.95, 0.99]:
            var_level = 1 - conf
            var = np.percentile(final_values, var_level * 100)
            statistics[f'var_{int(conf*100)}'] = float(var - 1.0)
            
            # CVaR (average of values below VaR)
            tail_values = final_values[final_values <= var]
            if len(tail_values) > 0:
                cvar = np.mean(tail_values)
                statistics[f'cvar_{int(conf*100)}'] = float(cvar - 1.0)
        
        logger.info(
            f"Monte Carlo complete: Mean final={statistics['mean_final_value']:.4f}, "
            f"Prob(positive)={statistics['probability_positive']:.2%}"
        )
        
        return {
            'paths': paths_df,
            'percentiles': percentiles_df,
            'final_values': final_values,
            'statistics': statistics
        }
    
    def detect_regimes(
        self,
        returns: pd.Series,
        method: str = 'volatility',
        n_regimes: int = 2,
        **kwargs
    ) -> pd.Series:
        """
        Detect market regimes.
        
        Args:
            returns: Return series
            method: Detection method:
                   - 'volatility': High/low volatility regimes
                   - 'trend': Bull/bear market regimes
                   - 'hmm': Hidden Markov Model (requires hmmlearn)
                   - 'percentile': Based on return percentiles
            n_regimes: Number of regimes (2 for bull/bear, 3 for bull/neutral/bear)
            **kwargs: Method-specific parameters
        
        Returns:
            Series with regime labels (0, 1, 2, ...)
        """
        logger.info(f"Detecting regimes using method={method}")
        
        if method == 'volatility':
            return self._detect_volatility_regimes(returns, n_regimes, **kwargs)
        elif method == 'trend':
            return self._detect_trend_regimes(returns, n_regimes, **kwargs)
        elif method == 'hmm':
            return self._detect_hmm_regimes(returns, n_regimes, **kwargs)
        elif method == 'percentile':
            return self._detect_percentile_regimes(returns, n_regimes, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _detect_volatility_regimes(
        self,
        returns: pd.Series,
        n_regimes: int = 2,
        window: int = 20
    ) -> pd.Series:
        """Detect regimes based on volatility."""
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=window).std()
        
        # Create regime labels based on percentiles
        if n_regimes == 2:
            median_vol = rolling_vol.median()
            regimes = (rolling_vol > median_vol).astype(int)
        else:
            percentiles = np.linspace(0, 100, n_regimes + 1)[1:-1]
            thresholds = np.percentile(rolling_vol.dropna(), percentiles)
            regimes = pd.Series(0, index=returns.index)
            for i, threshold in enumerate(thresholds, 1):
                regimes[rolling_vol > threshold] = i
        
        return regimes
    
    def _detect_trend_regimes(
        self,
        returns: pd.Series,
        n_regimes: int = 2,
        window: int = 50
    ) -> pd.Series:
        """Detect regimes based on trend."""
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()
        
        # Calculate moving average
        ma = cum_returns.rolling(window=window).mean()
        
        # Trend indicator
        trend = cum_returns - ma
        
        # Create regime labels
        if n_regimes == 2:
            regimes = (trend > 0).astype(int)
        else:
            percentiles = np.linspace(0, 100, n_regimes + 1)[1:-1]
            thresholds = np.percentile(trend.dropna(), percentiles)
            regimes = pd.Series(0, index=returns.index)
            for i, threshold in enumerate(thresholds, 1):
                regimes[trend > threshold] = i
        
        return regimes
    
    def _detect_hmm_regimes(
        self,
        returns: pd.Series,
        n_regimes: int = 2,
        **kwargs
    ) -> pd.Series:
        """Detect regimes using Hidden Markov Model."""
        try:
            from hmmlearn import hmm
        except ImportError:
            logger.warning("hmmlearn not available, falling back to volatility method")
            return self._detect_volatility_regimes(returns, n_regimes)
        
        # Prepare data
        X = returns.values.reshape(-1, 1)
        
        # Fit HMM
        model = hmm.GaussianHMM(
            n_components=n_regimes,
            covariance_type='full',
            n_iter=100,
            random_state=42
        )
        
        model.fit(X)
        regimes = model.predict(X)
        
        return pd.Series(regimes, index=returns.index)
    
    def _detect_percentile_regimes(
        self,
        returns: pd.Series,
        n_regimes: int = 3,
        window: int = 20
    ) -> pd.Series:
        """Detect regimes based on return percentiles."""
        # Calculate rolling returns
        rolling_returns = returns.rolling(window=window).mean()
        
        # Create regime labels based on percentiles
        percentiles = np.linspace(0, 100, n_regimes + 1)[1:-1]
        thresholds = np.percentile(rolling_returns.dropna(), percentiles)
        
        regimes = pd.Series(0, index=returns.index)
        for i, threshold in enumerate(thresholds, 1):
            regimes[rolling_returns > threshold] = i
        
        return regimes
    
    def analyze_regimes(
        self,
        returns: pd.Series,
        regimes: pd.Series
    ) -> pd.DataFrame:
        """
        Analyze performance by regime.
        
        Args:
            returns: Return series
            regimes: Regime labels
        
        Returns:
            DataFrame with regime statistics
        """
        logger.info("Analyzing regime performance")
        
        # Align data
        data = pd.DataFrame({'returns': returns, 'regime': regimes})
        data = data.dropna()
        
        # Calculate statistics for each regime
        regime_stats = []
        
        for regime in sorted(data['regime'].unique()):
            regime_returns = data[data['regime'] == regime]['returns']
            
            stats = {
                'regime': regime,
                'count': len(regime_returns),
                'frequency': len(regime_returns) / len(data),
                'mean_return': regime_returns.mean(),
                'annual_return': (
                    (1 + regime_returns.mean()) ** self.periods_per_year - 1
                ),
                'volatility': regime_returns.std() * np.sqrt(self.periods_per_year),
                'sharpe': (
                    regime_returns.mean() / regime_returns.std() *
                    np.sqrt(self.periods_per_year)
                    if regime_returns.std() > 0 else 0
                ),
                'win_rate': (regime_returns > 0).mean(),
                'best_return': regime_returns.max(),
                'worst_return': regime_returns.min(),
                'skewness': regime_returns.skew(),
                'kurtosis': regime_returns.kurtosis()
            }
            
            regime_stats.append(stats)
        
        return pd.DataFrame(regime_stats)
    
    def calculate_drawdown_analysis(
        self,
        equity_curve: pd.Series,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Detailed drawdown analysis.
        
        Args:
            equity_curve: Portfolio values
            top_n: Number of top drawdowns to analyze
        
        Returns:
            DataFrame with drawdown details
        """
        logger.info(f"Analyzing top {top_n} drawdowns")
        
        # Calculate drawdown series
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        
        # Identify drawdown periods
        in_drawdown = drawdown < 0
        dd_groups = (in_drawdown != in_drawdown.shift()).cumsum()
        
        # Analyze each drawdown period
        drawdown_list = []
        
        for group in dd_groups[in_drawdown].unique():
            dd_period = drawdown[dd_groups == group]
            
            if len(dd_period) == 0:
                continue
            
            # Find peak, trough, and recovery
            start_idx = dd_period.index[0]
            trough_idx = dd_period.idxmin()
            
            # Find recovery (if exists)
            recovery_idx = None
            peak_value = equity_curve.loc[start_idx]
            
            future_values = equity_curve.loc[trough_idx:]
            recovery_points = future_values[future_values >= peak_value]
            
            if len(recovery_points) > 0:
                recovery_idx = recovery_points.index[0]
                recovery_time = (recovery_idx - trough_idx).days
            else:
                recovery_idx = equity_curve.index[-1]
                recovery_time = None  # Still in drawdown
            
            drawdown_info = {
                'start_date': start_idx,
                'trough_date': trough_idx,
                'recovery_date': recovery_idx,
                'depth': dd_period.min(),
                'length_days': (trough_idx - start_idx).days,
                'recovery_days': recovery_time,
                'total_days': (recovery_idx - start_idx).days if recovery_time else None,
                'peak_value': peak_value,
                'trough_value': equity_curve.loc[trough_idx],
                'recovered': recovery_time is not None
            }
            
            drawdown_list.append(drawdown_info)
        
        # Convert to DataFrame and sort by depth
        dd_df = pd.DataFrame(drawdown_list)
        
        if len(dd_df) > 0:
            dd_df = dd_df.sort_values('depth').head(top_n)
        
        return dd_df
    
    def calculate_rolling_correlation(
        self,
        returns1: pd.Series,
        returns2: pd.Series,
        window: int = 252
    ) -> pd.Series:
        """
        Calculate rolling correlation between two return series.
        
        Args:
            returns1: First return series
            returns2: Second return series
            window: Rolling window size
        
        Returns:
            Series of rolling correlations
        """
        # Align series
        aligned = pd.DataFrame({
            'r1': returns1,
            'r2': returns2
        }).dropna()
        
        # Calculate rolling correlation
        rolling_corr = aligned['r1'].rolling(window).corr(aligned['r2'])
        
        return rolling_corr
    
    def calculate_stress_tests(
        self,
        returns: pd.Series,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None
    ) -> pd.DataFrame:
        """
        Perform stress testing on portfolio returns.
        
        Args:
            returns: Return series
            scenarios: Dict of scenario definitions with 'shock' and 'duration'
                      If None, uses default crisis scenarios
        
        Returns:
            DataFrame with stress test results
        """
        if scenarios is None:
            # Default crisis scenarios
            scenarios = {
                '2008_crisis': {'shock': -0.50, 'duration': 252},
                'flash_crash': {'shock': -0.10, 'duration': 1},
                'moderate_correction': {'shock': -0.20, 'duration': 60},
                'severe_bear': {'shock': -0.40, 'duration': 504}
            }
        
        results = []
        
        for scenario_name, params in scenarios.items():
            shock = params['shock']
            duration = params.get('duration', 1)
            
            # Apply shock to returns
            stressed_returns = returns.copy()
            shock_per_period = shock / duration
            
            # Simulate shocked returns
            shocked_equity = (1 + stressed_returns).cumprod()
            final_value = shocked_equity.iloc[-1] * (1 + shock)
            
            # Calculate metrics under stress
            max_dd = (shocked_equity / shocked_equity.expanding().max() - 1).min()
            
            results.append({
                'scenario': scenario_name,
                'shock': shock,
                'duration': duration,
                'final_value': final_value,
                'total_loss': final_value - shocked_equity.iloc[-1],
                'max_drawdown': max_dd
            })
        
        return pd.DataFrame(results)
    
    def calculate_performance_attribution(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate performance attribution vs benchmark.
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns
        
        Returns:
            Dictionary with attribution metrics
        """
        # Align returns
        aligned = pd.DataFrame({
            'strategy': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        strategy_ret = aligned['strategy']
        benchmark_ret = aligned['benchmark']
        
        # Calculate metrics
        total_strategy = (1 + strategy_ret).prod() - 1
        total_benchmark = (1 + benchmark_ret).prod() - 1
        
        # Alpha
        excess_returns = strategy_ret - benchmark_ret
        alpha = excess_returns.mean() * self.periods_per_year
        
        # Beta
        covariance = np.cov(strategy_ret, benchmark_ret)[0, 1]
        benchmark_var = np.var(benchmark_ret)
        beta = covariance / benchmark_var if benchmark_var > 0 else 0
        
        # Information ratio
        tracking_error = excess_returns.std() * np.sqrt(self.periods_per_year)
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0
        
        # Active return
        active_return = total_strategy - total_benchmark
        
        return {
            'total_strategy_return': total_strategy,
            'total_benchmark_return': total_benchmark,
            'active_return': active_return,
            'alpha': alpha,
            'beta': beta,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'correlation': strategy_ret.corr(benchmark_ret)
        }
