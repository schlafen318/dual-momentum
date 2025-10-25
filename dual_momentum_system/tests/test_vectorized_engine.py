"""
Unit tests for vectorized backtesting engine.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import vectorized components (requires vectorbt/numba)
try:
    from src.backtesting.vectorized_engine import (
        VectorizedBacktestEngine,
        SignalGenerator
    )
    from src.backtesting.vectorized_metrics import VectorizedMetricsCalculator
    from src.backtesting.advanced_analytics import AdvancedAnalytics
    VECTORBT_AVAILABLE = True
except (ImportError, SystemError) as e:
    # Skip tests if vectorbt/numba not available or incompatible
    VECTORBT_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason=f"vectorbt/numba not available: {e}")


@pytest.fixture
def sample_prices():
    """Generate sample price data for testing."""
    dates = pd.date_range('2020-01-01', '2022-12-31', freq='B')
    np.random.seed(42)
    
    prices = pd.DataFrame({
        'ASSET_A': 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.01, len(dates)))),
        'ASSET_B': 100 * np.exp(np.cumsum(np.random.normal(0.0003, 0.015, len(dates)))),
        'ASSET_C': 100 * np.exp(np.cumsum(np.random.normal(0.0007, 0.012, len(dates)))),
    }, index=dates)
    
    return prices


@pytest.fixture
def sample_returns():
    """Generate sample returns for testing."""
    dates = pd.date_range('2020-01-01', '2022-12-31', freq='B')
    np.random.seed(42)
    
    returns = pd.Series(
        np.random.normal(0.0005, 0.01, len(dates)),
        index=dates
    )
    
    return returns


class TestVectorizedBacktestEngine:
    """Test VectorizedBacktestEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = VectorizedBacktestEngine(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005
        )
        
        assert engine.initial_capital == 100000
        assert engine.commission == 0.001
        assert engine.slippage == 0.0005
    
    def test_run_backtest_basic(self, sample_prices):
        """Test basic backtest execution."""
        engine = VectorizedBacktestEngine(initial_capital=100000)
        
        # Create simple signals (equal weight)
        signals = pd.DataFrame(
            0.33,
            index=sample_prices.index,
            columns=sample_prices.columns
        )
        
        results = engine.run_backtest(
            price_data=sample_prices,
            signals=signals,
            size_type='percent'
        )
        
        assert results is not None
        assert results.initial_capital == 100000
        assert results.final_capital > 0
        assert 'sharpe_ratio' in results.metrics
        assert 'max_drawdown' in results.metrics
        assert len(results.equity_curve) > 0
    
    @pytest.mark.skip(reason="Known issue: NaN cash value with zero signals (vectorbt bug)")
    def test_run_backtest_with_zero_signals(self, sample_prices):
        """Test backtest with zero signals (no trading)."""
        engine = VectorizedBacktestEngine(initial_capital=100000)
        
        # Zero signals (no positions)
        signals = pd.DataFrame(
            0.0,
            index=sample_prices.index,
            columns=sample_prices.columns
        )
        
        results = engine.run_backtest(
            price_data=sample_prices,
            signals=signals
        )
        
        # Should stay at initial capital
        assert abs(results.final_capital - 100000) < 100  # Allow for small rounding
    
    def test_run_signal_strategy(self, sample_prices):
        """Test signal-based strategy."""
        engine = VectorizedBacktestEngine(initial_capital=50000)
        
        # Create simple entry/exit signals
        entries = sample_prices.pct_change(10) > 0.02
        exits = sample_prices.pct_change(10) < -0.02
        
        results = engine.run_signal_strategy(
            price_data=sample_prices,
            entries=entries,
            exits=exits,
            size=0.5
        )
        
        assert results is not None
        assert results.initial_capital == 50000
        assert 'sharpe_ratio' in results.metrics
    
    def test_prepare_price_data_from_dataframe(self, sample_prices):
        """Test price data preparation from DataFrame."""
        engine = VectorizedBacktestEngine()
        
        prepared = engine._prepare_price_data(sample_prices)
        
        assert isinstance(prepared, pd.DataFrame)
        assert prepared.shape == sample_prices.shape
    
    def test_multi_strategy_comparison(self, sample_prices):
        """Test multi-strategy comparison."""
        engine = VectorizedBacktestEngine(initial_capital=100000)
        
        strategies = {
            'Strategy_A': pd.DataFrame(
                0.5, index=sample_prices.index, columns=sample_prices.columns
            ),
            'Strategy_B': pd.DataFrame(
                0.33, index=sample_prices.index, columns=sample_prices.columns
            )
        }
        
        results = engine.run_multi_strategy_comparison(
            price_data=sample_prices,
            strategies=strategies
        )
        
        assert len(results) == 2
        assert 'Strategy_A' in results
        assert 'Strategy_B' in results
        assert all(r.metrics['sharpe_ratio'] is not None for r in results.values())


class TestSignalGenerator:
    """Test SignalGenerator class."""
    
    def test_momentum_signals(self, sample_prices):
        """Test momentum signal generation."""
        signals = SignalGenerator.momentum_signals(
            sample_prices,
            lookback=50,
            top_n=2,
            normalize=True
        )
        
        assert isinstance(signals, pd.DataFrame)
        assert signals.shape == sample_prices.shape
        
        # Check that signals are normalized (sum to ~1 where non-zero)
        row_sums = signals.sum(axis=1)
        non_zero_rows = row_sums[row_sums > 0]
        assert all(abs(non_zero_rows - 1.0) < 0.01)
    
    def test_sma_crossover_signals(self, sample_prices):
        """Test SMA crossover signal generation."""
        entries, exits = SignalGenerator.sma_crossover_signals(
            sample_prices,
            fast_window=20,
            slow_window=50
        )
        
        assert isinstance(entries, pd.DataFrame)
        assert isinstance(exits, pd.DataFrame)
        assert entries.shape == sample_prices.shape
        assert exits.shape == sample_prices.shape
        
        # Check that signals are boolean
        assert entries.dtypes.all() == bool or entries.dtypes.all() == np.bool_
    
    def test_mean_reversion_signals(self, sample_prices):
        """Test mean reversion signal generation."""
        entries, exits = SignalGenerator.mean_reversion_signals(
            sample_prices,
            window=20,
            entry_std=2.0,
            exit_std=0.5
        )
        
        assert isinstance(entries, pd.DataFrame)
        assert isinstance(exits, pd.DataFrame)
        assert entries.shape == sample_prices.shape
    
    def test_equal_weight_signals(self, sample_prices):
        """Test equal weight signal generation."""
        signals = SignalGenerator.equal_weight_signals(
            sample_prices,
            rebalance_freq='M'
        )
        
        assert isinstance(signals, pd.DataFrame)
        assert signals.shape == sample_prices.shape
        
        # Check that weights are equal when rebalancing
        n_assets = len(sample_prices.columns)
        expected_weight = 1.0 / n_assets
        
        # Find rebalance dates
        rebalance_rows = signals[signals.sum(axis=1) > 0]
        
        for _, row in rebalance_rows.iterrows():
            non_zero = row[row > 0]
            assert all(abs(non_zero - expected_weight) < 0.01)


class TestVectorizedMetricsCalculator:
    """Test VectorizedMetricsCalculator class."""
    
    def test_calculator_initialization(self):
        """Test calculator initialization."""
        calc = VectorizedMetricsCalculator(freq='D')
        
        assert calc.freq == 'D'
        assert calc.periods_per_year == 252
    
    def test_calculate_all_metrics(self, sample_returns):
        """Test comprehensive metrics calculation."""
        equity = (1 + sample_returns).cumprod() * 100000
        
        calc = VectorizedMetricsCalculator(freq='D')
        metrics = calc.calculate_all_metrics(
            returns=sample_returns,
            equity_curve=equity
        )
        
        # Check that all key metrics are present
        required_metrics = [
            'total_return', 'cagr', 'annual_volatility',
            'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
            'calmar_ratio'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
            assert metrics[metric] is not None
    
    def test_calculate_cagr(self, sample_returns):
        """Test CAGR calculation."""
        equity = (1 + sample_returns).cumprod() * 100000
        
        calc = VectorizedMetricsCalculator(freq='D')
        cagr = calc.calculate_cagr(equity)
        
        assert isinstance(cagr, float)
        assert -1.0 <= cagr <= 5.0  # Reasonable range
    
    def test_calculate_sharpe_ratio(self, sample_returns):
        """Test Sharpe ratio calculation."""
        calc = VectorizedMetricsCalculator(freq='D')
        sharpe = calc.calculate_sharpe_ratio(sample_returns, risk_free_rate=0.02)
        
        assert isinstance(sharpe, float)
        assert -5.0 <= sharpe <= 10.0  # Reasonable range
    
    def test_calculate_drawdown_metrics(self, sample_returns):
        """Test drawdown metrics calculation."""
        equity = (1 + sample_returns).cumprod() * 100000
        
        calc = VectorizedMetricsCalculator(freq='D')
        dd_metrics = calc.calculate_drawdown_metrics(equity)
        
        assert 'max_drawdown' in dd_metrics
        assert 'avg_drawdown' in dd_metrics
        assert 'max_drawdown_duration' in dd_metrics
        assert dd_metrics['max_drawdown'] <= 0  # Should be negative
    
    def test_calculate_var_cvar(self, sample_returns):
        """Test VaR and CVaR calculation."""
        calc = VectorizedMetricsCalculator(freq='D')
        
        var_95 = calc.calculate_var(sample_returns, confidence=0.95)
        cvar_95 = calc.calculate_cvar(sample_returns, confidence=0.95)
        
        assert isinstance(var_95, float)
        assert isinstance(cvar_95, float)
        # CVaR should be worse (more negative) than VaR
        assert cvar_95 <= var_95
    
    def test_empty_returns(self):
        """Test handling of empty returns."""
        calc = VectorizedMetricsCalculator(freq='D')
        
        empty_returns = pd.Series([], dtype=float)
        empty_equity = pd.Series([], dtype=float)
        
        metrics = calc.calculate_all_metrics(empty_returns, empty_equity)
        
        # Should return zero metrics without errors
        assert metrics['total_return'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0


class TestAdvancedAnalytics:
    """Test AdvancedAnalytics class."""
    
    def test_analytics_initialization(self):
        """Test analytics initialization."""
        analytics = AdvancedAnalytics(freq='D')
        
        assert analytics.freq == 'D'
        assert analytics.periods_per_year == 252
    
    def test_calculate_rolling_metrics(self, sample_returns):
        """Test rolling metrics calculation."""
        analytics = AdvancedAnalytics(freq='D')
        
        rolling_stats = analytics.calculate_rolling_metrics(
            sample_returns,
            window=50,
            metrics=['return', 'volatility', 'sharpe']
        )
        
        assert isinstance(rolling_stats, pd.DataFrame)
        assert 'rolling_return' in rolling_stats.columns
        assert 'rolling_volatility' in rolling_stats.columns
        assert 'rolling_sharpe' in rolling_stats.columns
        assert len(rolling_stats) == len(sample_returns)
    
    def test_monte_carlo_simulation(self, sample_returns):
        """Test Monte Carlo simulation."""
        analytics = AdvancedAnalytics(freq='D')
        
        mc_results = analytics.monte_carlo_simulation(
            sample_returns,
            num_simulations=100,
            num_periods=100,
            method='bootstrap'
        )
        
        assert 'paths' in mc_results
        assert 'percentiles' in mc_results
        assert 'final_values' in mc_results
        assert 'statistics' in mc_results
        
        assert mc_results['paths'].shape[1] == 100  # 100 simulations
        assert len(mc_results['final_values']) == 100
        
        stats = mc_results['statistics']
        assert 'mean_final_value' in stats
        assert 'probability_positive' in stats
        assert 0 <= stats['probability_positive'] <= 1
    
    def test_monte_carlo_parametric(self, sample_returns):
        """Test parametric Monte Carlo."""
        analytics = AdvancedAnalytics(freq='D')
        
        mc_results = analytics.monte_carlo_simulation(
            sample_returns,
            num_simulations=100,
            method='parametric'
        )
        
        assert 'statistics' in mc_results
        assert mc_results['statistics']['mean_final_value'] > 0
    
    def test_detect_regimes_volatility(self, sample_returns):
        """Test volatility-based regime detection."""
        analytics = AdvancedAnalytics(freq='D')
        
        regimes = analytics.detect_regimes(
            sample_returns,
            method='volatility',
            n_regimes=2,
            window=20
        )
        
        assert isinstance(regimes, pd.Series)
        assert len(regimes) == len(sample_returns)
        assert set(regimes.unique()).issubset({0, 1})
    
    def test_detect_regimes_trend(self, sample_returns):
        """Test trend-based regime detection."""
        analytics = AdvancedAnalytics(freq='D')
        
        regimes = analytics.detect_regimes(
            sample_returns,
            method='trend',
            n_regimes=2,
            window=50
        )
        
        assert isinstance(regimes, pd.Series)
        assert len(regimes) == len(sample_returns)
    
    def test_analyze_regimes(self, sample_returns):
        """Test regime analysis."""
        analytics = AdvancedAnalytics(freq='D')
        
        # Detect regimes first
        regimes = analytics.detect_regimes(
            sample_returns,
            method='volatility',
            n_regimes=2
        )
        
        # Analyze regimes
        regime_analysis = analytics.analyze_regimes(sample_returns, regimes)
        
        assert isinstance(regime_analysis, pd.DataFrame)
        assert len(regime_analysis) == 2  # 2 regimes
        assert 'mean_return' in regime_analysis.columns
        assert 'volatility' in regime_analysis.columns
        assert 'sharpe' in regime_analysis.columns
    
    def test_calculate_drawdown_analysis(self, sample_returns):
        """Test drawdown analysis."""
        equity = (1 + sample_returns).cumprod() * 100000
        
        analytics = AdvancedAnalytics(freq='D')
        dd_analysis = analytics.calculate_drawdown_analysis(equity, top_n=3)
        
        assert isinstance(dd_analysis, pd.DataFrame)
        
        if len(dd_analysis) > 0:
            assert 'depth' in dd_analysis.columns
            assert 'start_date' in dd_analysis.columns
            assert 'trough_date' in dd_analysis.columns
            assert all(dd_analysis['depth'] <= 0)
    
    def test_calculate_rolling_correlation(self, sample_returns):
        """Test rolling correlation calculation."""
        # Create second return series
        returns2 = sample_returns + np.random.normal(0, 0.005, len(sample_returns))
        
        analytics = AdvancedAnalytics(freq='D')
        rolling_corr = analytics.calculate_rolling_correlation(
            sample_returns,
            returns2,
            window=50
        )
        
        assert isinstance(rolling_corr, pd.Series)
        assert all(abs(rolling_corr.dropna()) <= 1.0)
    
    def test_calculate_stress_tests(self, sample_returns):
        """Test stress testing."""
        analytics = AdvancedAnalytics(freq='D')
        
        stress_results = analytics.calculate_stress_tests(sample_returns)
        
        assert isinstance(stress_results, pd.DataFrame)
        assert len(stress_results) > 0
        assert 'scenario' in stress_results.columns
        assert 'shock' in stress_results.columns
        assert 'final_value' in stress_results.columns
    
    def test_performance_attribution(self, sample_returns):
        """Test performance attribution."""
        # Create benchmark returns
        benchmark_returns = sample_returns * 0.8 + np.random.normal(0, 0.005, len(sample_returns))
        
        analytics = AdvancedAnalytics(freq='D')
        attribution = analytics.calculate_performance_attribution(
            sample_returns,
            benchmark_returns
        )
        
        assert isinstance(attribution, dict)
        assert 'alpha' in attribution
        assert 'beta' in attribution
        assert 'information_ratio' in attribution
        assert 'tracking_error' in attribution


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.skip(reason="Known issue: NaN cash value (vectorbt bug)")
    def test_complete_backtest_workflow(self, sample_prices):
        """Test complete backtest workflow from start to finish."""
        # 1. Create engine
        engine = VectorizedBacktestEngine(
            initial_capital=100000,
            commission=0.001
        )
        
        # 2. Generate signals
        signals = SignalGenerator.momentum_signals(
            sample_prices,
            lookback=50,
            top_n=2
        )
        
        # 3. Run backtest
        results = engine.run_backtest(sample_prices, signals)
        
        # 4. Verify results
        assert results.total_return is not None
        assert len(results.equity_curve) > 0
        
        # 5. Calculate advanced analytics
        analytics = AdvancedAnalytics(freq='D')
        
        rolling_stats = analytics.calculate_rolling_metrics(
            results.returns,
            window=50
        )
        
        mc_results = analytics.monte_carlo_simulation(
            results.returns,
            num_simulations=100
        )
        
        regimes = analytics.detect_regimes(results.returns)
        
        # All should complete without errors
        assert rolling_stats is not None
        assert mc_results is not None
        assert regimes is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
