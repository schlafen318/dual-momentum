"""
Backtesting engine for executing and evaluating trading strategies.

This module provides the core backtesting functionality, including
trade execution simulation, portfolio tracking, and results generation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np
from loguru import logger

from ..core.base_risk import BaseRiskManager
from ..core.base_strategy import BaseStrategy
from ..core.types import (
    BacktestResult,
    Position,
    PortfolioState,
    PriceData,
    Signal,
    Trade,
)


class BacktestEngine:
    """
    Backtesting engine for strategy evaluation.
    
    Executes strategies on historical data and tracks performance.
    
    Example:
        >>> engine = BacktestEngine(
        ...     initial_capital=100000,
        ...     commission=0.001
        ... )
        >>> results = engine.run(
        ...     strategy=dual_momentum,
        ...     price_data=data_dict,
        ...     risk_manager=risk_mgr
        ... )
        >>> print(results.metrics['sharpe_ratio'])
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        risk_free_rate: float = 0.0,
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting portfolio value
            commission: Commission rate (e.g., 0.001 = 0.1%)
            slippage: Slippage rate (e.g., 0.0005 = 0.05%)
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate
        
        # State tracking
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.timestamps: List[datetime] = []
        
        logger.info(
            f"Initialized BacktestEngine with ${initial_capital:,.2f} capital, "
            f"{commission:.2%} commission, {slippage:.2%} slippage"
        )
    
    def run(
        self,
        strategy: BaseStrategy,
        price_data: Dict[str, PriceData],
        risk_manager: Optional[BaseRiskManager] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BacktestResult:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy to backtest
            price_data: Dictionary mapping symbols to PriceData
            risk_manager: Optional risk manager for position sizing
            start_date: Optional start date (uses data start if None)
            end_date: Optional end date (uses data end if None)
        
        Returns:
            BacktestResult with performance metrics and trade history
        """
        logger.info(f"Starting backtest for {strategy.get_name()}")
        
        # Reset state
        self._reset()
        
        # Validate data
        if not price_data:
            raise ValueError("No price data provided")
        
        # Check if strategy has enough data
        if not strategy.backtest_ready(price_data):
            raise ValueError(
                f"Insufficient data for strategy. "
                f"Required: {strategy.get_required_history()} bars"
            )
        
        # Align data and get common date range
        aligned_data, date_index = self._align_data(price_data, start_date, end_date)
        
        if len(date_index) == 0:
            raise ValueError("No overlapping dates in price data")
        
        logger.info(
            f"Backtesting from {date_index[0]} to {date_index[-1]} "
            f"({len(date_index)} periods)"
        )
        
        # Track last rebalance date
        last_rebalance = None
        
        # Iterate through each timestamp
        for i, current_date in enumerate(date_index):
            # Update current prices for all positions
            self._update_positions(current_date, aligned_data)
            
            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(current_date, aligned_data)
            
            # Record equity
            self.equity_curve.append(portfolio_value)
            self.timestamps.append(current_date)
            
            # Check if we should rebalance
            should_rebalance = (
                last_rebalance is None or
                strategy.should_rebalance(current_date, last_rebalance)
            )
            
            if should_rebalance and i >= strategy.get_required_history():
                # Get current data slice for signal generation
                current_price_data = self._get_current_data(
                    aligned_data,
                    current_date,
                    strategy.get_required_history()
                )
                
                # Generate signals
                signals = strategy.generate_signals(current_price_data)
                
                if signals:
                    logger.debug(
                        f"{current_date}: Generated {len(signals)} signals"
                    )
                    
                    # Execute trades based on signals
                    self._execute_signals(
                        signals,
                        current_date,
                        aligned_data,
                        portfolio_value,
                        risk_manager
                    )
                    
                    last_rebalance = current_date
        
        # Close all remaining positions at end
        final_date = date_index[-1]
        self._close_all_positions(final_date, aligned_data)
        
        # Generate results
        results = self._generate_results(
            strategy.get_name(),
            date_index[0],
            date_index[-1]
        )
        
        logger.info(
            f"Backtest complete. Final value: ${results.final_capital:,.2f} "
            f"({results.total_return:.2%} return)"
        )
        
        return results
    
    def _reset(self) -> None:
        """Reset engine state for new backtest."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.timestamps = []
    
    def _align_data(
        self,
        price_data: Dict[str, PriceData],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> tuple[Dict[str, pd.DataFrame], pd.DatetimeIndex]:
        """
        Align all price data to common date index.
        
        Args:
            price_data: Dictionary of PriceData objects
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Tuple of (aligned_data_dict, common_date_index)
        """
        # Extract DataFrames
        data_dict = {symbol: pdata.data for symbol, pdata in price_data.items()}
        
        # Find common date range
        all_indices = [df.index for df in data_dict.values()]
        
        # Get intersection of all dates
        common_dates = all_indices[0]
        for idx in all_indices[1:]:
            common_dates = common_dates.intersection(idx)
        
        # Apply date filters (handle timezone-aware vs naive)
        if start_date:
            # Make start_date timezone-aware if common_dates is timezone-aware
            if common_dates.tz is not None and start_date.tzinfo is None:
                import pytz
                start_date = common_dates.tz.localize(start_date)
            elif common_dates.tz is None and start_date.tzinfo is not None:
                start_date = start_date.replace(tzinfo=None)
            common_dates = common_dates[common_dates >= start_date]
        if end_date:
            # Make end_date timezone-aware if common_dates is timezone-aware
            if common_dates.tz is not None and end_date.tzinfo is None:
                import pytz
                end_date = common_dates.tz.localize(end_date)
            elif common_dates.tz is None and end_date.tzinfo is not None:
                end_date = end_date.replace(tzinfo=None)
            common_dates = common_dates[common_dates <= end_date]
        
        # Align all data to common dates
        aligned_data = {
            symbol: df.loc[common_dates]
            for symbol, df in data_dict.items()
        }
        
        return aligned_data, common_dates
    
    def _get_current_data(
        self,
        aligned_data: Dict[str, pd.DataFrame],
        current_date: datetime,
        lookback: int
    ) -> Dict[str, PriceData]:
        """
        Get price data slice up to current date.
        
        Args:
            aligned_data: Aligned price data
            current_date: Current timestamp
            lookback: Number of periods to include
        
        Returns:
            Dictionary of PriceData objects with historical data
        """
        current_price_data = {}
        
        for symbol, df in aligned_data.items():
            # Get slice up to current date
            date_loc = df.index.get_loc(current_date)
            start_loc = max(0, date_loc - lookback + 1)
            slice_df = df.iloc[start_loc:date_loc + 1]
            
            # Create PriceData object (simplified metadata)
            from ..core.types import AssetMetadata, AssetType
            
            current_price_data[symbol] = PriceData(
                symbol=symbol,
                data=slice_df,
                metadata=AssetMetadata(
                    symbol=symbol,
                    name=symbol,
                    asset_type=AssetType.EQUITY
                )
            )
        
        return current_price_data
    
    def _update_positions(
        self,
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame]
    ) -> None:
        """Update current prices for all positions."""
        for symbol, position in self.positions.items():
            if symbol in aligned_data:
                current_price = float(aligned_data[symbol].loc[current_date, 'close'])
                position.current_price = current_price
                position.current_timestamp = current_date
    
    def _calculate_portfolio_value(
        self,
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame]
    ) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(
            pos.market_value for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    def _execute_signals(
        self,
        signals: List[Signal],
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame],
        portfolio_value: float,
        risk_manager: Optional[BaseRiskManager]
    ) -> None:
        """
        Execute trading signals.
        
        Args:
            signals: List of trading signals
            current_date: Current timestamp
            aligned_data: Price data
            portfolio_value: Current portfolio value
            risk_manager: Risk manager for position sizing
        """
        # First, close positions not in new signals
        signal_symbols = {s.symbol for s in signals if s.direction != 0}
        positions_to_close = [
            symbol for symbol in self.positions.keys()
            if symbol not in signal_symbols
        ]
        
        for symbol in positions_to_close:
            self._close_position(symbol, current_date, aligned_data)
        
        # Then, open/adjust positions based on signals
        for signal in signals:
            if signal.direction == 0 or signal.symbol not in aligned_data:
                continue
            
            # Get current price
            current_price = float(aligned_data[signal.symbol].loc[current_date, 'close'])
            
            # Apply slippage
            if signal.direction > 0:
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)
            
            # Calculate position size
            if risk_manager:
                position_size_dollars = risk_manager.calculate_position_size(
                    signal,
                    portfolio_value,
                    self.positions
                )
            else:
                # Simple equal weight
                target_pct = signal.strength / len(signals)
                position_size_dollars = portfolio_value * target_pct
            
            # Calculate shares to buy
            shares = position_size_dollars / execution_price
            
            # Calculate commission
            commission_cost = position_size_dollars * self.commission
            total_cost = position_size_dollars + commission_cost
            
            # Check if we have enough cash
            if total_cost > self.cash:
                logger.warning(
                    f"Insufficient cash for {signal.symbol}. "
                    f"Required: ${total_cost:,.2f}, Available: ${self.cash:,.2f}"
                )
                continue
            
            # Execute trade
            if signal.symbol in self.positions:
                # Adjust existing position
                self._adjust_position(
                    signal.symbol,
                    shares,
                    execution_price,
                    current_date
                )
            else:
                # Open new position
                self._open_position(
                    signal.symbol,
                    shares,
                    execution_price,
                    current_date
                )
            
            # Deduct cash
            self.cash -= total_cost
    
    def _open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        timestamp: datetime
    ) -> None:
        """Open a new position."""
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            entry_timestamp=timestamp,
            current_price=price,
            current_timestamp=timestamp,
            metadata={'initial_quantity': quantity}
        )
        
        self.positions[symbol] = position
        logger.debug(f"Opened position: {symbol} x {quantity:.2f} @ ${price:.2f}")
    
    def _adjust_position(
        self,
        symbol: str,
        new_quantity: float,
        price: float,
        timestamp: datetime
    ) -> None:
        """Adjust an existing position (simplified - treats as close and reopen)."""
        # For simplicity, close old and open new
        self._close_position(symbol, timestamp, {symbol: pd.DataFrame({'close': [price]}, index=[timestamp])})
        self._open_position(symbol, new_quantity, price, timestamp)
    
    def _close_position(
        self,
        symbol: str,
        timestamp: datetime,
        aligned_data: Dict[str, pd.DataFrame]
    ) -> None:
        """Close a position."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Get exit price
        if symbol in aligned_data and timestamp in aligned_data[symbol].index:
            exit_price = float(aligned_data[symbol].loc[timestamp, 'close'])
        else:
            exit_price = position.current_price
        
        # Apply slippage
        if position.quantity > 0:
            execution_price = exit_price * (1 - self.slippage)
        else:
            execution_price = exit_price * (1 + self.slippage)
        
        # Calculate proceeds
        proceeds = abs(position.quantity) * execution_price
        commission_cost = proceeds * self.commission
        net_proceeds = proceeds - commission_cost
        
        # Add to cash
        self.cash += net_proceeds
        
        # Record trade
        pnl = (execution_price - position.entry_price) * position.quantity
        pnl_pct = (execution_price - position.entry_price) / position.entry_price
        
        trade = Trade(
            symbol=symbol,
            entry_timestamp=position.entry_timestamp,
            exit_timestamp=timestamp,
            entry_price=position.entry_price,
            exit_price=execution_price,
            quantity=position.quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            direction=1 if position.quantity > 0 else -1,
            metadata={
                'commission': commission_cost,
                'gross_proceeds': proceeds,
                'net_proceeds': net_proceeds
            }
        )
        
        self.trades.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        logger.debug(
            f"Closed position: {symbol} x {position.quantity:.2f} @ ${execution_price:.2f} "
            f"(P&L: ${pnl:,.2f})"
        )
    
    def _close_all_positions(
        self,
        timestamp: datetime,
        aligned_data: Dict[str, pd.DataFrame]
    ) -> None:
        """Close all open positions."""
        symbols_to_close = list(self.positions.keys())
        for symbol in symbols_to_close:
            self._close_position(symbol, timestamp, aligned_data)
    
    def _generate_results(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Generate backtest results."""
        # Create equity curve series
        equity_series = pd.Series(self.equity_curve, index=self.timestamps)
        
        # Calculate returns
        returns = equity_series.pct_change().dropna()
        
        # Create trades DataFrame
        if self.trades:
            trades_df = pd.DataFrame([
                {
                    'symbol': t.symbol,
                    'entry_date': t.entry_timestamp,
                    'exit_date': t.exit_timestamp,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'quantity': t.quantity,
                    'pnl': t.pnl,
                    'pnl_pct': t.pnl_pct,
                    'duration': t.duration,
                }
                for t in self.trades
            ])
        else:
            trades_df = pd.DataFrame()
        
        # Calculate metrics
        from .performance import PerformanceCalculator
        calculator = PerformanceCalculator()
        metrics = calculator.calculate_metrics(
            returns,
            equity_series,
            self.risk_free_rate
        )
        
        # Create result object
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.equity_curve[-1] if self.equity_curve else self.initial_capital,
            returns=returns,
            positions=pd.DataFrame(),  # Could track position history
            trades=trades_df,
            metrics=metrics,
            equity_curve=equity_series,
            metadata={
                'commission': self.commission,
                'slippage': self.slippage,
                'risk_free_rate': self.risk_free_rate,
            }
        )
        
        return result
