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
        self.position_history: List[Dict[str, Any]] = []
        
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
        benchmark_data: Optional[PriceData] = None,
    ) -> BacktestResult:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy to backtest
            price_data: Dictionary mapping symbols to PriceData
            risk_manager: Optional risk manager for position sizing
            start_date: Optional start date (uses data start if None)
            end_date: Optional end date (uses data end if None)
            benchmark_data: Optional benchmark price data for comparison
        
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
            required_history = strategy.get_required_history()
            min_bars = min(len(pdata.data) for pdata in price_data.values())
            raise ValueError(
                f"Insufficient data for strategy. "
                f"Required: {required_history} bars, but only {min_bars} bars available. "
                f"\n\nTip: When fetching data, start from an earlier date to allow for warm-up period. "
                f"For a lookback of {required_history} days, fetch data starting at least {int(required_history * 1.5)} days before your desired backtest start date."
            )
        
        # Align data and get common date range
        aligned_data, date_index = self._align_data(price_data, start_date, end_date)
        
        if len(date_index) == 0:
            raise ValueError("No overlapping dates in price data")
        
        logger.info(
            f"Backtesting from {date_index[0]} to {date_index[-1]} "
            f"({len(date_index)} periods)"
        )
        
        # Log when first rebalancing will occur
        required_history = strategy.get_required_history()
        if len(date_index) > required_history:
            first_rebalance_idx = required_history
            # Find first month-end (for monthly rebalancing) after required history
            last_rebalance_check = None
            for i in range(required_history, min(required_history + 30, len(date_index))):
                should_rebal = (
                    last_rebalance_check is None or
                    strategy.should_rebalance(date_index[i], last_rebalance_check)
                )
                if should_rebal:
                    logger.info(
                        f"First rebalancing expected on or after {date_index[i]} "
                        f"(after {i} periods of warm-up data)"
                    )
                    break
                last_rebalance_check = date_index[i]
        else:
            logger.warning(
                f"Insufficient data for any rebalancing! "
                f"Have {len(date_index)} periods, need {required_history}"
            )
        
        # Validate safe asset availability
        self._validate_safe_asset_data(strategy, aligned_data)
        
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
            
            # Record position snapshot for allocation tracking
            self._record_position_snapshot(current_date, portfolio_value)
            
            # Check if we should rebalance
            should_rebalance = (
                last_rebalance is None or
                strategy.should_rebalance(current_date, last_rebalance)
            )
            
            if should_rebalance and i >= strategy.get_required_history():
                # Verify we have enough actual data (not just index position)
                # Check that each asset has sufficient bars before this date
                sufficient_data = True
                required_history = strategy.get_required_history()
                
                for symbol, df in aligned_data.items():
                    date_loc = df.index.get_loc(current_date)
                    if date_loc < required_history:
                        sufficient_data = False
                        logger.debug(
                            f"Insufficient data for {symbol}: only {date_loc} bars available, "
                            f"need {required_history}"
                        )
                        break
                
                if not sufficient_data:
                    # Skip rebalancing - not enough historical data yet
                    continue
                
                # Log rebalancing start
                logger.info(f"🔄 REBALANCING on {current_date.strftime('%Y-%m-%d')}")
                logger.info(f"   Portfolio Value: ${portfolio_value:,.2f}")
                logger.info(f"   Available Cash: ${self.cash:,.2f}")
                
                # Log current positions before rebalancing
                if self.positions:
                    logger.info("   Current Positions:")
                    for symbol, pos in self.positions.items():
                        market_value = pos.quantity * pos.current_price
                        pnl = (pos.current_price - pos.entry_price) * pos.quantity
                        logger.info(f"     {symbol}: {pos.quantity:.2f} shares @ ${pos.current_price:.2f} "
                                  f"(Value: ${market_value:,.2f}, P&L: ${pnl:,.2f})")
                else:
                    logger.info("   Current Positions: None")
                
                # Get current data slice for signal generation
                current_price_data = self._get_current_data(
                    aligned_data,
                    current_date,
                    strategy.get_required_history()
                )
                
                # Generate signals
                signals = strategy.generate_signals(current_price_data)
                
                if signals:
                    logger.info(f"   Generated {len(signals)} signals:")
                    for signal in signals:
                        direction_str = "LONG" if signal.direction > 0 else "SHORT" if signal.direction < 0 else "EXIT"
                        logger.info(f"     {signal.symbol}: {direction_str} (strength: {signal.strength:.2f})")
                    
                    # Store positions before execution for comparison
                    positions_before = dict(self.positions)
                    
                    # Execute trades based on signals
                    self._execute_signals(
                        signals,
                        current_date,
                        aligned_data,
                        portfolio_value,
                        risk_manager,
                        strategy
                    )
                    
                    # Log position changes after execution
                    positions_after = dict(self.positions)
                    self._log_position_changes(positions_before, positions_after, current_date)
                    
                    # Log portfolio state after rebalancing
                    new_portfolio_value = self._calculate_portfolio_value(current_date, aligned_data)
                    logger.info(f"   After Rebalancing:")
                    logger.info(f"     Portfolio Value: ${new_portfolio_value:,.2f}")
                    logger.info(f"     Available Cash: ${self.cash:,.2f}")
                    logger.info(f"     Change: ${new_portfolio_value - portfolio_value:,.2f}")
                else:
                    logger.info("   No signals generated - maintaining current positions")
                
                # Update last rebalance date
                last_rebalance = current_date
                logger.info("   ✅ Rebalancing complete")
        
        # Close all remaining positions at end
        final_date = date_index[-1]
        self._close_all_positions(final_date, aligned_data)
        
        # Generate results
        results = self._generate_results(
            strategy.get_name(),
            date_index[0],
            date_index[-1],
            benchmark_data
        )
        
        logger.info(
            f"Backtest complete. Final value: ${results.final_capital:,.2f} "
            f"({results.total_return:.2%} return)"
        )
        
        return results
    
    def _validate_safe_asset_data(
        self,
        strategy: BaseStrategy,
        aligned_data: Dict[str, pd.DataFrame]
    ) -> None:
        """
        Validate that safe asset data is available if configured.
        
        This is critical because if the safe asset is configured but not included
        in the price data, defensive signals will be silently skipped, leaving the
        portfolio in cash during bearish periods instead of rotating to bonds.
        
        FAIL-FAST: This now raises an exception instead of just warning, preventing
        silent failures during backtesting.
        
        Args:
            strategy: Strategy instance
            aligned_data: Price data dictionary
        
        Raises:
            ValueError: If safe asset is configured but data is not available
        """
        safe_asset = None
        
        # Try to get safe asset from strategy config or attribute
        if hasattr(strategy, 'config'):
            safe_asset = strategy.config.get('safe_asset')
        elif hasattr(strategy, 'safe_asset'):
            safe_asset = strategy.safe_asset
        
        if safe_asset and safe_asset not in aligned_data:
            error_msg = (
                f"\n{'='*80}\n"
                f"❌ CONFIGURATION ERROR: Safe asset '{safe_asset}' configured but no price data available!\n"
                f"\n"
                f"IMPACT: During bearish markets, defensive signals will fail, leaving portfolio in CASH.\n"
                f"\n"
                f"SOLUTIONS:\n"
                f"  1. Add '{safe_asset}' to your asset universe, OR\n"
                f"  2. Use a safe asset already in your universe (e.g., 'AGG', 'TLT'), OR\n"
                f"  3. Use utils.ensure_safe_asset_data() to auto-fetch, OR\n"
                f"  4. Set safe_asset=None to explicitly hold cash\n"
                f"\n"
                f"Available symbols in price data: {list(aligned_data.keys())}\n"
                f"{'='*80}"
            )
            logger.error(error_msg)
            raise ValueError(
                f"Safe asset '{safe_asset}' configured but not in price data. "
                f"Add to universe or use utils.ensure_safe_asset_data()."
            )
    
    def _reset(self) -> None:
        """Reset engine state for new backtest."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.timestamps = []
        self.position_history = []
    
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
            # Note: pct_change(N) needs N+1 bars to calculate the change from bar 0 to bar N
            # So we need to fetch lookback+1 bars to have enough data for the calculation
            date_loc = df.index.get_loc(current_date)
            start_loc = max(0, date_loc - lookback)  # Changed from (date_loc - lookback + 1)
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
            pos.quantity * pos.current_price for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    def _record_position_snapshot(
        self,
        current_date: datetime,
        portfolio_value: float
    ) -> None:
        """
        Record a snapshot of current positions for allocation tracking.
        
        Args:
            current_date: Current timestamp
            portfolio_value: Total portfolio value
        """
        snapshot = {
            'timestamp': current_date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
        }
        
        # Add position data
        num_positions = len(self.positions)
        for symbol, position in self.positions.items():
            snapshot[f'{symbol}_quantity'] = position.quantity
            snapshot[f'{symbol}_price'] = position.current_price
            snapshot[f'{symbol}_value'] = position.quantity * position.current_price
        
        self.position_history.append(snapshot)
        
        # Log first few snapshots for debugging
        if len(self.position_history) <= 3:
            logger.debug(f"Position snapshot #{len(self.position_history)}: {num_positions} positions, cash=${self.cash:,.2f}")
    
    def _create_positions_dataframe(self) -> pd.DataFrame:
        """
        Convert position history into a structured DataFrame.
        
        Returns:
            DataFrame with position history organized for allocation tracking
        """
        if not self.position_history:
            logger.debug("Position history is empty, returning empty DataFrame")
            return pd.DataFrame()
        
        logger.debug(f"Creating positions DataFrame from {len(self.position_history)} snapshots")
        
        # Convert list of dicts to DataFrame
        try:
            positions_df = pd.DataFrame(self.position_history)
            logger.debug(f"Initial DataFrame shape after conversion: {positions_df.shape}")
            logger.debug(f"Initial DataFrame columns: {positions_df.columns.tolist()}")
        except Exception as e:
            logger.error(f"Failed to create DataFrame from position_history: {e}")
            return pd.DataFrame()
        
        # Extract all unique symbols from the column names
        value_columns = [col for col in positions_df.columns if col.endswith('_value')]
        symbols = [col.replace('_value', '') for col in value_columns]
        
        # Create a cleaner structure for allocation analysis
        # Each row represents the state at a given timestamp
        result_data = []
        
        for idx, row in positions_df.iterrows():
            timestamp = row['timestamp']
            portfolio_value = row['portfolio_value']
            cash = row['cash']
            
            # Create base record
            record = {
                'timestamp': timestamp,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'cash_pct': (cash / portfolio_value * 100) if portfolio_value > 0 else 0
            }
            
            # Add each symbol's allocation
            for symbol in symbols:
                value = row.get(f'{symbol}_value', 0)
                quantity = row.get(f'{symbol}_quantity', 0)
                price = row.get(f'{symbol}_price', 0)
                
                record[f'{symbol}_value'] = value
                record[f'{symbol}_quantity'] = quantity
                record[f'{symbol}_price'] = price
                record[f'{symbol}_pct'] = (value / portfolio_value * 100) if portfolio_value > 0 else 0
            
            result_data.append(record)
        
        result_df = pd.DataFrame(result_data)
        result_df.set_index('timestamp', inplace=True)
        
        return result_df
    
    def _execute_signals(
        self,
        signals: List[Signal],
        current_date: datetime,
        aligned_data: Dict[str, pd.DataFrame],
        portfolio_value: float,
        risk_manager: Optional[BaseRiskManager],
        strategy: Optional[BaseStrategy] = None
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
        # We'll close positions after building target weights so we know intended holdings
        
        # Determine allocation weights in two steps:
        # 1) Decide included assets count vs desired position_count
        # 2) Allocate 100% across included risk assets if enough pass; otherwise
        #    assign remaining share to the safe asset (if available). Cash only when
        #    no safe asset is available.

        # Separate risk vs safe
        safe_symbol = getattr(strategy, 'safe_asset', None) if strategy is not None else None
        risk_signals: List[Signal] = []
        safe_signal: Optional[Signal] = None
        for s in signals:
            if safe_symbol and s.symbol == safe_symbol:
                safe_signal = s
            else:
                risk_signals.append(s)

        # Determine desired number of positions
        desired_positions = getattr(strategy, 'config', {}).get('position_count', len(risk_signals)) if strategy is not None else len(risk_signals)
        desired_positions = max(1, desired_positions)

        # Include at most desired_positions risk assets (highest strength first)
        risk_signals_sorted = sorted(risk_signals, key=lambda s: getattr(s, 'strength', 0.0), reverse=True)
        included_risk = risk_signals_sorted[:desired_positions]
        included_count = len(included_risk)

        # Compute shares
        risk_share = 1.0 if included_count >= desired_positions else (included_count / float(desired_positions))
        safe_share = 0.0
        if safe_signal is not None and included_count < desired_positions:
            safe_share = 1.0 - risk_share

        # Risk weights by strength (fallback equal if strengths sum to 0)
        total_strength = sum(max(0.0, min(1.0, s.strength)) for s in included_risk)
        normalized_weights: Dict[str, float] = {}
        if included_count > 0:
            if total_strength > 0:
                for s in included_risk:
                    normalized_weights[s.symbol] = (max(0.0, min(1.0, s.strength)) / total_strength) * risk_share
            else:
                equal = risk_share / included_count
                for s in included_risk:
                    normalized_weights[s.symbol] = equal
        
        if safe_share > 0 and safe_signal is not None:
            normalized_weights[safe_signal.symbol] = safe_share
        
        # If no included assets and safe not available, weights remain empty (cash)

        # Then, open/adjust positions based on weights
        ordered_signals: List[Signal] = []
        # Maintain stable order: all risk signals first, then safe (if any)
        if included_risk:
            ordered_signals.extend(included_risk)
        if safe_signal is not None and safe_signal.symbol in normalized_weights:
            ordered_signals.append(safe_signal)
        
        remaining_cash = self.cash
        total_signals = len(ordered_signals)
        # Precompute scaling factor and log target weights
        est_total_required = 0.0
        for s2 in ordered_signals:
            pct2 = normalized_weights.get(s2.symbol, 0.0)
            est_total_required += portfolio_value * pct2 * (1 + self.commission)
        scaling_factor = min(1.0, remaining_cash / est_total_required) if est_total_required > 0 else 0.0
        logger.info(
            f"[ORDER SIZING] {current_date.strftime('%Y-%m-%d')}: PV=${portfolio_value:,.2f}, Cash=${remaining_cash:,.2f}, Comm={self.commission:.4%}, Slip={self.slippage:.4%}, Scale={scaling_factor:.6f}"
        )
        logger.info("[ORDER SIZING] Weights: " + ", ".join([f"{sym}={normalized_weights[sym]*100:.2f}%" for sym in normalized_weights.keys()]))
        batch_total_cost = 0.0
        
        for idx, signal in enumerate(ordered_signals):
            if signal.direction == 0:
                continue
            
            # Check if price data is available for this signal
            if signal.symbol not in aligned_data:
                # This should not happen now due to fail-fast validation
                # But keeping as defensive check
                logger.error(
                    f"❌ Signal for '{signal.symbol}' cannot be executed - no price data! "
                    f"This should have been caught in validation. "
                    f"Reason: {signal.reason.value if hasattr(signal, 'reason') else 'unknown'}"
                )
                continue
            
            # Get current price
            current_price = float(aligned_data[signal.symbol].loc[current_date, 'close'])
            
            # Apply slippage
            if signal.direction > 0:
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)
            
            # Determine target allocation percent from normalized weights
            target_pct = normalized_weights.get(signal.symbol, 0.0)
            # Calculate desired spend such that sum(cost) == cash (proportional scaling)
            desired_dollars = portfolio_value * target_pct
            # Apply scaling factor (and remove commission impact for notional sizing)
            desired_size = desired_dollars * scaling_factor / (1 + self.commission)
            
            if risk_manager and desired_size > 0:
                rm_cap = risk_manager.calculate_position_size(signal, portfolio_value, self.positions) if hasattr(risk_manager, 'calculate_position_size') else desired_size
                position_size_dollars = max(0.0, min(desired_size, rm_cap))
            else:
                position_size_dollars = max(0.0, desired_size)
            
            # Calculate shares to buy
            shares = position_size_dollars / execution_price
            
            # Calculate commission
            commission_cost = position_size_dollars * self.commission
            total_cost = position_size_dollars + commission_cost
            
            # Log trade details with enhanced context
            direction_str = "BUY" if signal.direction > 0 else "SELL"
            reason_str = f" [{signal.reason.value}]" if hasattr(signal, 'reason') else ""
            blend_str = ""
            if hasattr(signal, 'blend_ratio') and signal.blend_ratio is not None:
                blend_str = f" (blend: {signal.blend_ratio:.1%} risky)"
            confidence_str = ""
            if hasattr(signal, 'confidence'):
                confidence_str = f" confidence={signal.confidence:.2f}"
            
            logger.info(f"     📈 {direction_str} {signal.symbol}{reason_str}{blend_str}")
            logger.info(f"        Price: ${current_price:.2f} → ${execution_price:.2f} (slippage: {self.slippage:.3%})")
            logger.info(f"        Signal: strength={signal.strength:.2f}{confidence_str}")
            logger.info(f"        Position Size: ${position_size_dollars:,.2f}")
            logger.info(f"        Shares: {shares:.2f}")
            logger.info(f"        Commission: ${commission_cost:.2f}")
            logger.info(f"        Total Cost: ${total_cost:,.2f}")
            
            # If total cost exceeds available cash, reduce position size
            if total_cost > self.cash:
                # Calculate maximum position size that fits within available cash
                # position_size + (position_size * commission) <= cash
                # position_size * (1 + commission) <= cash
                # position_size <= cash / (1 + commission)
                max_position_size = self.cash / (1 + self.commission)
                position_size_dollars = min(position_size_dollars, max_position_size)
                shares = position_size_dollars / execution_price
                commission_cost = position_size_dollars * self.commission
                total_cost = position_size_dollars + commission_cost
                
                # Ensure total cost doesn't exceed cash due to floating point precision
                if total_cost > self.cash:
                    # Reduce position size by a small amount to account for precision
                    position_size_dollars = self.cash - (position_size_dollars * self.commission)
                    position_size_dollars = max(0, position_size_dollars)  # Ensure non-negative
                    shares = position_size_dollars / execution_price
                    commission_cost = position_size_dollars * self.commission
                    total_cost = position_size_dollars + commission_cost
            
            # Check if we have enough cash (with small tolerance for floating point precision)
            if total_cost > remaining_cash + 1e-6 or position_size_dollars <= 0:
                logger.warning(f"     ❌ SKIPPED {direction_str} {signal.symbol} - Insufficient cash")
                logger.warning(f"        Required: ${total_cost:,.2f}, Available: ${remaining_cash:,.2f}")
                continue
            
            # Deduct from remaining tracker now (engine cash updates after execution)
            remaining_cash = max(0.0, remaining_cash - total_cost)
            batch_total_cost += total_cost
            logger.info(
                f"  {signal.symbol}: target={target_pct*100:.2f}%, desired=${desired_dollars:,.2f}, scaled=${position_size_dollars:,.2f}, price=${execution_price:,.4f}, shares={shares:.6f}, cost=${total_cost:,.2f}, cash_left=${remaining_cash:,.2f}"
            )
            
            # Execute trade
            if signal.symbol in self.positions:
                # Adjust existing position
                self._adjust_position(
                    signal.symbol,
                    shares,
                    execution_price,
                    current_date
                )
                logger.info(f"        ✅ Position adjusted successfully")
            else:
                # Open new position
                self._open_position(
                    signal.symbol,
                    shares,
                    execution_price,
                    current_date
                )
                logger.info(f"        ✅ Position opened successfully")
            
            # Deduct cash (keep engine cash in sync with remaining tracker)
            self.cash -= total_cost
            logger.info(f"        💰 Cash remaining: ${self.cash:,.2f}")

        logger.info(f"[ORDER SIZING] Batch total cost=${batch_total_cost:,.2f}, Cash end=${self.cash:,.2f}")
    
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
    
    def _log_position_changes(
        self,
        positions_before: Dict[str, Position],
        positions_after: Dict[str, Position],
        current_date: datetime
    ) -> None:
        """Log detailed position changes during rebalancing."""
        # Find positions that were closed
        closed_positions = set(positions_before.keys()) - set(positions_after.keys())
        if closed_positions:
            logger.info("   Positions Closed:")
            for symbol in closed_positions:
                pos = positions_before[symbol]
                market_value = pos.quantity * pos.current_price
                pnl = (pos.current_price - pos.entry_price) * pos.quantity
                logger.info(f"     {symbol}: {pos.quantity:.2f} shares @ ${pos.current_price:.2f} "
                          f"(Value: ${market_value:,.2f}, P&L: ${pnl:,.2f})")
        
        # Find positions that were opened
        opened_positions = set(positions_after.keys()) - set(positions_before.keys())
        if opened_positions:
            logger.info("   Positions Opened:")
            for symbol in opened_positions:
                pos = positions_after[symbol]
                market_value = pos.quantity * pos.current_price
                logger.info(f"     {symbol}: {pos.quantity:.2f} shares @ ${pos.current_price:.2f} "
                          f"(Value: ${market_value:,.2f})")
        
        # Find positions that were adjusted
        adjusted_positions = set(positions_before.keys()) & set(positions_after.keys())
        for symbol in adjusted_positions:
            pos_before = positions_before[symbol]
            pos_after = positions_after[symbol]
            if pos_before.quantity != pos_after.quantity:
                quantity_change = pos_after.quantity - pos_before.quantity
                action = "Increased" if quantity_change > 0 else "Reduced"
                logger.info(f"   Position Adjusted:")
                logger.info(f"     {symbol}: {action} by {abs(quantity_change):.2f} shares "
                          f"({pos_before.quantity:.2f} → {pos_after.quantity:.2f})")
        
        # If no changes, log that
        if not closed_positions and not opened_positions and not any(
            positions_before.get(symbol, Position("", 0, 0, current_date, 0, current_date, {})).quantity != 
            positions_after.get(symbol, Position("", 0, 0, current_date, 0, current_date, {})).quantity
            for symbol in adjusted_positions
        ):
            logger.info("   No position changes made")
    
    def _generate_results(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        benchmark_data: Optional[PriceData] = None
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
                    'entry_timestamp': t.entry_timestamp,
                    'exit_timestamp': t.exit_timestamp,
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
        
        # Calculate benchmark returns if provided
        benchmark_returns = None
        if benchmark_data is not None:
            benchmark_prices = benchmark_data.data['close'].reindex(equity_series.index).fillna(method='ffill')
            benchmark_returns = benchmark_prices.pct_change().dropna()
        
        # Calculate metrics
        from .performance import PerformanceCalculator
        calculator = PerformanceCalculator()
        metrics = calculator.calculate_metrics(
            returns,
            equity_series,
            self.risk_free_rate,
            benchmark_returns=benchmark_returns
        )
        
        # Convert position history to DataFrame
        positions_df = self._create_positions_dataframe()
        
        # Debug logging for position data
        logger.info("=" * 60)
        logger.info("POSITION DATA SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total timesteps in backtest: {len(equity_series)}")
        logger.info(f"Position history snapshots recorded: {len(self.position_history)}")
        logger.info(f"Positions DataFrame shape: {positions_df.shape}")
        
        if not positions_df.empty:
            logger.info(f"Positions DataFrame columns: {positions_df.columns.tolist()}")
            logger.info("First 3 rows of positions data:")
            logger.info(f"\n{positions_df.head(3)}")
            logger.info("Last 3 rows of positions data:")
            logger.info(f"\n{positions_df.tail(3)}")
        else:
            logger.warning("⚠️  Positions DataFrame is EMPTY!")
            logger.warning("This means no position history was recorded during the backtest.")
            if len(self.position_history) == 0:
                logger.error("❌ position_history list is empty - _record_position_snapshot was never called!")
            else:
                logger.error(f"❌ position_history has {len(self.position_history)} entries but DataFrame is empty!")
        logger.info("=" * 60)
        
        # Create result object
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.equity_curve[-1] if self.equity_curve else self.initial_capital,
            returns=returns,
            positions=positions_df,
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
