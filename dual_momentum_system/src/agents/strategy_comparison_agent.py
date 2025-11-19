"""
Strategy Comparison Agent.

Automatically tests all available strategies against a benchmark to identify
outperforming strategies.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.engine import BacktestEngine
from src.config.config_api import get_config_api
from src.data_sources import get_default_data_source
from src.core.plugin_manager import get_plugin_manager
from src.backtesting.utils import (
    calculate_data_fetch_dates,
    ensure_safe_asset_data,
)
from src.core.types import BacktestResult


@dataclass
class StrategyResult:
    """Result for a single strategy backtest."""
    
    strategy_id: str
    strategy_name: str
    success: bool
    error: Optional[str] = None
    result: Optional[BacktestResult] = None
    
    # Performance metrics
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    
    # Benchmark comparison
    benchmark_total_return: Optional[float] = None
    excess_return: Optional[float] = None
    outperformance: bool = False
    
    # Additional metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'success': self.success,
            'error': self.error,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'benchmark_total_return': self.benchmark_total_return,
            'excess_return': self.excess_return,
            'outperformance': self.outperformance,
            'metrics': self.metrics,
        }


@dataclass
class ComparisonConfig:
    """Configuration for strategy comparison."""
    
    # Date range
    start_date: datetime
    end_date: datetime
    
    # Universe
    universe: List[str]
    benchmark_symbol: str
    
    # Engine parameters
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    risk_free_rate: float = 0.0
    
    # Strategy filtering
    strategy_ids: Optional[List[str]] = None  # If None, test all strategies
    exclude_strategy_ids: Optional[List[str]] = None
    
    # Comparison criteria
    min_excess_return: float = 0.0  # Minimum excess return to be considered outperforming
    min_sharpe_ratio: Optional[float] = None  # Minimum Sharpe ratio
    
    # Execution
    max_workers: int = 4  # For parallel execution
    parallel: bool = True
    
    # Data source
    api_keys: Optional[Dict[str, str]] = None


class StrategyComparisonAgent:
    """
    Agent that tests all strategies against a benchmark.
    
    Automatically discovers strategies, runs backtests, and identifies
    outperforming strategies.
    
    Example:
        >>> agent = StrategyComparisonAgent()
        >>> results = agent.compare_all_strategies(
        ...     universe=['SPY', 'EFA', 'EEM', 'AGG'],
        ...     benchmark_symbol='SPY',
        ...     start_date=datetime(2015, 1, 1),
        ...     end_date=datetime(2024, 1, 1)
        ... )
        >>> 
        >>> # Get outperforming strategies
        >>> outperforming = agent.get_outperforming_strategies(results)
        >>> for strategy in outperforming:
        ...     print(f"{strategy.strategy_name}: {strategy.excess_return:.2%} excess return")
    """
    
    def __init__(self):
        """Initialize the comparison agent."""
        self.config_api = get_config_api()
        self.plugin_manager = get_plugin_manager()
        
    def compare_all_strategies(
        self,
        config: ComparisonConfig
    ) -> List[StrategyResult]:
        """
        Test all available strategies against a benchmark.
        
        Args:
            config: Comparison configuration
            
        Returns:
            List of StrategyResult objects
        """
        logger.info("=" * 80)
        logger.info("STRATEGY COMPARISON AGENT")
        logger.info("=" * 80)
        logger.info(f"Universe: {config.universe}")
        logger.info(f"Benchmark: {config.benchmark_symbol}")
        logger.info(f"Period: {config.start_date.date()} to {config.end_date.date()}")
        logger.info("")
        
        # Get all strategies
        all_strategies = self.config_api.get_all_strategies()
        
        # Filter strategies
        strategy_ids = config.strategy_ids or list(all_strategies.keys())
        
        if config.exclude_strategy_ids:
            strategy_ids = [s for s in strategy_ids if s not in config.exclude_strategy_ids]
        
        logger.info(f"Testing {len(strategy_ids)} strategies...")
        logger.info("")
        
        # Run backtests
        if config.parallel and config.max_workers > 1:
            results = self._run_parallel(config, strategy_ids)
        else:
            results = self._run_sequential(config, strategy_ids)
        
        # Sort by excess return (descending)
        results.sort(key=lambda x: x.excess_return or -999, reverse=True)
        
        return results
    
    def _run_sequential(
        self,
        config: ComparisonConfig,
        strategy_ids: List[str]
    ) -> List[StrategyResult]:
        """Run backtests sequentially."""
        results = []
        
        for i, strategy_id in enumerate(strategy_ids, 1):
            logger.info(f"[{i}/{len(strategy_ids)}] Testing {strategy_id}...")
            
            try:
                result = self._test_strategy(config, strategy_id)
                results.append(result)
                
                if result.success:
                    logger.info(
                        f"  ✓ {strategy_id}: "
                        f"Return={result.total_return:.2%}, "
                        f"Excess={result.excess_return:.2%}, "
                        f"Sharpe={result.sharpe_ratio:.2f}"
                    )
                else:
                    logger.warning(f"  ✗ {strategy_id}: {result.error}")
                    
            except Exception as e:
                logger.error(f"  ✗ {strategy_id}: Error - {e}")
                results.append(StrategyResult(
                    strategy_id=strategy_id,
                    strategy_name=strategy_id,
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    def _run_parallel(
        self,
        config: ComparisonConfig,
        strategy_ids: List[str]
    ) -> List[StrategyResult]:
        """Run backtests in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # Submit all tasks
            future_to_strategy = {
                executor.submit(self._test_strategy, config, strategy_id): strategy_id
                for strategy_id in strategy_ids
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_strategy):
                strategy_id = future_to_strategy[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        logger.info(
                            f"[{completed}/{len(strategy_ids)}] ✓ {strategy_id}: "
                            f"Return={result.total_return:.2%}, "
                            f"Excess={result.excess_return:.2%}, "
                            f"Sharpe={result.sharpe_ratio:.2f}"
                        )
                    else:
                        logger.warning(f"[{completed}/{len(strategy_ids)}] ✗ {strategy_id}: {result.error}")
                        
                except Exception as e:
                    logger.error(f"[{completed}/{len(strategy_ids)}] ✗ {strategy_id}: Error - {e}")
                    results.append(StrategyResult(
                        strategy_id=strategy_id,
                        strategy_name=strategy_id,
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    def _test_strategy(
        self,
        config: ComparisonConfig,
        strategy_id: str
    ) -> StrategyResult:
        """
        Test a single strategy.
        
        Args:
            config: Comparison configuration
            strategy_id: Strategy identifier
            
        Returns:
            StrategyResult
        """
        try:
            # Get strategy info
            strategy_info = self.config_api.get_strategy(strategy_id)
            if not strategy_info:
                return StrategyResult(
                    strategy_id=strategy_id,
                    strategy_name=strategy_id,
                    success=False,
                    error=f"Strategy '{strategy_id}' not found"
                )
            
            strategy_name = strategy_info.get('name', strategy_id)
            
            # Create strategy
            success, strategy, msg = self.config_api.create_configured_strategy(
                strategy_id=strategy_id,
                custom_params=None
            )
            
            if not success:
                return StrategyResult(
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    success=False,
                    error=f"Failed to create strategy: {msg}"
                )
            
            # Update universe if needed
            if hasattr(strategy, 'config'):
                strategy.config['universe'] = config.universe
            elif hasattr(strategy, 'universe'):
                strategy.universe = config.universe
            
            # Get data source
            data_source = get_default_data_source(config.api_keys or {})
            
            # Calculate data fetch dates
            required_history = strategy.get_required_history()
            data_fetch_start, data_fetch_end = calculate_data_fetch_dates(
                backtest_start_date=config.start_date,
                backtest_end_date=config.end_date,
                lookback_period=required_history,
                safety_factor=1.5
            )
            
            # Fetch price data
            price_data = {}
            EquityAsset = self.plugin_manager.get_asset_class('EquityAsset')
            asset_class = EquityAsset() if EquityAsset else None
            
            for symbol in config.universe:
                try:
                    raw_data = data_source.fetch_data(
                        symbol=symbol,
                        start_date=data_fetch_start,
                        end_date=data_fetch_end,
                        timeframe='1d'
                    )
                    
                    if not raw_data.empty and asset_class:
                        normalized = asset_class.normalize_data(raw_data, symbol)
                        price_data[symbol] = normalized
                    elif not raw_data.empty:
                        from src.core.types import PriceData, AssetMetadata, AssetType
                        price_data[symbol] = PriceData(
                            symbol=symbol,
                            data=raw_data,
                            metadata=AssetMetadata(
                                symbol=symbol,
                                name=symbol,
                                asset_type=AssetType.EQUITY
                            )
                        )
                except Exception as e:
                    logger.debug(f"Failed to fetch data for {symbol}: {e}")
            
            if not price_data:
                return StrategyResult(
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    success=False,
                    error="No price data available"
                )
            
            # Ensure safe asset data if configured
            if hasattr(strategy, 'safe_asset') and strategy.safe_asset:
                ensure_safe_asset_data(
                    strategy=strategy,
                    price_data=price_data,
                    data_source=data_source,
                    start_date=data_fetch_start,
                    end_date=data_fetch_end
                )
            
            # Fetch benchmark data
            benchmark_data = None
            try:
                raw_benchmark = data_source.fetch_data(
                    symbol=config.benchmark_symbol,
                    start_date=data_fetch_start,
                    end_date=data_fetch_end,
                    timeframe='1d'
                )
                if not raw_benchmark.empty and asset_class:
                    benchmark_data = asset_class.normalize_data(raw_benchmark, config.benchmark_symbol)
                elif not raw_benchmark.empty:
                    from src.core.types import PriceData, AssetMetadata, AssetType
                    benchmark_data = PriceData(
                        symbol=config.benchmark_symbol,
                        data=raw_benchmark,
                        metadata=AssetMetadata(
                            symbol=config.benchmark_symbol,
                            name=config.benchmark_symbol,
                            asset_type=AssetType.EQUITY
                        )
                    )
            except Exception as e:
                logger.debug(f"Failed to fetch benchmark data: {e}")
            
            # Run backtest
            engine = BacktestEngine(
                initial_capital=config.initial_capital,
                commission=config.commission,
                slippage=config.slippage,
                risk_free_rate=config.risk_free_rate
            )
            
            result = engine.run(
                strategy=strategy,
                price_data=price_data,
                start_date=config.start_date,
                end_date=config.end_date,
                benchmark_data=benchmark_data
            )
            
            # Extract metrics
            strategy_result = StrategyResult(
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                success=True,
                result=result,
                total_return=result.total_return,
                annualized_return=result.annualized_return if hasattr(result, 'annualized_return') else None,
                sharpe_ratio=result.sharpe_ratio if hasattr(result, 'sharpe_ratio') else None,
                max_drawdown=result.max_drawdown if hasattr(result, 'max_drawdown') else None,
                volatility=result.metrics.get('volatility') if result.metrics else None,
                metrics=result.metrics or {}
            )
            
            # Calculate benchmark comparison
            if result.benchmark_curve is not None and len(result.benchmark_curve) > 0:
                benchmark_returns = result.benchmark_curve.pct_change().dropna()
                if len(benchmark_returns) > 0:
                    benchmark_total_return = (result.benchmark_curve.iloc[-1] / result.benchmark_curve.iloc[0]) - 1.0
                    strategy_result.benchmark_total_return = benchmark_total_return
                    strategy_result.excess_return = result.total_return - benchmark_total_return
                    strategy_result.outperformance = (
                        strategy_result.excess_return >= config.min_excess_return and
                        (config.min_sharpe_ratio is None or 
                         (strategy_result.sharpe_ratio is not None and 
                          strategy_result.sharpe_ratio >= config.min_sharpe_ratio))
                    )
            
            return strategy_result
            
        except Exception as e:
            logger.error(f"Error testing strategy {strategy_id}: {e}", exc_info=True)
            return StrategyResult(
                strategy_id=strategy_id,
                strategy_name=strategy_id,
                success=False,
                error=str(e)
            )
    
    def get_outperforming_strategies(
        self,
        results: List[StrategyResult],
        config: Optional[ComparisonConfig] = None
    ) -> List[StrategyResult]:
        """
        Filter results to only outperforming strategies.
        
        Args:
            results: List of strategy results
            config: Optional config for filtering criteria
            
        Returns:
            List of outperforming strategies
        """
        if config is None:
            # Use default criteria
            return [
                r for r in results
                if r.success and r.outperformance
            ]
        else:
            return [
                r for r in results
                if r.success and
                r.excess_return is not None and
                r.excess_return >= config.min_excess_return and
                (config.min_sharpe_ratio is None or
                 (r.sharpe_ratio is not None and r.sharpe_ratio >= config.min_sharpe_ratio))
            ]
    
    def generate_report(
        self,
        results: List[StrategyResult],
        output_file: Optional[Path] = None
    ) -> str:
        """
        Generate a comparison report.
        
        Args:
            results: List of strategy results
            output_file: Optional file to save report
            
        Returns:
            Report as string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("STRATEGY COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary
        total = len(results)
        successful = sum(1 for r in results if r.success)
        outperforming = sum(1 for r in results if r.success and r.outperformance)
        
        report_lines.append(f"Total Strategies Tested: {total}")
        report_lines.append(f"Successful: {successful}")
        report_lines.append(f"Outperforming: {outperforming}")
        report_lines.append("")
        
        # Outperforming strategies
        outperforming_strategies = [r for r in results if r.success and r.outperformance]
        if outperforming_strategies:
            report_lines.append("=" * 80)
            report_lines.append("OUTPERFORMING STRATEGIES")
            report_lines.append("=" * 80)
            report_lines.append("")
            report_lines.append(
                f"{'Strategy':<30} {'Return':>12} {'Excess':>12} {'Sharpe':>10} {'Max DD':>10}"
            )
            report_lines.append("-" * 80)
            
            for result in outperforming_strategies:
                report_lines.append(
                    f"{result.strategy_name[:28]:<30} "
                    f"{result.total_return:>11.2%} "
                    f"{result.excess_return:>11.2%} "
                    f"{result.sharpe_ratio:>9.2f} "
                    f"{result.max_drawdown:>9.2%}"
                )
            report_lines.append("")
        
        # All results
        report_lines.append("=" * 80)
        report_lines.append("ALL RESULTS")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(
            f"{'Strategy':<30} {'Status':<12} {'Return':>12} {'Excess':>12} {'Sharpe':>10} {'Max DD':>10}"
        )
        report_lines.append("-" * 80)
        
        for result in results:
            status = "✓" if result.success else "✗"
            if result.success:
                report_lines.append(
                    f"{result.strategy_name[:28]:<30} "
                    f"{status:<12} "
                    f"{result.total_return:>11.2%} "
                    f"{result.excess_return or 0:>11.2%} "
                    f"{result.sharpe_ratio or 0:>9.2f} "
                    f"{result.max_drawdown or 0:>9.2%}"
                )
            else:
                report_lines.append(
                    f"{result.strategy_name[:28]:<30} "
                    f"{status:<12} "
                    f"{'ERROR':>12} "
                    f"{'':>12} "
                    f"{'':>10} "
                    f"{'':>10}"
                )
                if result.error:
                    report_lines.append(f"  Error: {result.error}")
        
        report = "\n".join(report_lines)
        
        if output_file:
            output_file.write_text(report)
            logger.info(f"Report saved to {output_file}")
        
        return report

