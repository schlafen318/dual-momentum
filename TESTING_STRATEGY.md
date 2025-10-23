# Comprehensive Testing Strategy

## Overview

This document outlines our multi-layered testing strategy to prevent bugs like the "sell-before-buy" execution order issue from happening again.

## Testing Pyramid

```
        /\
       /  \      E2E Tests (Few)
      /----\     - Full system integration
     /------\    - Real-world scenarios
    /--------\   
   /----------\  Integration Tests (Some)
  /------------\ - Component interactions
 /--------------\- Realistic data flows
/----------------\
|   Unit Tests    | (Many)
|   - Functions   |
|   - Classes     |
|   - Edge cases  |
\----------------/
```

---

## 1. Unit Tests

### Purpose
Test individual functions and methods in isolation.

### Coverage Areas

#### Critical Functions
- [x] `_execute_signals()` - Execution order logic
- [x] Weight normalization (`lines 710-720`)
- [x] Risk share calculation (`line 705`)
- [x] Position sizing logic
- [x] Transaction cost calculations

#### Test Files
- `tests/test_rebalancing_execution_order.py` ✅ **NEW**
- `tests/test_backtest_engine.py` (expand)
- `tests/test_dual_momentum.py` (expand)

### Examples

```python
def test_sell_signals_before_buy_signals():
    """Verify sells are executed before buys."""
    sells = [signal1, signal2]
    buys = [signal3, signal4]
    execution_order = separate_signals(signals)
    assert execution_order[:2] == sells
    assert execution_order[2:] == buys

def test_risk_share_calculation():
    """Test risk_share < 1.0 when included < desired."""
    included_count = 2
    desired_positions = 3
    risk_share = calculate_risk_share(included_count, desired_positions)
    assert risk_share == 2/3
```

---

## 2. Integration Tests

### Purpose
Test interactions between components with realistic data.

### Coverage Areas

#### Cash Management
- [x] Cash never goes negative ✅ **NEW**
- [x] Portfolio value consistency ✅ **NEW**
- [x] Transaction costs within bounds ✅ **NEW**
- [x] No excessive cash drag ✅ **NEW**

#### Rebalancing Scenarios
- [ ] Full rotation (sell all, buy new)
- [ ] Partial rotation (adjust positions)
- [ ] Defensive mode (go to cash/safe asset)
- [ ] Exit defensive mode (redeploy)

#### Test Files
- `tests/test_cash_management_integration.py` ✅ **NEW**
- `tests/test_rebalancing_scenarios.py` (create)

### Examples

```python
def test_full_rotation_maintains_value():
    """Test rotating from SPY/DIA/IWM to QQQ/AAPL/MSFT."""
    # Run backtest with rotation
    # Verify portfolio value unchanged (minus costs)
    # Verify full deployment (no cash drag)

def test_defensive_then_offensive():
    """Test going defensive, then back to risky assets."""
    # Simulate bear market → defensive
    # Then bull market → back to equities
    # Verify smooth transitions
```

---

## 3. Property-Based Tests

### Purpose
Test invariants that should always hold, using generated inputs.

### Tool
[Hypothesis](https://hypothesis.readthedocs.io/) (Python)

### Properties to Test

```python
@given(prices=price_data_strategy(), positions=position_strategy())
def test_cash_never_negative(prices, positions):
    """Property: Cash >= 0 always."""
    engine = BacktestEngine(initial_capital=100000)
    # ... execute ...
    assert engine.cash >= 0

@given(signals=signal_strategy())
def test_weights_sum_to_one(signals):
    """Property: Normalized weights sum to 1.0."""
    weights = normalize_weights(signals, risk_share=1.0)
    assert abs(sum(weights.values()) - 1.0) < 1e-10

@given(portfolio_value=st.floats(1000, 1000000))
def test_portfolio_value_conservation(portfolio_value):
    """Property: PV before = PV after rebalancing (minus costs)."""
    # ... rebalance ...
    # assert abs(pv_after - pv_before) <= transaction_costs
```

---

## 4. Regression Tests

### Purpose
Ensure fixed bugs don't reappear.

### Strategy

1. **For each bug found:**
   - Write a failing test that reproduces it
   - Fix the bug
   - Keep the test permanently

2. **Bug Database:**
   - `tests/regressions/` directory
   - Each file named after the bug: `test_bug_sell_before_buy.py`

### Example

```python
def test_regression_sell_before_buy():
    """
    Regression test for sell-before-buy execution order bug.
    
    Bug ID: #2025-10-23-001
    Description: Buy orders failed when sells would have provided cash
    Fix: Execute sells before buys in rebalancing
    """
    # Exact scenario that exposed the bug
    result = run_backtest_with_scenario(...)
    assert result.positions['cash_pct'].iloc[0] < 1.0
```

---

## 5. End-to-End Tests

### Purpose
Test complete workflows from user perspective.

### Scenarios

#### Streamlit UI Tests
```python
def test_ui_complete_backtest_workflow():
    """Test: Select symbols → Configure → Run → View results"""
    # Use selenium or streamlit testing
    # Verify no errors, results displayed correctly

def test_ui_default_settings_produce_valid_results():
    """Test that default settings work out of the box."""
    # This would have caught the 7.52% cash bug!
```

#### CLI Tests
```python
def test_cli_run_backtest_command():
    """Test: python -m src.cli run-backtest --config=..."""
    # Verify command succeeds
    # Check output files created
```

---

## 6. Performance/Benchmark Tests

### Purpose
Ensure changes don't degrade performance.

### Metrics to Track
- Backtest execution time
- Memory usage
- Number of trades executed
- Accuracy vs vectorized implementation

### Implementation

```python
@pytest.mark.benchmark
def test_backtest_performance(benchmark):
    """Benchmark backtest execution time."""
    result = benchmark(run_standard_backtest)
    assert result.time < 5.0  # Should complete in < 5 seconds
```

---

## 7. Code Review Checklist

### Before Merging Code

- [ ] All new code has unit tests
- [ ] Integration tests pass
- [ ] No regression in existing tests
- [ ] Code coverage >= 80% for new code
- [ ] Performance benchmarks pass
- [ ] Documentation updated

### Critical Areas Requiring Extra Scrutiny

1. **Cash/Money Flow Logic**
   - Double-check arithmetic
   - Verify cash never goes negative
   - Test with zero cash scenarios

2. **Execution Order Logic**
   - Verify dependencies are correct
   - Test edge cases (all sells, all buys, mixed)

3. **Weight/Allocation Calculations**
   - Test edge cases (1 asset, many assets, 0 assets)
   - Verify sums to 100%
   - Handle division by zero

---

## 8. Continuous Integration (CI)

### Automated Testing Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov hypothesis
    
    - name: Run unit tests
      run: pytest tests/ -v --cov=src --cov-report=term-missing
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
    
    - name: Check code coverage
      run: |
        coverage report --fail-under=80
    
    - name: Run linting
      run: |
        pip install flake8 mypy
        flake8 src/
        mypy src/ --ignore-missing-imports
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/test_rebalancing_execution_order.py -v
        language: system
        pass_filenames: false
        always_run: true
```

---

## 9. Test Data Management

### Fixtures and Factories

```python
# tests/conftest.py

import pytest
from datetime import datetime
import pandas as pd

@pytest.fixture
def sample_price_data():
    """Reusable price data for tests."""
    # ... generate standard test data ...
    return data

@pytest.fixture
def edge_case_price_data():
    """Edge case: Extreme volatility, gaps, etc."""
    return data

@pytest.fixture
def realistic_multi_year_data():
    """Multi-year realistic data for integration tests."""
    return data
```

### Test Data Versioning
- Store golden datasets in `tests/data/`
- Version control test data
- Document data generation process

---

## 10. Monitoring and Alerting

### Production Monitoring (if deployed)

```python
def log_cash_allocation_metrics(results):
    """Log metrics to catch issues in production."""
    avg_cash = results.positions['cash_pct'].mean()
    max_cash = results.positions['cash_pct'].max()
    
    # Alert if anomalous
    if avg_cash > 1.0:
        logger.warning(f"High average cash: {avg_cash:.2f}%")
        send_alert("High cash drag detected")
```

### Health Checks
- Daily/Weekly automated backtest runs
- Compare results against benchmarks
- Alert on significant deviations

---

## 11. Documentation

### Test Documentation Standards

Each test should have:
1. **Descriptive name**: `test_sell_before_buy_execution_order`
2. **Docstring**: What it tests and why
3. **Clear assertions**: What conditions must hold
4. **Comments**: Explain non-obvious logic

### Example

```python
def test_sell_before_buy_execution_order(self):
    """
    Test that sells execute before buys during rebalancing.
    
    WHY: Ensures cash from sales is available for purchases in
    the same rebalancing event.
    
    BUG REFERENCE: #2025-10-23-001
    
    SCENARIO:
    1. Start with positions in SPY, DIA, IWM
    2. Rebalance to QQQ (new), SPY (reduced), DIA (reduced)
    3. Verify QQQ buy succeeds (sells happened first)
    
    ASSERTIONS:
    - Cash allocation < 1%
    - All target positions opened successfully
    - Portfolio value conserved (minus transaction costs)
    """
    # ... test code ...
```

---

## 12. Test Metrics to Track

### Coverage Metrics
- **Line coverage**: Goal 80%+
- **Branch coverage**: Goal 70%+
- **Critical path coverage**: Goal 100%

### Quality Metrics
- **Test pass rate**: Goal 100%
- **Flaky test rate**: Goal < 1%
- **Test execution time**: Monitor trends

### Bug Metrics
- **Time to detect**: Measure
- **Escaped to production**: Track
- **Regression rate**: Monitor

---

## Implementation Checklist

### Immediate (Week 1)
- [x] Create `test_rebalancing_execution_order.py` ✅
- [x] Create `test_cash_management_integration.py` ✅
- [ ] Run tests and fix any failures
- [ ] Add to CI pipeline
- [ ] Set up pre-commit hooks

### Short-term (Month 1)
- [ ] Add property-based tests with Hypothesis
- [ ] Create regression test suite
- [ ] Achieve 80% code coverage
- [ ] Document all critical test scenarios

### Long-term (Quarter 1)
- [ ] E2E tests for Streamlit UI
- [ ] Performance benchmarking suite
- [ ] Automated golden dataset updates
- [ ] Production monitoring dashboard

---

## Best Practices

### Test-Driven Development (TDD)

For new features:
1. **Write failing test first**
2. Implement minimum code to pass
3. Refactor while keeping tests green

### Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### Test Readability
- One assertion per test (when possible)
- Clear arrange-act-assert structure
- Descriptive variable names

### Test Maintenance
- Remove obsolete tests
- Update tests when requirements change
- Refactor duplicate test code

---

## Resources

### Testing Tools
- **pytest**: Test runner
- **pytest-cov**: Coverage reporting
- **hypothesis**: Property-based testing
- **pytest-benchmark**: Performance testing
- **pytest-mock**: Mocking utilities

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

---

## Conclusion

By implementing this comprehensive testing strategy, we create multiple layers of defense against bugs:

1. **Unit tests** catch logic errors early
2. **Integration tests** catch interaction bugs
3. **Property tests** catch edge cases we didn't think of
4. **Regression tests** prevent bugs from returning
5. **E2E tests** verify user workflows
6. **CI/CD** automates verification
7. **Code review** adds human judgment

**The sell-before-buy bug would have been caught by:**
- `test_sell_before_buy_execution_order()` ✅
- `test_cash_availability_during_rotation()` ✅
- `test_no_excessive_cash_drag()` ✅

With these tests in place, similar bugs cannot slip through again.

---

**Created:** 2025-10-23  
**Last Updated:** 2025-10-23  
**Owner:** Engineering Team
