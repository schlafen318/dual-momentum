# Unit Test Fixes

## Issues Fixed

### 1. ❌ Unknown config option: timeout

**Error:**
```
Unknown config option: timeout
```

**Root Cause:**
The `pytest.ini` file had `timeout = 300` configured, but the `pytest-timeout` plugin was not installed in `requirements.txt`.

**Fix:**
Removed the timeout configuration from `pytest.ini` since the plugin is not included.

**File Modified:** `pytest.ini`
```diff
- # Timeout
- timeout = 300
```

### 2. ⚠️ pkg_resources deprecation warning

**Warning:**
```
pkg_resources is deprecated as an API
```

**Fix:**
Added warning filter to suppress this known deprecation warning from llvmlite/numba.

**File Modified:** `pytest.ini`
```diff
  filterwarnings =
      ignore::DeprecationWarning
      ignore::PendingDeprecationWarning
+     ignore::UserWarning:pkg_resources
```

## Changes Made

### pytest.ini
```python
# Before
[pytest]
# ... config ...
timeout = 300
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

# After
[pytest]
# ... config ...
# Removed timeout (requires pytest-timeout plugin not in requirements)
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::UserWarning:pkg_resources  # Suppress llvmlite warning
```

## Test Files Status

### ✅ test_vectorized_engine.py
- **Location**: `tests/test_vectorized_engine.py`
- **Status**: File exists and is properly structured
- **Tests**: 32 test methods across 5 test classes
- **Dependencies**: All imports valid (vectorized_engine, vectorized_metrics, advanced_analytics)

### Test Coverage:
1. **TestVectorizedBacktestEngine** (8 tests)
   - Engine initialization
   - Basic backtest execution
   - Zero signals handling
   - Signal-based strategies
   - Price data preparation
   - Multi-strategy comparison

2. **TestSignalGenerator** (4 tests)
   - Momentum signals
   - SMA crossover signals
   - Mean reversion signals
   - Equal weight signals

3. **TestVectorizedMetricsCalculator** (8 tests)
   - Calculator initialization
   - Comprehensive metrics
   - CAGR calculation
   - Sharpe ratio
   - Drawdown metrics
   - VaR and CVaR
   - Empty returns handling

4. **TestAdvancedAnalytics** (11 tests)
   - Analytics initialization
   - Rolling metrics
   - Monte Carlo simulation (bootstrap & parametric)
   - Regime detection (volatility & trend)
   - Drawdown analysis
   - Rolling correlation
   - Stress testing
   - Performance attribution

5. **TestIntegration** (1 test)
   - Complete backtest workflow

## How to Run Tests

### Locally (after installing dependencies):
```bash
cd /workspace/dual_momentum_system

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_vectorized_engine.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### In CI/CD:
```yaml
# GitHub Actions example
- name: Install dependencies
  run: |
    pip install -r requirements.txt

- name: Run tests
  run: |
    pytest -v --cov=src
```

## Expected Results After Fix

### Before Fix:
```
ERROR tests/test_vectorized_engine.py
Unknown config option: timeout
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
Exit code: 2
```

### After Fix:
```
tests/test_vectorized_engine.py::TestVectorizedBacktestEngine::test_engine_initialization PASSED
tests/test_vectorized_engine.py::TestVectorizedBacktestEngine::test_run_backtest_basic PASSED
... (all tests should pass or skip)
Exit code: 0
```

## Additional Recommendations

### 1. Add pytest-timeout if needed
If you want timeout protection for tests:

```bash
# Add to requirements.txt
pytest-timeout>=2.1.0

# Then use in pytest.ini
[pytest]
timeout = 300
timeout_method = thread
```

### 2. Optimize Test Performance
Some tests may be slow (Monte Carlo, rolling metrics):
```python
# Mark slow tests
@pytest.mark.slow
def test_monte_carlo_simulation(self, sample_returns):
    ...

# Run without slow tests
pytest -m "not slow"
```

### 3. Add Test Markers in pytest.ini
Already configured:
```ini
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take a long time to run
    requires_network: Tests that require network access
```

Usage:
```python
@pytest.mark.unit
def test_engine_initialization(self):
    ...

@pytest.mark.slow
@pytest.mark.integration
def test_complete_backtest_workflow(self):
    ...
```

## Remaining Warnings (Non-Critical)

### pkg_resources deprecation
```
pkg_resources is deprecated as an API
```
- **Source**: llvmlite/numba dependencies (from vectorbt)
- **Impact**: None (cosmetic warning)
- **Status**: Now filtered out

### Solution if warning persists:
The filter has been added to pytest.ini. If you still see it:
```bash
# Run with explicit warning suppression
pytest -W ignore::UserWarning
```

## Verification Checklist

After applying fixes:

- [x] Remove `timeout = 300` from pytest.ini
- [x] Add `ignore::UserWarning:pkg_resources` filter
- [x] Verify pytest.ini syntax
- [x] Confirm all test files exist
- [x] Check test file imports are valid
- [ ] Install dependencies and run tests
- [ ] Verify all tests pass or skip appropriately

## Files Modified

```
pytest.ini (2 changes)
  1. Removed timeout configuration
  2. Added pkg_resources warning filter
```

## Summary

✅ **Fixed**: Removed invalid `timeout` config option  
✅ **Fixed**: Suppressed pkg_resources deprecation warning  
✅ **Verified**: Test file structure is correct  
✅ **Verified**: All imports are valid  

**Next Step**: Install dependencies and run `pytest -v` to execute the tests.

---

**Status**: ✅ Configuration fixed  
**Impact**: Tests can now be collected and run  
**Breaking Changes**: None
