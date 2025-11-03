"""
Hyperparameter tuning module for backtesting optimization.

Provides grid search, random search, and Bayesian optimization
capabilities for finding optimal strategy parameters.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import pickle

import pandas as pd
import numpy as np
from loguru import logger

from ..core.base_strategy import BaseStrategy
from ..core.types import PriceData, BacktestResult
from .engine import BacktestEngine


@dataclass
class ParameterSpace:
    """
    Definition of a parameter search space.
    
    Attributes:
        name: Parameter name
        param_type: Type of parameter ('int', 'float', 'categorical')
        values: List of discrete values (for categorical or grid search)
        min_value: Minimum value (for continuous parameters)
        max_value: Maximum value (for continuous parameters)
        log_scale: Whether to use log scale for sampling
    """
    name: str
    param_type: str  # 'int', 'float', 'categorical'
    values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    log_scale: bool = False
    
    def validate(self) -> None:
        """Validate parameter space configuration."""
        if self.param_type == 'categorical':
            if not self.values:
                raise ValueError(f"Categorical parameter '{self.name}' must have values")
        elif self.param_type in ['int', 'float']:
            if self.min_value is None or self.max_value is None:
                if not self.values:
                    raise ValueError(
                        f"Numeric parameter '{self.name}' must have min/max or explicit values"
                    )
            elif self.min_value >= self.max_value:
                raise ValueError(
                    f"Parameter '{self.name}' min_value must be < max_value"
                )
        else:
            raise ValueError(
                f"Invalid param_type '{self.param_type}'. Must be 'int', 'float', or 'categorical'"
            )


@dataclass
class OptimizationResult:
    """
    Results from hyperparameter optimization.
    
    Attributes:
        best_params: Best parameter configuration found
        best_score: Best score achieved
        best_backtest: Full backtest result for best parameters
        all_results: DataFrame with all trials
        optimization_time: Total time spent optimizing
        n_trials: Number of trials completed
        metric_name: Name of optimization metric
        method: Optimization method used
    """
    best_params: Dict[str, Any]
    best_score: float
    best_backtest: BacktestResult
    all_results: pd.DataFrame
    optimization_time: float
    n_trials: int
    metric_name: str
    method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodComparisonResult:
    """
    Results from comparing multiple optimization methods.
    
    Attributes:
        results: Dictionary mapping method names to OptimizationResults
        best_method: Name of the best performing method
        best_overall_score: Best score across all methods
        best_overall_params: Parameters that achieved best score
        comparison_metrics: DataFrame comparing methods on various metrics
        metric_name: Name of optimization metric used
        higher_is_better: Whether higher metric values are better
    """
    results: Dict[str, OptimizationResult]
    best_method: str
    best_overall_score: float
    best_overall_params: Dict[str, Any]
    comparison_metrics: pd.DataFrame
    metric_name: str
    higher_is_better: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class HyperparameterTuner:
    """
    Hyperparameter tuning engine for strategy optimization.
    
    Supports multiple optimization methods:
    - Grid Search: Exhaustive search over discrete parameter grid
    - Random Search: Random sampling from parameter distributions
    - Bayesian Optimization: Efficient optimization using surrogate models
    
    Example:
        >>> tuner = HyperparameterTuner(
        ...     strategy_class=DualMomentumStrategy,
        ...     backtest_engine=engine,
        ...     price_data=data
        ... )
        >>> 
        >>> param_space = [
        ...     ParameterSpace('lookback_period', 'int', values=[126, 189, 252, 315]),
        ...     ParameterSpace('position_count', 'int', values=[1, 2, 3]),
        ... ]
        >>> 
        >>> results = tuner.grid_search(
        ...     param_space=param_space,
        ...     metric='sharpe_ratio',
        ...     n_jobs=4
        ... )
    """
    
    def __init__(
        self,
        strategy_class: type,
        backtest_engine: BacktestEngine,
        price_data: Dict[str, PriceData],
        base_config: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        benchmark_data: Optional[PriceData] = None,
        risk_manager: Optional[Any] = None,
    ):
        """
        Initialize hyperparameter tuner.
        
        Args:
            strategy_class: Strategy class to optimize
            backtest_engine: Backtesting engine instance
            price_data: Historical price data
            base_config: Base configuration (non-tuned parameters)
            start_date: Backtest start date
            end_date: Backtest end date
            benchmark_data: Benchmark data for comparison
            risk_manager: Risk manager instance
        """
        self.strategy_class = strategy_class
        self.backtest_engine = backtest_engine
        self.price_data = price_data
        self.base_config = base_config or {}
        self.start_date = start_date
        self.end_date = end_date
        self.benchmark_data = benchmark_data
        self.risk_manager = risk_manager
        
        # Results tracking
        self.trial_results: List[Dict[str, Any]] = []
        
        logger.info(
            f"Initialized HyperparameterTuner for {strategy_class.__name__}"
        )
    
    def grid_search(
        self,
        param_space: List[ParameterSpace],
        metric: str = 'sharpe_ratio',
        higher_is_better: bool = True,
        n_jobs: int = 1,
        verbose: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OptimizationResult:
        """
        Perform grid search over parameter space.
        
        Args:
            param_space: List of parameter spaces to search
            metric: Metric to optimize
            higher_is_better: Whether higher metric values are better
            n_jobs: Number of parallel jobs (currently sequential)
            verbose: Whether to print progress
        
        Returns:
            OptimizationResult with best parameters and all results
        """
        logger.info("Starting grid search hyperparameter optimization")
        logger.info(f"Optimizing metric: {metric} ({'maximize' if higher_is_better else 'minimize'})")
        
        # Validate parameter spaces
        for ps in param_space:
            ps.validate()
        
        # Generate all parameter combinations
        param_combinations = self._generate_grid_combinations(param_space)
        n_combinations = len(param_combinations)
        
        logger.info(f"Generated {n_combinations} parameter combinations")
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"GRID SEARCH OPTIMIZATION")
            print(f"{'='*80}")
            print(f"Strategy: {self.strategy_class.__name__}")
            print(f"Metric: {metric}")
            print(f"Total combinations: {n_combinations}")
            print(f"{'='*80}\n")
        
        # Reset trial results
        self.trial_results = []
        start_time = pd.Timestamp.now()
        
        # Evaluate each combination
        best_score = -np.inf if higher_is_better else np.inf
        best_params = None
        best_backtest = None
        
        for idx, params in enumerate(param_combinations, 1):
            if verbose:
                print(f"\nTrial {idx}/{n_combinations}")
                print(f"Parameters: {params}")

            trial_score: Optional[float] = None
            status = 'running'

            # Run backtest
            try:
                score, backtest_result = self._evaluate_params(params, metric)
                trial_score = score
                status = 'ok'

                # Track result
                self.trial_results.append({
                    'trial': idx,
                    'params': params,
                    'score': score,
                    'backtest': backtest_result,
                })

                # Update best
                is_better = (
                    (higher_is_better and score > best_score) or
                    (not higher_is_better and score < best_score)
                )

                if is_better:
                    best_score = score
                    best_params = params
                    best_backtest = backtest_result

                    if verbose:
                        print(f"[OK] New best! Score: {score:.4f}")
                else:
                    if verbose:
                        print(f"  Score: {score:.4f}")

            except Exception as e:
                status = 'error'
                logger.error(f"Error evaluating params {params}: {e}")
                if verbose:
                    print(f"[ERROR] {e}")

                # Track failed trial
                self.trial_results.append({
                    'trial': idx,
                    'params': params,
                    'score': np.nan,
                    'error': str(e),
                })

            if progress_callback:
                elapsed_seconds = (pd.Timestamp.now() - start_time).total_seconds()
                progress_callback({
                    'method': 'grid_search',
                    'trial': idx,
                    'total': n_combinations,
                    'score': trial_score,
                    'best_score': None if best_params is None else best_score,
                    'status': status,
                    'elapsed_seconds': elapsed_seconds,
                })

        end_time = pd.Timestamp.now()
        optimization_time = (end_time - start_time).total_seconds()
        
        # Create results DataFrame
        results_df = self._create_results_dataframe()
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"OPTIMIZATION COMPLETE")
            print(f"{'='*80}")
            print(f"Best score: {best_score:.4f}")
            print(f"Best parameters: {best_params}")
            print(f"Time: {optimization_time:.2f}s")
            print(f"{'='*80}\n")
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_backtest=best_backtest,
            all_results=results_df,
            optimization_time=optimization_time,
            n_trials=n_combinations,
            metric_name=metric,
            method='grid_search',
            metadata={
                'higher_is_better': higher_is_better,
                'n_jobs': n_jobs,
            }
        )
    
    def random_search(
        self,
        param_space: List[ParameterSpace],
        n_trials: int = 50,
        metric: str = 'sharpe_ratio',
        higher_is_better: bool = True,
        random_state: Optional[int] = None,
        verbose: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OptimizationResult:
        """
        Perform random search over parameter space.
        
        Args:
            param_space: List of parameter spaces to search
            n_trials: Number of random trials
            metric: Metric to optimize
            higher_is_better: Whether higher metric values are better
            random_state: Random seed for reproducibility
            verbose: Whether to print progress
        
        Returns:
            OptimizationResult with best parameters and all results
        """
        logger.info("Starting random search hyperparameter optimization")
        logger.info(f"Optimizing metric: {metric} ({'maximize' if higher_is_better else 'minimize'})")
        
        # Validate parameter spaces
        for ps in param_space:
            ps.validate()
        
        # Set random seed
        if random_state is not None:
            np.random.seed(random_state)
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"RANDOM SEARCH OPTIMIZATION")
            print(f"{'='*80}")
            print(f"Strategy: {self.strategy_class.__name__}")
            print(f"Metric: {metric}")
            print(f"Number of trials: {n_trials}")
            print(f"{'='*80}\n")
        
        # Reset trial results
        self.trial_results = []
        start_time = pd.Timestamp.now()
        
        # Evaluate random combinations
        best_score = -np.inf if higher_is_better else np.inf
        best_params = None
        best_backtest = None
        
        for idx in range(1, n_trials + 1):
            # Sample random parameters
            params = self._sample_random_params(param_space)

            if verbose:
                print(f"\nTrial {idx}/{n_trials}")
                print(f"Parameters: {params}")

            trial_score: Optional[float] = None
            status = 'running'

            # Run backtest
            try:
                score, backtest_result = self._evaluate_params(params, metric)
                trial_score = score
                status = 'ok'

                # Track result
                self.trial_results.append({
                    'trial': idx,
                    'params': params,
                    'score': score,
                    'backtest': backtest_result,
                })

                # Update best
                is_better = (
                    (higher_is_better and score > best_score) or
                    (not higher_is_better and score < best_score)
                )

                if is_better:
                    best_score = score
                    best_params = params
                    best_backtest = backtest_result

                    if verbose:
                        print(f"[OK] New best! Score: {score:.4f}")
                else:
                    if verbose:
                        print(f"  Score: {score:.4f}")

            except Exception as e:
                status = 'error'
                logger.error(f"Error evaluating params {params}: {e}")
                if verbose:
                    print(f"[ERROR] {e}")

                self.trial_results.append({
                    'trial': idx,
                    'params': params,
                    'score': np.nan,
                    'error': str(e),
                })

            if progress_callback:
                elapsed_seconds = (pd.Timestamp.now() - start_time).total_seconds()
                progress_callback({
                    'method': 'random_search',
                    'trial': idx,
                    'total': n_trials,
                    'score': trial_score,
                    'best_score': None if best_params is None else best_score,
                    'status': status,
                    'elapsed_seconds': elapsed_seconds,
                })

        end_time = pd.Timestamp.now()
        optimization_time = (end_time - start_time).total_seconds()
        
        # Create results DataFrame
        results_df = self._create_results_dataframe()
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"OPTIMIZATION COMPLETE")
            print(f"{'='*80}")
            print(f"Best score: {best_score:.4f}")
            print(f"Best parameters: {best_params}")
            print(f"Time: {optimization_time:.2f}s")
            print(f"{'='*80}\n")
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_backtest=best_backtest,
            all_results=results_df,
            optimization_time=optimization_time,
            n_trials=n_trials,
            metric_name=metric,
            method='random_search',
            metadata={
                'higher_is_better': higher_is_better,
                'random_state': random_state,
            }
        )
    
    def bayesian_optimization(
        self,
        param_space: List[ParameterSpace],
        n_trials: int = 50,
        n_initial_points: int = 10,
        metric: str = 'sharpe_ratio',
        higher_is_better: bool = True,
        random_state: Optional[int] = None,
        verbose: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OptimizationResult:
        """
        Perform Bayesian optimization using Optuna.
        
        Args:
            param_space: List of parameter spaces to search
            n_trials: Number of optimization trials
            n_initial_points: Number of random initial points
            metric: Metric to optimize
            higher_is_better: Whether higher metric values are better
            random_state: Random seed for reproducibility
            verbose: Whether to print progress
        
        Returns:
            OptimizationResult with best parameters and all results
        """
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            raise ImportError(
                "Optuna is required for Bayesian optimization. "
                "Install it with: pip install optuna"
            )
        
        logger.info("Starting Bayesian optimization")
        logger.info(f"Optimizing metric: {metric} ({'maximize' if higher_is_better else 'minimize'})")
        
        # Validate parameter spaces
        for ps in param_space:
            ps.validate()
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"BAYESIAN OPTIMIZATION")
            print(f"{'='*80}")
            print(f"Strategy: {self.strategy_class.__name__}")
            print(f"Metric: {metric}")
            print(f"Number of trials: {n_trials}")
            print(f"Initial random points: {n_initial_points}")
            print(f"{'='*80}\n")
        
        # Reset trial results
        self.trial_results = []
        start_time = pd.Timestamp.now()
        best_score_value = -np.inf if higher_is_better else np.inf
        best_params_candidate: Optional[Dict[str, Any]] = None

        # Create objective function
        def objective(trial):
            nonlocal best_score_value, best_params_candidate
            # Sample parameters
            params = {}
            for ps in param_space:
                if ps.param_type == 'categorical':
                    params[ps.name] = trial.suggest_categorical(ps.name, ps.values)
                elif ps.param_type == 'int':
                    if ps.values:
                        params[ps.name] = trial.suggest_categorical(ps.name, ps.values)
                    else:
                        params[ps.name] = trial.suggest_int(
                            ps.name, int(ps.min_value), int(ps.max_value),
                            log=ps.log_scale
                        )
                elif ps.param_type == 'float':
                    if ps.values:
                        params[ps.name] = trial.suggest_categorical(ps.name, ps.values)
                    else:
                        params[ps.name] = trial.suggest_float(
                            ps.name, ps.min_value, ps.max_value,
                            log=ps.log_scale
                        )
            
            if verbose:
                print(f"\nTrial {trial.number + 1}/{n_trials}")
                print(f"Parameters: {params}")
            
            # Evaluate parameters
            try:
                score, backtest_result = self._evaluate_params(params, metric)
                
                # Track result
                self.trial_results.append({
                    'trial': trial.number + 1,
                    'params': params,
                    'score': score,
                    'backtest': backtest_result,
                })
                
                is_better = (
                    (higher_is_better and score > best_score_value) or
                    (not higher_is_better and score < best_score_value)
                )
                if is_better:
                    best_score_value = score
                    best_params_candidate = params
                
                if verbose:
                    print(f"  Score: {score:.4f}")
                if progress_callback:
                    elapsed_seconds = (pd.Timestamp.now() - start_time).total_seconds()
                    progress_callback({
                        'method': 'bayesian_optimization',
                        'trial': trial.number + 1,
                        'total': n_trials,
                        'score': score,
                        'best_score': None if best_params_candidate is None else best_score_value,
                        'status': 'ok',
                        'elapsed_seconds': elapsed_seconds,
                    })
                
                return score
            
            except Exception as e:
                logger.error(f"Error in trial {trial.number}: {e}")
                if verbose:
                    print(f"[ERROR] {e}")
                
                self.trial_results.append({
                    'trial': trial.number + 1,
                    'params': params,
                    'score': np.nan,
                    'error': str(e),
                })
                if progress_callback:
                    elapsed_seconds = (pd.Timestamp.now() - start_time).total_seconds()
                    progress_callback({
                        'method': 'bayesian_optimization',
                        'trial': trial.number + 1,
                        'total': n_trials,
                        'score': None,
                        'best_score': None if best_params_candidate is None else best_score_value,
                        'status': 'error',
                        'elapsed_seconds': elapsed_seconds,
                    })
                
                # Return worst possible value
                return -np.inf if higher_is_better else np.inf
        
        # Create study
        direction = 'maximize' if higher_is_better else 'minimize'
        study = optuna.create_study(
            direction=direction,
            sampler=optuna.samplers.TPESampler(
                n_startup_trials=n_initial_points,
                seed=random_state
            )
        )
        
        # Optimize
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        end_time = pd.Timestamp.now()
        optimization_time = (end_time - start_time).total_seconds()
        
        # Get best results
        best_params = study.best_params
        best_score = study.best_value
        
        # Find best backtest result
        best_backtest = None
        for result in self.trial_results:
            if result['params'] == best_params:
                best_backtest = result.get('backtest')
                break
        
        # Create results DataFrame
        results_df = self._create_results_dataframe()
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"OPTIMIZATION COMPLETE")
            print(f"{'='*80}")
            print(f"Best score: {best_score:.4f}")
            print(f"Best parameters: {best_params}")
            print(f"Time: {optimization_time:.2f}s")
            print(f"{'='*80}\n")
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            best_backtest=best_backtest,
            all_results=results_df,
            optimization_time=optimization_time,
            n_trials=n_trials,
            metric_name=metric,
            method='bayesian_optimization',
            metadata={
                'higher_is_better': higher_is_better,
                'n_initial_points': n_initial_points,
                'random_state': random_state,
            }
        )
    
    def _evaluate_params(
        self,
        params: Dict[str, Any],
        metric: str
    ) -> Tuple[float, BacktestResult]:
        """
        Evaluate a parameter configuration.
        
        Args:
            params: Parameter dictionary
            metric: Metric to extract
        
        Returns:
            Tuple of (score, backtest_result)
        """
        # Merge with base config
        config = {**self.base_config, **params}
        
        # Create strategy instance
        strategy = self.strategy_class(config)
        
        # Run backtest
        backtest_result = self.backtest_engine.run(
            strategy=strategy,
            price_data=self.price_data,
            risk_manager=self.risk_manager,
            start_date=self.start_date,
            end_date=self.end_date,
            benchmark_data=self.benchmark_data,
        )
        
        # Extract metric
        score = backtest_result.metrics.get(metric, np.nan)
        
        if pd.isna(score):
            logger.warning(f"Metric '{metric}' not found in results")
            score = 0.0
        
        return score, backtest_result
    
    def _generate_grid_combinations(
        self,
        param_space: List[ParameterSpace]
    ) -> List[Dict[str, Any]]:
        """Generate all combinations for grid search."""
        from itertools import product
        
        # Get all value lists
        param_names = []
        param_values_lists = []
        
        for ps in param_space:
            param_names.append(ps.name)
            
            if ps.values:
                param_values_lists.append(ps.values)
            elif ps.param_type == 'int':
                # Generate integer range
                values = list(range(int(ps.min_value), int(ps.max_value) + 1))
                param_values_lists.append(values)
            else:
                raise ValueError(
                    f"Grid search requires explicit values for parameter '{ps.name}'"
                )
        
        # Generate all combinations
        combinations = []
        for combo in product(*param_values_lists):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)
        
        return combinations
    
    def _sample_random_params(
        self,
        param_space: List[ParameterSpace]
    ) -> Dict[str, Any]:
        """Sample random parameter configuration."""
        params = {}
        
        for ps in param_space:
            if ps.values:
                # Sample from discrete values
                params[ps.name] = np.random.choice(ps.values)
            elif ps.param_type == 'int':
                # Sample random integer
                if ps.log_scale:
                    log_min = np.log(ps.min_value)
                    log_max = np.log(ps.max_value)
                    log_val = np.random.uniform(log_min, log_max)
                    params[ps.name] = int(np.exp(log_val))
                else:
                    params[ps.name] = np.random.randint(
                        int(ps.min_value), int(ps.max_value) + 1
                    )
            elif ps.param_type == 'float':
                # Sample random float
                if ps.log_scale:
                    log_min = np.log(ps.min_value)
                    log_max = np.log(ps.max_value)
                    log_val = np.random.uniform(log_min, log_max)
                    params[ps.name] = np.exp(log_val)
                else:
                    params[ps.name] = np.random.uniform(ps.min_value, ps.max_value)
        
        return params
    
    def _create_results_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from trial results."""
        if not self.trial_results:
            return pd.DataFrame()
        
        rows = []
        for result in self.trial_results:
            row = {
                'trial': result['trial'],
                'score': result.get('score', np.nan),
            }
            
            # Add parameters
            if 'params' in result:
                for key, value in result['params'].items():
                    row[f'param_{key}'] = value
            
            # Add key metrics if backtest exists
            if 'backtest' in result and result['backtest']:
                bt = result['backtest']
                row['total_return'] = bt.metrics.get('total_return', np.nan)
                row['sharpe_ratio'] = bt.metrics.get('sharpe_ratio', np.nan)
                row['max_drawdown'] = bt.metrics.get('max_drawdown', np.nan)
                row['annual_return'] = bt.metrics.get('annual_return', np.nan)
                row['volatility'] = bt.metrics.get('volatility', np.nan)
            
            # Add error if present
            if 'error' in result:
                row['error'] = result['error']
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df
    
    def compare_optimization_methods(
        self,
        param_space: List[ParameterSpace],
        methods: Optional[List[str]] = None,
        n_trials: int = 50,
        n_initial_points: int = 10,
        metric: str = 'sharpe_ratio',
        higher_is_better: bool = True,
        random_state: Optional[int] = None,
        verbose: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> MethodComparisonResult:
        """
        Compare multiple optimization methods on the same problem.
        
        This method runs multiple optimization algorithms (Grid Search, Random Search,
        and/or Bayesian Optimization) and compares their performance, convergence speed,
        and parameter exploration strategies.
        
        Args:
            param_space: List of parameter spaces to search
            methods: List of method names to compare. Options: 'grid_search', 
                    'random_search', 'bayesian_optimization'. If None, compares all.
            n_trials: Number of trials for random search and Bayesian optimization
            n_initial_points: Number of initial random points for Bayesian optimization
            metric: Metric to optimize
            higher_is_better: Whether higher metric values are better
            random_state: Random seed for reproducibility
            verbose: Whether to print progress
        
        Returns:
            MethodComparisonResult with results from all methods and comparison metrics
        
        Example:
            >>> tuner = HyperparameterTuner(...)
            >>> param_space = [
            ...     ParameterSpace('lookback_period', 'int', values=[126, 189, 252]),
            ...     ParameterSpace('position_count', 'int', values=[1, 2, 3]),
            ... ]
            >>> comparison = tuner.compare_optimization_methods(
            ...     param_space=param_space,
            ...     methods=['grid_search', 'random_search', 'bayesian_optimization'],
            ...     n_trials=30,
            ...     metric='sharpe_ratio'
            ... )
            >>> print(f"Best method: {comparison.best_method}")
            >>> print(comparison.comparison_metrics)
        """
        # Default to all methods if not specified
        if methods is None:
            methods = ['grid_search', 'random_search', 'bayesian_optimization']
        
        # Validate methods
        valid_methods = ['grid_search', 'random_search', 'bayesian_optimization']
        for method in methods:
            if method not in valid_methods:
                raise ValueError(
                    f"Invalid method '{method}'. Must be one of {valid_methods}"
                )
        
        logger.info(f"Comparing optimization methods: {methods}")
        logger.info(f"Optimizing metric: {metric} ({'maximize' if higher_is_better else 'minimize'})")
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"OPTIMIZATION METHOD COMPARISON")
            print(f"{'='*80}")
            print(f"Strategy: {self.strategy_class.__name__}")
            print(f"Metric: {metric}")
            print(f"Methods: {', '.join(methods)}")
            print(f"{'='*80}\n")
        
        results = {}
        method_totals: Dict[str, int] = {}
        for method in methods:
            if method == 'grid_search':
                method_totals[method] = max(1, len(self._generate_grid_combinations(param_space)))
            else:
                method_totals[method] = max(1, n_trials)
        total_steps = sum(method_totals.values()) or len(methods)
        completed_steps = 0
        method_progress: Dict[str, int] = {method: 0 for method in methods}

        def make_progress_callback(method_name: str) -> Callable[[Dict[str, Any]], None]:
            def _callback(event: Dict[str, Any]) -> None:
                nonlocal completed_steps
                trial = event.get('trial') or 0
                prev = method_progress.get(method_name, 0)
                delta = max(0, trial - prev)
                method_progress[method_name] = max(prev, trial)
                completed_steps += delta
                if progress_callback:
                    payload = dict(event)
                    payload['method'] = method_name
                    payload['trial'] = trial
                    payload['method_total'] = method_totals.get(method_name, event.get('total'))
                    payload['completed_steps'] = completed_steps
                    payload['total_steps'] = total_steps
                    payload.setdefault('status', 'running')
                    progress_callback(payload)
            return _callback
        
        # Run each optimization method
        for method in methods:
            if verbose:
                print(f"\n{'='*80}")
                print(f"Running {method.replace('_', ' ').title()}")
                print(f"{'='*80}")
            
            try:
                if method == 'grid_search':
                    result = self.grid_search(
                        param_space=param_space,
                        metric=metric,
                        higher_is_better=higher_is_better,
                        verbose=verbose,
                        progress_callback=make_progress_callback('grid_search'),
                    )
                elif method == 'random_search':
                    result = self.random_search(
                        param_space=param_space,
                        n_trials=n_trials,
                        metric=metric,
                        higher_is_better=higher_is_better,
                        random_state=random_state,
                        verbose=verbose,
                        progress_callback=make_progress_callback('random_search'),
                    )
                elif method == 'bayesian_optimization':
                    result = self.bayesian_optimization(
                        param_space=param_space,
                        n_trials=n_trials,
                        n_initial_points=n_initial_points,
                        metric=metric,
                        higher_is_better=higher_is_better,
                        random_state=random_state,
                        verbose=verbose,
                        progress_callback=make_progress_callback('bayesian_optimization'),
                    )
                
                results[method] = result

                remaining = method_totals[method] - method_progress[method]
                if remaining > 0:
                    completed_steps += remaining
                    method_progress[method] = method_totals[method]
                if progress_callback:
                    progress_callback({
                        'method': method,
                        'trial': method_totals[method],
                        'method_total': method_totals[method],
                        'completed_steps': completed_steps,
                        'total_steps': total_steps,
                        'status': 'completed',
                        'score': result.best_score,
                        'best_score': result.best_score,
                        'elapsed_seconds': result.optimization_time,
                    })

                if verbose:
                    print(f"\n[INFO] {method} completed:")
                    print(f"  Best score: {result.best_score:.4f}")
                    print(f"  Time: {result.optimization_time:.2f}s")
                    print(f"  Trials: {result.n_trials}")
            
            except Exception as e:
                logger.error(f"Error running {method}: {e}")
                if verbose:
                    print(f"\n[ERROR] {method} failed: {e}")
        
        if not results:
            raise RuntimeError("All optimization methods failed")
        
        # Determine best method
        best_method = None
        best_overall_score = -np.inf if higher_is_better else np.inf
        best_overall_params = None
        
        for method, result in results.items():
            is_better = (
                (higher_is_better and result.best_score > best_overall_score) or
                (not higher_is_better and result.best_score < best_overall_score)
            )
            if is_better:
                best_overall_score = result.best_score
                best_method = method
                best_overall_params = result.best_params
        
        # Create comparison metrics DataFrame
        comparison_data = []
        for method, result in results.items():
            comparison_data.append({
                'method': method.replace('_', ' ').title(),
                'best_score': result.best_score,
                'optimization_time': result.optimization_time,
                'n_trials': result.n_trials,
                'time_per_trial': result.optimization_time / result.n_trials if result.n_trials > 0 else 0,
                'is_best': method == best_method,
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Sort by best score
        comparison_df = comparison_df.sort_values(
            by='best_score',
            ascending=not higher_is_better
        )
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"COMPARISON COMPLETE")
            print(f"{'='*80}")
            print(f"\nBest method: {best_method.replace('_', ' ').title()}")
            print(f"Best score: {best_overall_score:.4f}")
            print(f"\nComparison metrics:")
            print(comparison_df.to_string(index=False))
            print(f"{'='*80}\n")
        
        return MethodComparisonResult(
            results=results,
            best_method=best_method,
            best_overall_score=best_overall_score,
            best_overall_params=best_overall_params,
            comparison_metrics=comparison_df,
            metric_name=metric,
            higher_is_better=higher_is_better,
            metadata={
                'n_trials': n_trials,
                'n_initial_points': n_initial_points,
                'random_state': random_state,
            }
        )
    
    def save_results(
        self,
        results: OptimizationResult,
        output_dir: Union[str, Path],
        prefix: str = 'optimization'
    ) -> Dict[str, Path]:
        """
        Save optimization results to disk.
        
        Args:
            results: Optimization results to save
            output_dir: Output directory
            prefix: Filename prefix
        
        Returns:
            Dictionary mapping file types to paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"{prefix}_{results.method}_{timestamp}"
        
        saved_files = {}
        
        # Save results DataFrame as CSV
        csv_path = output_dir / f"{base_name}_results.csv"
        results.all_results.to_csv(csv_path, index=False)
        saved_files['csv'] = csv_path
        logger.info(f"Saved results to {csv_path}")
        
        # Save best parameters as JSON
        json_path = output_dir / f"{base_name}_best_params.json"
        with open(json_path, 'w') as f:
            json.dump({
                'best_params': results.best_params,
                'best_score': float(results.best_score),
                'metric': results.metric_name,
                'method': results.method,
                'n_trials': results.n_trials,
                'optimization_time': results.optimization_time,
            }, f, indent=2)
        saved_files['json'] = json_path
        logger.info(f"Saved best parameters to {json_path}")
        
        # Save full optimization result as pickle
        pickle_path = output_dir / f"{base_name}_full_results.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(results, f)
        saved_files['pickle'] = pickle_path
        logger.info(f"Saved full results to {pickle_path}")
        
        return saved_files
    
    def save_comparison_results(
        self,
        comparison: MethodComparisonResult,
        output_dir: Union[str, Path],
        prefix: str = 'method_comparison'
    ) -> Dict[str, Path]:
        """
        Save method comparison results to disk.
        
        Args:
            comparison: Method comparison results to save
            output_dir: Output directory
            prefix: Filename prefix
        
        Returns:
            Dictionary mapping file types to paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"{prefix}_{timestamp}"
        
        saved_files = {}
        
        # Save comparison metrics as CSV
        csv_path = output_dir / f"{base_name}_comparison.csv"
        comparison.comparison_metrics.to_csv(csv_path, index=False)
        saved_files['comparison_csv'] = csv_path
        logger.info(f"Saved comparison metrics to {csv_path}")
        
        # Save each method's results
        for method, result in comparison.results.items():
            method_csv_path = output_dir / f"{base_name}_{method}_results.csv"
            result.all_results.to_csv(method_csv_path, index=False)
            saved_files[f'{method}_csv'] = method_csv_path
        
        # Save summary as JSON
        json_path = output_dir / f"{base_name}_summary.json"
        with open(json_path, 'w') as f:
            json.dump({
                'best_method': comparison.best_method,
                'best_overall_score': float(comparison.best_overall_score),
                'best_overall_params': comparison.best_overall_params,
                'metric_name': comparison.metric_name,
                'higher_is_better': comparison.higher_is_better,
                'methods_compared': list(comparison.results.keys()),
                'metadata': comparison.metadata,
            }, f, indent=2)
        saved_files['json'] = json_path
        logger.info(f"Saved comparison summary to {json_path}")
        
        # Save full comparison result as pickle
        pickle_path = output_dir / f"{base_name}_full_comparison.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(comparison, f)
        saved_files['pickle'] = pickle_path
        logger.info(f"Saved full comparison to {pickle_path}")
        
        return saved_files


def create_default_param_space() -> List[ParameterSpace]:
    """
    Create default parameter space for dual momentum strategy.
    
    Returns:
        List of ParameterSpace objects
    """
    return [
        ParameterSpace(
            name='lookback_period',
            param_type='int',
            values=[63, 126, 189, 252, 315, 378]  # 3, 6, 9, 12, 15, 18 months
        ),
        ParameterSpace(
            name='position_count',
            param_type='int',
            values=[1, 2, 3, 4]
        ),
        ParameterSpace(
            name='absolute_threshold',
            param_type='float',
            values=[-0.05, 0.0, 0.01, 0.02, 0.05]
        ),
        ParameterSpace(
            name='use_volatility_adjustment',
            param_type='categorical',
            values=[True, False]
        ),
    ]
