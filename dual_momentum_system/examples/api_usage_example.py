"""
Example usage of the REST API for backtesting.

This demonstrates how to use the programmatic API to run backtests
via HTTP requests.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API base URL (adjust for your deployment)
API_BASE_URL = "http://localhost:8000"


def example_run_backtest():
    """Example: Run a backtest via API."""
    
    print("=" * 80)
    print("REST API BACKTESTING EXAMPLE")
    print("=" * 80)
    print()
    
    # Prepare backtest request
    request_data = {
        "strategy_id": "dual_momentum_classic",
        "universe": ["SPY", "EFA", "EEM", "AGG"],
        "start_date": "2015-01-01",
        "end_date": "2024-01-01",
        "initial_capital": 100000.0,
        "commission": 0.001,
        "slippage": 0.0005,
        "benchmark_symbol": "SPY",
        "strategy_params": {
            "lookback_period": 252,
            "rebalancing_frequency": "monthly"
        }
    }
    
    print("1. Submitting backtest request...")
    print(f"   Strategy: {request_data['strategy_id']}")
    print(f"   Universe: {request_data['universe']}")
    print(f"   Period: {request_data['start_date']} to {request_data['end_date']}")
    print()
    
    # Submit backtest
    response = requests.post(
        f"{API_BASE_URL}/api/backtest/run",
        json=request_data
    )
    
    if response.status_code != 202:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    backtest_id = result['backtest_id']
    
    print(f"✅ Backtest queued successfully!")
    print(f"   Backtest ID: {backtest_id}")
    print(f"   Status: {result['status']}")
    print()
    
    # Poll for completion
    print("2. Waiting for backtest to complete...")
    max_wait = 300  # 5 minutes
    start_time = time.time()
    check_interval = 2  # Check every 2 seconds
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(
            f"{API_BASE_URL}/api/backtest/{backtest_id}"
        )
        
        if status_response.status_code != 200:
            print(f"❌ Error checking status: {status_response.status_code}")
            break
        
        status_data = status_response.json()
        status = status_data['status']
        
        if status == 'completed':
            print(f"✅ Backtest completed!")
            print()
            break
        elif status == 'failed':
            print(f"❌ Backtest failed: {status_data.get('error', 'Unknown error')}")
            return
        else:
            message = status_data.get('message', 'Running...')
            print(f"   Status: {status} - {message}")
            time.sleep(check_interval)
    else:
        print("⏱️  Timeout waiting for backtest to complete")
        return
    
    # Get results
    print("3. Retrieving results...")
    results_response = requests.get(
        f"{API_BASE_URL}/api/backtest/{backtest_id}"
    )
    
    if results_response.status_code != 200:
        print(f"❌ Error retrieving results: {results_response.status_code}")
        return
    
    results = results_response.json()
    result_data = results['result']
    
    # Display key metrics
    print()
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"Strategy: {result_data['strategy_name']}")
    print(f"Period: {result_data['start_date']} to {result_data['end_date']}")
    print()
    print("Performance Metrics:")
    print(f"  Initial Capital: ${result_data['initial_capital']:,.2f}")
    print(f"  Final Capital: ${result_data['final_capital']:,.2f}")
    print(f"  Total Return: {result_data['total_return']:.2%}")
    print(f"  Annualized Return: {result_data.get('annualized_return', 'N/A')}")
    if isinstance(result_data.get('annualized_return'), (int, float)):
        print(f"  Annualized Return: {result_data['annualized_return']:.2%}")
    print(f"  Sharpe Ratio: {result_data.get('sharpe_ratio', 'N/A')}")
    if isinstance(result_data.get('sharpe_ratio'), (int, float)):
        print(f"  Sharpe Ratio: {result_data['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {result_data.get('max_drawdown', 'N/A')}")
    if isinstance(result_data.get('max_drawdown'), (int, float)):
        print(f"  Max Drawdown: {result_data['max_drawdown']:.2%}")
    print(f"  Number of Trades: {len(result_data.get('trades', []))}")
    print()
    
    # Display additional metrics if available
    if result_data.get('metrics'):
        print("Additional Metrics:")
        for key, value in result_data['metrics'].items():
            if value is not None and isinstance(value, (int, float)):
                if 'ratio' in key.lower() or 'beta' in key.lower():
                    print(f"  {key}: {value:.2f}")
                elif 'return' in key.lower() or 'drawdown' in key.lower():
                    print(f"  {key}: {value:.2%}")
                else:
                    print(f"  {key}: {value:.2f}")
        print()


def example_list_strategies():
    """Example: List available strategies."""
    
    print("=" * 80)
    print("LISTING AVAILABLE STRATEGIES")
    print("=" * 80)
    print()
    
    response = requests.get(f"{API_BASE_URL}/api/strategies")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    strategies = data.get('strategies', {})
    
    print(f"Found {len(strategies)} strategies:")
    print()
    
    for strategy_id, info in strategies.items():
        print(f"  • {strategy_id}")
        if 'name' in info:
            print(f"    Name: {info['name']}")
        if 'description' in info:
            print(f"    Description: {info['description']}")
        print()


def example_list_universes():
    """Example: List available universes."""
    
    print("=" * 80)
    print("LISTING AVAILABLE UNIVERSES")
    print("=" * 80)
    print()
    
    response = requests.get(f"{API_BASE_URL}/api/universes")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    universes = data.get('universes', {})
    
    print(f"Found {len(universes)} universes:")
    print()
    
    for universe_id, info in universes.items():
        print(f"  • {universe_id}")
        if 'name' in info:
            print(f"    Name: {info['name']}")
        if 'symbols' in info:
            print(f"    Symbols: {info['symbols']}")
        print()


def example_validate_backtest():
    """Example: Validate backtest configuration."""
    
    print("=" * 80)
    print("VALIDATING BACKTEST CONFIGURATION")
    print("=" * 80)
    print()
    
    request_data = {
        "strategy_id": "dual_momentum_classic",
        "universe": ["SPY", "EFA", "EEM"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/backtest/validate",
        json=request_data
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    validation = response.json()
    
    if validation['valid']:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors:")
        for error in validation['errors']:
            print(f"   - {error}")
    
    if validation.get('warnings'):
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   - {warning}")


def main():
    """Run all examples."""
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API is not responding correctly")
            print(f"   Make sure the API server is running at {API_BASE_URL}")
            print(f"   Start it with: uvicorn src.api.main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_BASE_URL}")
        print(f"   Make sure the API server is running")
        print(f"   Start it with: uvicorn src.api.main:app --reload")
        return
    
    print("✅ API is available")
    print()
    
    # Run examples
    example_list_strategies()
    print()
    
    example_list_universes()
    print()
    
    example_validate_backtest()
    print()
    
    # Uncomment to run actual backtest (takes time)
    # example_run_backtest()


if __name__ == "__main__":
    main()

