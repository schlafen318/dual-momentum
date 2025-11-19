"""
Serialization utilities for API responses.

Converts internal data structures to JSON-serializable formats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from ..core.types import BacktestResult


class BacktestResultSerializer:
    """Serialize BacktestResult to JSON-compatible format."""
    
    @staticmethod
    def serialize(result: BacktestResult) -> Dict[str, Any]:
        """
        Convert BacktestResult to dictionary.
        
        Args:
            result: BacktestResult instance
            
        Returns:
            Dictionary with serialized results
        """
        # Serialize equity curve
        equity_curve = None
        if result.equity_curve is not None and len(result.equity_curve) > 0:
            if isinstance(result.equity_curve, pd.Series):
                equity_curve = {
                    'dates': result.equity_curve.index.strftime('%Y-%m-%d').tolist(),
                    'values': result.equity_curve.values.tolist()
                }
            else:
                equity_curve = {
                    'values': list(result.equity_curve)
                }
        
        # Serialize returns
        returns = None
        if result.returns is not None and len(result.returns) > 0:
            if isinstance(result.returns, pd.Series):
                returns = {
                    'dates': result.returns.index.strftime('%Y-%m-%d').tolist(),
                    'values': result.returns.values.tolist()
                }
            else:
                returns = {
                    'values': list(result.returns)
                }
        
        # Serialize trades
        trades = []
        if result.trades is not None and len(result.trades) > 0:
            if isinstance(result.trades, pd.DataFrame):
                trades = result.trades.to_dict('records')
                # Convert datetime columns to strings
                for trade in trades:
                    for key, value in trade.items():
                        if isinstance(value, (pd.Timestamp, datetime)):
                            trade[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif pd.isna(value):
                            trade[key] = None
            else:
                trades = [
                    {
                        'symbol': t.symbol,
                        'entry_timestamp': t.entry_timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(t.entry_timestamp, datetime) else str(t.entry_timestamp),
                        'exit_timestamp': t.exit_timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(t.exit_timestamp, datetime) else str(t.exit_timestamp),
                        'entry_price': float(t.entry_price),
                        'exit_price': float(t.exit_price),
                        'quantity': float(t.quantity),
                        'pnl': float(t.pnl),
                        'pnl_pct': float(t.pnl_pct),
                        'duration': int(t.duration.total_seconds() / 86400) if hasattr(t.duration, 'total_seconds') else None,
                    }
                    for t in result.trades
                ]
        
        # Serialize positions DataFrame
        positions = None
        if result.positions is not None and not result.positions.empty:
            positions_df = result.positions.copy()
            # Reset index to include timestamp as column
            if isinstance(positions_df.index, pd.DatetimeIndex):
                positions_df = positions_df.reset_index()
                positions_df['timestamp'] = positions_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            positions = positions_df.to_dict('records')
            # Convert NaN to None
            for pos in positions:
                for key, value in pos.items():
                    if pd.isna(value):
                        pos[key] = None
                    elif isinstance(value, (int, float)):
                        pos[key] = float(value)
        
        # Serialize benchmark curve
        benchmark_curve = None
        if result.benchmark_curve is not None and len(result.benchmark_curve) > 0:
            if isinstance(result.benchmark_curve, pd.Series):
                benchmark_curve = {
                    'dates': result.benchmark_curve.index.strftime('%Y-%m-%d').tolist(),
                    'values': result.benchmark_curve.values.tolist()
                }
            else:
                benchmark_curve = {
                    'values': list(result.benchmark_curve)
                }
        
        # Serialize metrics (ensure all values are JSON-serializable)
        metrics = {}
        if result.metrics:
            for key, value in result.metrics.items():
                if value is None:
                    metrics[key] = None
                elif isinstance(value, (int, float)):
                    # Handle NaN and inf
                    if pd.isna(value):
                        metrics[key] = None
                    elif pd.isinf(value):
                        metrics[key] = None
                    else:
                        metrics[key] = float(value)
                elif isinstance(value, bool):
                    metrics[key] = value
                elif isinstance(value, str):
                    metrics[key] = value
                else:
                    # Try to convert to string for unknown types
                    metrics[key] = str(value)
        
        return {
            'strategy_name': result.strategy_name,
            'start_date': result.start_date.strftime('%Y-%m-%d') if isinstance(result.start_date, datetime) else str(result.start_date),
            'end_date': result.end_date.strftime('%Y-%m-%d') if isinstance(result.end_date, datetime) else str(result.end_date),
            'initial_capital': float(result.initial_capital),
            'final_capital': float(result.final_capital),
            'total_return': float(result.total_return),
            'annualized_return': float(result.annualized_return) if hasattr(result, 'annualized_return') else None,
            'sharpe_ratio': float(result.sharpe_ratio) if hasattr(result, 'sharpe_ratio') else None,
            'max_drawdown': float(result.max_drawdown) if hasattr(result, 'max_drawdown') else None,
            'metrics': metrics,
            'equity_curve': equity_curve,
            'returns': returns,
            'trades': trades,
            'positions': positions,
            'benchmark_curve': benchmark_curve,
            'metadata': result.metadata or {},
        }
    
    @staticmethod
    def serialize_summary(result: BacktestResult) -> Dict[str, Any]:
        """
        Serialize only summary metrics (lighter weight).
        
        Args:
            result: BacktestResult instance
            
        Returns:
            Dictionary with summary metrics only
        """
        return {
            'strategy_name': result.strategy_name,
            'start_date': result.start_date.strftime('%Y-%m-%d') if isinstance(result.start_date, datetime) else str(result.start_date),
            'end_date': result.end_date.strftime('%Y-%m-%d') if isinstance(result.end_date, datetime) else str(result.end_date),
            'initial_capital': float(result.initial_capital),
            'final_capital': float(result.final_capital),
            'total_return': float(result.total_return),
            'annualized_return': float(result.annualized_return) if hasattr(result, 'annualized_return') else None,
            'sharpe_ratio': float(result.sharpe_ratio) if hasattr(result, 'sharpe_ratio') else None,
            'max_drawdown': float(result.max_drawdown) if hasattr(result, 'max_drawdown') else None,
            'num_trades': len(result.trades) if result.trades is not None else 0,
            'metrics': {
                k: float(v) if isinstance(v, (int, float)) and not pd.isna(v) and not pd.isinf(v) else None
                for k, v in (result.metrics or {}).items()
            },
        }

