"""
REST API for programmatic backtesting.

This module provides HTTP endpoints for running backtests, accessing results,
and managing strategies and universes.
"""

from .api_server import create_app, get_app
from .serializers import BacktestResultSerializer

__all__ = [
    'create_app',
    'get_app',
    'BacktestResultSerializer',
]

