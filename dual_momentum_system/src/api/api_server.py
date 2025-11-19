"""
FastAPI REST API server for backtesting.

Provides HTTP endpoints for:
- Running backtests
- Retrieving results
- Managing strategies and universes
- Validating configurations
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from loguru import logger

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.engine import BacktestEngine
from src.backtesting.performance import PerformanceCalculator
from src.config.config_api import get_config_api
from src.data_sources import get_default_data_source
from src.core.plugin_manager import get_plugin_manager
from src.backtesting.utils import (
    calculate_data_fetch_dates,
    ensure_safe_asset_data,
    prepare_backtest_data
)
from src.agents.strategy_comparison_agent import (
    StrategyComparisonAgent,
    ComparisonConfig
)
from .serializers import BacktestResultSerializer

# In-memory storage for backtest results (use Redis/DB in production)
_backtest_results: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class BacktestRequest(BaseModel):
    """Request model for running a backtest."""
    
    strategy_id: str = Field(..., description="Strategy identifier (e.g., 'dual_momentum_classic')")
    universe: List[str] = Field(..., description="List of asset symbols to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    
    # Optional strategy parameters
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Custom strategy parameters")
    
    # Optional engine parameters
    initial_capital: float = Field(100000.0, description="Initial capital")
    commission: float = Field(0.001, description="Commission rate (0.001 = 0.1%)")
    slippage: float = Field(0.0005, description="Slippage rate (0.0005 = 0.05%)")
    risk_free_rate: float = Field(0.0, description="Risk-free rate for Sharpe calculation")
    
    # Optional benchmark
    benchmark_symbol: Optional[str] = Field(None, description="Benchmark symbol (e.g., 'SPY')")
    
    # Optional data source config
    api_keys: Optional[Dict[str, str]] = Field(None, description="API keys for data sources")
    
    @validator('start_date', 'end_date')
    def validate_date(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate end_date is after start_date."""
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end <= start:
                raise ValueError('end_date must be after start_date')
        return v


class BacktestResponse(BaseModel):
    """Response model for backtest submission."""
    
    backtest_id: str = Field(..., description="Unique backtest identifier")
    status: str = Field(..., description="Status: 'queued', 'running', 'completed', 'failed'")
    message: str = Field(..., description="Status message")


class BacktestStatusResponse(BaseModel):
    """Response model for backtest status."""
    
    backtest_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# FastAPI App
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Dual Momentum Backtesting API",
        description="REST API for programmatic backtesting of momentum strategies",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


# Get app instance
app = create_app()


# ============================================================================
# Helper Functions
# ============================================================================

def _run_backtest_task(backtest_id: str, request: BacktestRequest):
    """Background task to run backtest."""
    
    try:
        # Update status to running
        _backtest_results[backtest_id]['status'] = 'running'
        _backtest_results[backtest_id]['message'] = 'Backtest started'
        
        logger.info(f"[API] Starting backtest {backtest_id}")
        
        # Parse dates
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
        
        # Get config API
        config_api = get_config_api()
        
        # Create strategy
        success, strategy, msg = config_api.create_configured_strategy(
            strategy_id=request.strategy_id,
            custom_params=request.strategy_params
        )
        
        if not success:
            raise ValueError(f"Failed to create strategy: {msg}")
        
        # Update universe if provided
        if request.universe:
            if hasattr(strategy, 'config'):
                strategy.config['universe'] = request.universe
            elif hasattr(strategy, 'universe'):
                strategy.universe = request.universe
        
        # Get data source
        data_source = get_default_data_source(request.api_keys or {})
        
        # Calculate data fetch dates (include warm-up period)
        required_history = strategy.get_required_history()
        data_fetch_start, data_fetch_end = calculate_data_fetch_dates(
            backtest_start_date=start_date,
            backtest_end_date=end_date,
            lookback_period=required_history,
            safety_factor=1.5
        )
        
        # Fetch price data
        logger.info(f"[API] Fetching data for {len(request.universe)} symbols")
        _backtest_results[backtest_id]['message'] = 'Fetching market data...'
        
        price_data = {}
        plugin_manager = get_plugin_manager()
        EquityAsset = plugin_manager.get_asset_class('EquityAsset')
        asset_class = EquityAsset() if EquityAsset else None
        
        for symbol in request.universe:
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
                    # Fallback: create PriceData directly
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
                logger.warning(f"[API] Failed to fetch data for {symbol}: {e}")
        
        if not price_data:
            raise ValueError("No price data available for any symbols")
        
        # Ensure safe asset data if configured
        if hasattr(strategy, 'safe_asset') and strategy.safe_asset:
            ensure_safe_asset_data(
                strategy=strategy,
                price_data=price_data,
                data_source=data_source,
                start_date=data_fetch_start,
                end_date=data_fetch_end
            )
        
        # Fetch benchmark data if specified
        benchmark_data = None
        if request.benchmark_symbol:
            try:
                raw_benchmark = data_source.fetch_data(
                    symbol=request.benchmark_symbol,
                    start_date=data_fetch_start,
                    end_date=data_fetch_end,
                    timeframe='1d'
                )
                if not raw_benchmark.empty and asset_class:
                    benchmark_data = asset_class.normalize_data(raw_benchmark, request.benchmark_symbol)
                elif not raw_benchmark.empty:
                    from src.core.types import PriceData, AssetMetadata, AssetType
                    benchmark_data = PriceData(
                        symbol=request.benchmark_symbol,
                        data=raw_benchmark,
                        metadata=AssetMetadata(
                            symbol=request.benchmark_symbol,
                            name=request.benchmark_symbol,
                            asset_type=AssetType.EQUITY
                        )
                    )
            except Exception as e:
                logger.warning(f"[API] Failed to fetch benchmark data: {e}")
        
        # Run backtest
        logger.info(f"[API] Running backtest engine")
        _backtest_results[backtest_id]['message'] = 'Running backtest...'
        
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
            risk_free_rate=request.risk_free_rate
        )
        
        results = engine.run(
            strategy=strategy,
            price_data=price_data,
            start_date=start_date,
            end_date=end_date,
            benchmark_data=benchmark_data
        )
        
        # Serialize results
        logger.info(f"[API] Serializing results")
        serializer = BacktestResultSerializer()
        serialized_results = serializer.serialize(results)
        
        # Store results
        _backtest_results[backtest_id]['status'] = 'completed'
        _backtest_results[backtest_id]['message'] = 'Backtest completed successfully'
        _backtest_results[backtest_id]['result'] = serialized_results
        _backtest_results[backtest_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"[API] Backtest {backtest_id} completed successfully")
        
    except Exception as e:
        logger.error(f"[API] Backtest {backtest_id} failed: {e}", exc_info=True)
        _backtest_results[backtest_id]['status'] = 'failed'
        _backtest_results[backtest_id]['message'] = f'Backtest failed: {str(e)}'
        _backtest_results[backtest_id]['error'] = str(e)
        _backtest_results[backtest_id]['completed_at'] = datetime.now().isoformat()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Dual Momentum Backtesting API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "operational"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/backtest/run", response_model=BacktestResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Run a backtest asynchronously.
    
    Returns immediately with a backtest ID. Use GET /api/backtest/{id} to check status.
    """
    # Generate unique ID
    backtest_id = str(uuid.uuid4())
    
    # Initialize result storage
    _backtest_results[backtest_id] = {
        'backtest_id': backtest_id,
        'status': 'queued',
        'message': 'Backtest queued',
        'request': request.dict(),
        'created_at': datetime.now().isoformat(),
        'result': None,
        'error': None,
    }
    
    # Start background task
    background_tasks.add_task(_run_backtest_task, backtest_id, request)
    
    logger.info(f"[API] Queued backtest {backtest_id} for strategy {request.strategy_id}")
    
    return BacktestResponse(
        backtest_id=backtest_id,
        status='queued',
        message='Backtest queued successfully'
    )


@app.get("/api/backtest/{backtest_id}", response_model=BacktestStatusResponse)
async def get_backtest_status(backtest_id: str, summary: bool = False):
    """
    Get backtest status and results.
    
    Args:
        backtest_id: Backtest identifier
        summary: If True, return only summary metrics (faster)
    """
    if backtest_id not in _backtest_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest {backtest_id} not found"
        )
    
    result_data = _backtest_results[backtest_id]
    
    # If completed and summary requested, return only summary
    if summary and result_data['status'] == 'completed' and result_data['result']:
        serializer = BacktestResultSerializer()
        # Reconstruct minimal result for summary
        from src.core.types import BacktestResult
        # We can't easily reconstruct, so just return the full result
        # In production, you'd store the BacktestResult object
        result = result_data['result']
    else:
        result = result_data['result']
    
    return BacktestStatusResponse(
        backtest_id=backtest_id,
        status=result_data['status'],
        message=result_data.get('message'),
        result=result,
        error=result_data.get('error')
    )


@app.get("/api/strategies")
async def list_strategies():
    """List all available strategies."""
    config_api = get_config_api()
    strategies = config_api.get_all_strategies()
    return {"strategies": strategies}


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get strategy information."""
    config_api = get_config_api()
    strategy_info = config_api.get_strategy(strategy_id)
    
    if not strategy_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )
    
    return strategy_info


@app.get("/api/universes")
async def list_universes():
    """List all available universes."""
    config_api = get_config_api()
    universes = config_api.get_all_universes()
    return {"universes": universes}


@app.get("/api/universes/{universe_id}")
async def get_universe(universe_id: str):
    """Get universe information."""
    config_api = get_config_api()
    universe_info = config_api.get_universe(universe_id)
    
    if not universe_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Universe {universe_id} not found"
        )
    
    return universe_info


@app.post("/api/backtest/validate")
async def validate_backtest(request: BacktestRequest):
    """
    Validate backtest configuration without running it.
    
    Returns validation errors and warnings.
    """
    errors = []
    warnings = []
    
    try:
        # Validate strategy exists
        config_api = get_config_api()
        strategy_info = config_api.get_strategy(request.strategy_id)
        
        if not strategy_info:
            errors.append(f"Strategy '{request.strategy_id}' not found")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Validate dates
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
        
        if end_date <= start_date:
            errors.append("end_date must be after start_date")
        
        if (end_date - start_date).days < 30:
            warnings.append("Backtest period is less than 30 days - results may not be meaningful")
        
        # Validate universe
        if not request.universe:
            errors.append("Universe cannot be empty")
        elif len(request.universe) < 1:
            errors.append("Universe must contain at least one symbol")
        
        # Check data availability (basic check)
        if request.universe:
            data_source = get_default_data_source(request.api_keys or {})
            # Note: Full data availability check would require fetching, which is expensive
            # This is a lightweight validation
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings
        }


@app.delete("/api/backtest/{backtest_id}")
async def delete_backtest(backtest_id: str):
    """Delete a backtest result."""
    if backtest_id not in _backtest_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest {backtest_id} not found"
        )
    
    del _backtest_results[backtest_id]
    return {"message": f"Backtest {backtest_id} deleted"}


@app.get("/api/backtests")
async def list_backtests(limit: int = 50):
    """List recent backtests."""
    backtests = list(_backtest_results.values())
    # Sort by creation time (newest first)
    backtests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Return summary for each
    summaries = []
    for bt in backtests[:limit]:
        summaries.append({
            'backtest_id': bt['backtest_id'],
            'status': bt['status'],
            'strategy_id': bt['request'].get('strategy_id'),
            'created_at': bt.get('created_at'),
            'completed_at': bt.get('completed_at'),
        })
    
    return {"backtests": summaries, "total": len(_backtest_results)}


class StrategyComparisonRequest(BaseModel):
    """Request model for strategy comparison."""
    
    universe: List[str] = Field(..., description="List of asset symbols")
    benchmark_symbol: str = Field(..., description="Benchmark symbol")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    
    # Optional filters
    strategy_ids: Optional[List[str]] = Field(None, description="Specific strategies to test (all if None)")
    exclude_strategy_ids: Optional[List[str]] = Field(None, description="Strategies to exclude")
    
    # Comparison criteria
    min_excess_return: float = Field(0.0, description="Minimum excess return to be considered outperforming")
    min_sharpe_ratio: Optional[float] = Field(None, description="Minimum Sharpe ratio")
    
    # Engine parameters
    initial_capital: float = Field(100000.0, description="Initial capital")
    commission: float = Field(0.001, description="Commission rate")
    slippage: float = Field(0.0005, description="Slippage rate")
    risk_free_rate: float = Field(0.0, description="Risk-free rate")
    
    # Execution
    max_workers: int = Field(4, description="Number of parallel workers")
    parallel: bool = Field(True, description="Run in parallel")
    
    # Data source
    api_keys: Optional[Dict[str, str]] = Field(None, description="API keys for data sources")
    
    @validator('start_date', 'end_date')
    def validate_date(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


@app.post("/api/strategies/compare", status_code=status.HTTP_202_ACCEPTED)
async def compare_strategies(request: StrategyComparisonRequest, background_tasks: BackgroundTasks):
    """
    Compare all strategies against a benchmark.
    
    Runs asynchronously. Returns immediately with a comparison ID.
    Use GET /api/strategies/compare/{id} to check status.
    """
    comparison_id = str(uuid.uuid4())
    
    # Store comparison request
    _backtest_results[comparison_id] = {
        'comparison_id': comparison_id,
        'status': 'queued',
        'message': 'Strategy comparison queued',
        'request': request.dict(),
        'created_at': datetime.now().isoformat(),
        'results': None,
        'error': None,
    }
    
    # Start background task
    background_tasks.add_task(_run_strategy_comparison, comparison_id, request)
    
    logger.info(f"[API] Queued strategy comparison {comparison_id}")
    
    return {
        "comparison_id": comparison_id,
        "status": "queued",
        "message": "Strategy comparison queued successfully"
    }


def _run_strategy_comparison(comparison_id: str, request: StrategyComparisonRequest):
    """Background task to run strategy comparison."""
    try:
        _backtest_results[comparison_id]['status'] = 'running'
        _backtest_results[comparison_id]['message'] = 'Running strategy comparison...'
        
        # Parse dates
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
        
        # Create config
        config = ComparisonConfig(
            start_date=start_date,
            end_date=end_date,
            universe=request.universe,
            benchmark_symbol=request.benchmark_symbol,
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage,
            risk_free_rate=request.risk_free_rate,
            strategy_ids=request.strategy_ids,
            exclude_strategy_ids=request.exclude_strategy_ids,
            min_excess_return=request.min_excess_return,
            min_sharpe_ratio=request.min_sharpe_ratio,
            max_workers=request.max_workers,
            parallel=request.parallel,
            api_keys=request.api_keys
        )
        
        # Run comparison
        agent = StrategyComparisonAgent()
        results = agent.compare_all_strategies(config)
        
        # Serialize results
        serialized_results = [r.to_dict() for r in results]
        
        # Get outperforming strategies
        outperforming = agent.get_outperforming_strategies(results, config)
        outperforming_dicts = [r.to_dict() for r in outperforming]
        
        # Store results
        _backtest_results[comparison_id]['status'] = 'completed'
        _backtest_results[comparison_id]['message'] = 'Strategy comparison completed'
        _backtest_results[comparison_id]['results'] = {
            'all_results': serialized_results,
            'outperforming': outperforming_dicts,
            'summary': {
                'total': len(results),
                'successful': sum(1 for r in results if r.success),
                'outperforming': len(outperforming)
            }
        }
        _backtest_results[comparison_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"[API] Strategy comparison {comparison_id} completed")
        
    except Exception as e:
        logger.error(f"[API] Strategy comparison {comparison_id} failed: {e}", exc_info=True)
        _backtest_results[comparison_id]['status'] = 'failed'
        _backtest_results[comparison_id]['message'] = f'Comparison failed: {str(e)}'
        _backtest_results[comparison_id]['error'] = str(e)
        _backtest_results[comparison_id]['completed_at'] = datetime.now().isoformat()


@app.get("/api/strategies/compare/{comparison_id}")
async def get_comparison_status(comparison_id: str):
    """Get strategy comparison status and results."""
    if comparison_id not in _backtest_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison {comparison_id} not found"
        )
    
    result_data = _backtest_results[comparison_id]
    
    return {
        "comparison_id": comparison_id,
        "status": result_data['status'],
        "message": result_data.get('message'),
        "results": result_data.get('results'),
        "error": result_data.get('error'),
        "created_at": result_data.get('created_at'),
        "completed_at": result_data.get('completed_at'),
    }


def get_app() -> FastAPI:
    """Get the FastAPI app instance."""
    return app

