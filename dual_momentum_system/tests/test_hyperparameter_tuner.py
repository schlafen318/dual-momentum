"""
Tests for hyperparameter tuning functionality.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.backtesting import (
    BacktestEngine,
    HyperparameterTuner,
    ParameterSpace,
    OptimizationResult,
    MethodComparisonResult,
    create_default_param_space,
)
from src.strategies.dual_momentum import DualMomentumStrategy
from src.core.types import PriceData, AssetMetadata, AssetType


# Helper function to check if optuna is available
def _has_optuna():
    """Check if optuna is installed."""
    try:
        import optuna
        return True
    except ImportError:
        return False


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    
    # Create price data for multiple assets
    price_data = {}
    
    for symbol in ['SPY', 'EFA', 'AGG']:
        # Generate synthetic price data with trend and noise
        np.random.seed(42 if symbol == 'SPY' else 43 if symbol == 'EFA' else 44)
        trend = np.linspace(100, 150, len(dates))
        noise = np.random.randn(len(dates)) * 2
        prices = trend + noise
        prices = np.maximum(prices, 50)  # Ensure positive prices
        
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        price_data[symbol] = PriceData(
            symbol=symbol,
            data=df,
            metadata=AssetMetadata(
                symbol=symbol,
                name=f"{symbol} Test",
                asset_type=AssetType.EQUITY
            )
        )
    
    return price_data


@pytest.fixture
def backtest_engine():
    """Create a backtest engine for testing."""
    return BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005,
    )


@pytest.fixture
def hyperparameter_tuner(sample_price_data, backtest_engine):
    """Create a hyperparameter tuner for testing."""
    base_config = {
        'safe_asset': 'AGG',
        'rebalance_frequency': 'monthly',
    }
    
    return HyperparameterTuner(
        strategy_class=DualMomentumStrategy,
        backtest_engine=backtest_engine,
        price_data=sample_price_data,
        base_config=base_config,
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2023, 12, 31),
    )


class TestParameterSpace:
    """Tests for ParameterSpace class."""
    
    def test_categorical_parameter_validation(self):
        """Test categorical parameter validation."""
        # Valid categorical parameter
        ps = ParameterSpace(
            name='test_param',
            param_type='categorical',
            values=['a', 'b', 'c']
        )
        ps.validate()  # Should not raise
        
        # Invalid: no values
        ps_invalid = ParameterSpace(
            name='test_param',
            param_type='categorical'
        )
        with pytest.raises(ValueError, match="must have values"):
            ps_invalid.validate()
    
    def test_numeric_parameter_validation(self):
        """Test numeric parameter validation."""
        # Valid with min/max
        ps = ParameterSpace(
            name='test_param',
            param_type='int',
            min_value=1,
            max_value=10
        )
        ps.validate()  # Should not raise
        
        # Valid with explicit values
        ps = ParameterSpace(
            name='test_param',
            param_type='float',
            values=[0.1, 0.2, 0.3]
        )
        ps.validate()  # Should not raise
        
        # Invalid: no values or min/max
        ps_invalid = ParameterSpace(
            name='test_param',
            param_type='int'
        )
        with pytest.raises(ValueError, match="must have min/max or explicit values"):
            ps_invalid.validate()
        
        # Invalid: min >= max
        ps_invalid = ParameterSpace(
            name='test_param',
            param_type='float',
            min_value=10,
            max_value=5
        )
        with pytest.raises(ValueError, match="min_value must be < max_value"):
            ps_invalid.validate()
    
    def test_invalid_param_type(self):
        """Test invalid parameter type."""
        ps = ParameterSpace(
            name='test_param',
            param_type='invalid_type',
            values=[1, 2, 3]
        )
        with pytest.raises(ValueError, match="Invalid param_type"):
            ps.validate()


class TestHyperparameterTuner:
    """Tests for HyperparameterTuner class."""
    
    def test_initialization(self, hyperparameter_tuner):
        """Test tuner initialization."""
        assert hyperparameter_tuner.strategy_class == DualMomentumStrategy
        assert hyperparameter_tuner.base_config['safe_asset'] == 'AGG'
        assert len(hyperparameter_tuner.trial_results) == 0
    
    def test_grid_search_basic(self, hyperparameter_tuner):
        """Test basic grid search functionality."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2]
            ),
        ]
        
        results = hyperparameter_tuner.grid_search(
            param_space=param_space,
            metric='sharpe_ratio',
            higher_is_better=True,
            verbose=False,
        )
        
        # Check results structure
        assert isinstance(results, OptimizationResult)
        assert results.best_params is not None
        assert 'lookback_period' in results.best_params
        assert 'position_count' in results.best_params
        assert results.n_trials == 4  # 2 x 2 = 4 combinations
        assert results.method == 'grid_search'
        assert not results.all_results.empty
    
    def test_random_search_basic(self, hyperparameter_tuner):
        """Test basic random search functionality."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 189, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2, 3]
            ),
        ]
        
        results = hyperparameter_tuner.random_search(
            param_space=param_space,
            n_trials=5,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Check results structure
        assert isinstance(results, OptimizationResult)
        assert results.best_params is not None
        assert results.n_trials == 5
        assert results.method == 'random_search'
        assert not results.all_results.empty
        assert len(results.all_results) == 5
    
    @pytest.mark.skipif(
        not _has_optuna(),
        reason="Optuna not installed"
    )
    def test_bayesian_optimization_basic(self, hyperparameter_tuner):
        """Test basic Bayesian optimization functionality."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 189, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2]
            ),
        ]
        
        results = hyperparameter_tuner.bayesian_optimization(
            param_space=param_space,
            n_trials=10,
            n_initial_points=3,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Check results structure
        assert isinstance(results, OptimizationResult)
        assert results.best_params is not None
        assert results.n_trials == 10
        assert results.method == 'bayesian_optimization'
        assert not results.all_results.empty
    
    def test_generate_grid_combinations(self, hyperparameter_tuner):
        """Test grid combination generation."""
        param_space = [
            ParameterSpace(
                name='param1',
                param_type='int',
                values=[1, 2, 3]
            ),
            ParameterSpace(
                name='param2',
                param_type='categorical',
                values=['a', 'b']
            ),
        ]
        
        combinations = hyperparameter_tuner._generate_grid_combinations(param_space)
        
        assert len(combinations) == 6  # 3 x 2 = 6
        assert all('param1' in combo and 'param2' in combo for combo in combinations)
        assert all(combo['param1'] in [1, 2, 3] for combo in combinations)
        assert all(combo['param2'] in ['a', 'b'] for combo in combinations)
    
    def test_sample_random_params(self, hyperparameter_tuner):
        """Test random parameter sampling."""
        param_space = [
            ParameterSpace(
                name='int_param',
                param_type='int',
                values=[1, 2, 3, 4, 5]
            ),
            ParameterSpace(
                name='float_param',
                param_type='float',
                values=[0.1, 0.2, 0.3]
            ),
            ParameterSpace(
                name='cat_param',
                param_type='categorical',
                values=['x', 'y', 'z']
            ),
        ]
        
        # Sample multiple times to check randomness
        samples = [
            hyperparameter_tuner._sample_random_params(param_space)
            for _ in range(10)
        ]
        
        assert len(samples) == 10
        assert all('int_param' in s and 'float_param' in s and 'cat_param' in s for s in samples)
        assert all(s['int_param'] in [1, 2, 3, 4, 5] for s in samples)
        assert all(s['float_param'] in [0.1, 0.2, 0.3] for s in samples)
        assert all(s['cat_param'] in ['x', 'y', 'z'] for s in samples)


class TestDefaultParameterSpace:
    """Tests for default parameter space creation."""
    
    def test_create_default_param_space(self):
        """Test default parameter space creation."""
        param_space = create_default_param_space()
        
        assert isinstance(param_space, list)
        assert len(param_space) > 0
        
        # Check that common parameters are included
        param_names = [ps.name for ps in param_space]
        assert 'lookback_period' in param_names
        assert 'position_count' in param_names
        
        # Validate all parameters
        for ps in param_space:
            ps.validate()  # Should not raise


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass."""
    
    def test_optimization_result_creation(self):
        """Test OptimizationResult creation."""
        # Create a minimal BacktestResult mock
        from src.core.types import BacktestResult
        
        backtest_result = BacktestResult(
            strategy_name='test',
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000,
            final_capital=120000,
            returns=pd.Series([0.01, 0.02, -0.01]),
            positions=pd.DataFrame(),
            trades=pd.DataFrame(),
            metrics={'sharpe_ratio': 1.5},
            equity_curve=pd.Series([100000, 101000, 103020, 102000]),
            benchmark_curve=None,
            metadata={}
        )
        
        result = OptimizationResult(
            best_params={'lookback_period': 252, 'position_count': 2},
            best_score=1.5,
            best_backtest=backtest_result,
            all_results=pd.DataFrame({'score': [1.0, 1.5, 1.2]}),
            optimization_time=10.5,
            n_trials=3,
            metric_name='sharpe_ratio',
            method='grid_search',
        )
        
        assert result.best_params['lookback_period'] == 252
        assert result.best_score == 1.5
        assert result.n_trials == 3
        assert result.method == 'grid_search'
        assert not result.all_results.empty


class TestMethodComparison:
    """Tests for method comparison functionality."""
    
    def test_compare_two_methods(self, hyperparameter_tuner):
        """Test comparing two optimization methods."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2]
            ),
        ]
        
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search'],
            n_trials=5,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Check comparison structure
        assert isinstance(comparison, MethodComparisonResult)
        assert len(comparison.results) == 2
        assert 'grid_search' in comparison.results
        assert 'random_search' in comparison.results
        assert comparison.best_method in ['grid_search', 'random_search']
        assert comparison.best_overall_score is not None
        assert comparison.best_overall_params is not None
        assert not comparison.comparison_metrics.empty
        assert comparison.metric_name == 'sharpe_ratio'
        assert comparison.higher_is_better is True
    
    @pytest.mark.skipif(
        not _has_optuna(),
        reason="Optuna not installed"
    )
    def test_compare_all_methods(self, hyperparameter_tuner):
        """Test comparing all three optimization methods."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 189, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2]
            ),
        ]
        
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=None,  # Should default to all methods
            n_trials=8,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Check all methods were run
        assert len(comparison.results) == 3
        assert 'grid_search' in comparison.results
        assert 'random_search' in comparison.results
        assert 'bayesian_optimization' in comparison.results
        
        # Check comparison metrics
        assert len(comparison.comparison_metrics) == 3
        assert 'method' in comparison.comparison_metrics.columns
        assert 'best_score' in comparison.comparison_metrics.columns
        assert 'optimization_time' in comparison.comparison_metrics.columns
        assert 'n_trials' in comparison.comparison_metrics.columns
        assert 'time_per_trial' in comparison.comparison_metrics.columns
        assert 'is_best' in comparison.comparison_metrics.columns
        
        # Check that exactly one method is marked as best
        assert comparison.comparison_metrics['is_best'].sum() == 1
    
    def test_comparison_metrics_calculation(self, hyperparameter_tuner):
        """Test that comparison metrics are calculated correctly."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
        ]
        
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search'],
            n_trials=5,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Check time per trial is calculated
        for idx, row in comparison.comparison_metrics.iterrows():
            assert row['time_per_trial'] >= 0
            assert row['time_per_trial'] == row['optimization_time'] / row['n_trials']
    
    def test_comparison_with_invalid_method(self, hyperparameter_tuner):
        """Test that invalid method name raises error."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
        ]
        
        with pytest.raises(ValueError, match="Invalid method"):
            hyperparameter_tuner.compare_optimization_methods(
                param_space=param_space,
                methods=['invalid_method'],
                n_trials=5,
                metric='sharpe_ratio',
            )
    
    def test_comparison_best_method_selection(self, hyperparameter_tuner):
        """Test that best method is selected correctly."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
            ParameterSpace(
                name='position_count',
                param_type='int',
                values=[1, 2]
            ),
        ]
        
        # Test with maximize
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search'],
            n_trials=4,
            metric='sharpe_ratio',
            higher_is_better=True,
            random_state=42,
            verbose=False,
        )
        
        # Verify best method has highest score
        best_result = comparison.results[comparison.best_method]
        for method, result in comparison.results.items():
            assert best_result.best_score >= result.best_score
    
    def test_comparison_metadata(self, hyperparameter_tuner):
        """Test that comparison metadata is stored correctly."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
        ]
        
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search'],
            n_trials=10,
            n_initial_points=5,
            metric='sharpe_ratio',
            random_state=42,
            verbose=False,
        )
        
        assert 'n_trials' in comparison.metadata
        assert 'n_initial_points' in comparison.metadata
        assert 'random_state' in comparison.metadata
        assert comparison.metadata['n_trials'] == 10
        assert comparison.metadata['n_initial_points'] == 5
        assert comparison.metadata['random_state'] == 42
    
    def test_save_comparison_results(self, hyperparameter_tuner, tmp_path):
        """Test saving comparison results to disk."""
        param_space = [
            ParameterSpace(
                name='lookback_period',
                param_type='int',
                values=[126, 252]
            ),
        ]
        
        comparison = hyperparameter_tuner.compare_optimization_methods(
            param_space=param_space,
            methods=['grid_search', 'random_search'],
            n_trials=5,
            metric='sharpe_ratio',
            verbose=False,
        )
        
        # Save results
        saved_files = hyperparameter_tuner.save_comparison_results(
            comparison=comparison,
            output_dir=tmp_path,
            prefix='test_comparison'
        )
        
        # Check that files were created
        assert 'comparison_csv' in saved_files
        assert 'json' in saved_files
        assert 'pickle' in saved_files
        assert 'grid_search_csv' in saved_files
        assert 'random_search_csv' in saved_files
        
        # Verify files exist
        for file_path in saved_files.values():
            assert file_path.exists()
        
        # Verify CSV content
        comparison_df = pd.read_csv(saved_files['comparison_csv'])
        assert not comparison_df.empty
        assert 'method' in comparison_df.columns
        assert 'best_score' in comparison_df.columns
        
        # Verify JSON content
        import json
        with open(saved_files['json'], 'r') as f:
            summary = json.load(f)
        assert 'best_method' in summary
        assert 'best_overall_score' in summary
        assert 'best_overall_params' in summary
        assert 'methods_compared' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
