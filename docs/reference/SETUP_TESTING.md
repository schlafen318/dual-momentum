# Setting Up the Testing Infrastructure

## Quick Start

```bash
# 1. Install testing dependencies
pip install pytest pytest-cov hypothesis pytest-benchmark pytest-mock

# 2. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 3. Run all tests
cd dual_momentum_system
pytest tests/ -v

# 4. Check coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Detailed Setup

### 1. Install Dependencies

```bash
# Core testing
pip install pytest==7.4.3
pip install pytest-cov==4.1.0
pip install pytest-mock==3.12.0

# Property-based testing
pip install hypothesis==6.92.1

# Performance testing
pip install pytest-benchmark==4.0.0

# Code quality
pip install flake8==6.1.0
pip install mypy==1.7.1
pip install black==23.11.0
pip install isort==5.12.0

# Security
pip install bandit==1.7.5
pip install safety==2.3.5

# Pre-commit hooks
pip install pre-commit==3.5.0
```

Or use the provided requirements:

```bash
pip install -r requirements-dev.txt
```

### 2. Configure Pre-commit Hooks

```bash
# Install the git hook scripts
pre-commit install

# Optionally, run against all files
pre-commit run --all-files
```

### 3. Run Tests Locally

```bash
cd dual_momentum_system

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rebalancing_execution_order.py -v

# Run specific test
pytest tests/test_rebalancing_execution_order.py::TestRebalancingExecutionOrder::test_sell_before_buy_execution_order -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run only fast tests
pytest tests/ -m "not slow"

# Run integration tests
pytest tests/test_cash_management_integration.py -v
```

### 4. View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## CI/CD Setup

### GitHub Actions

The `.github/workflows/tests.yml` file is already configured.

To enable:

1. Push your code to GitHub
2. GitHub Actions will automatically run on push/PR
3. View results in the "Actions" tab

### Required Secrets (if using private data)

```bash
# In GitHub repo settings > Secrets
CODECOV_TOKEN=<your_codecov_token>
```

---

## Writing New Tests

### Test File Structure

```python
"""
Module docstring explaining what this test file covers.
"""

import pytest
from datetime import datetime

# Import what you're testing
from src.backtesting.engine import BacktestEngine


class TestYourFeature:
    """Test suite for specific feature."""
    
    @pytest.fixture
    def setup_data(self):
        """Fixture providing test data."""
        return {...}
    
    def test_specific_behavior(self, setup_data):
        """
        Test that specific behavior works correctly.
        
        WHY: Explain why this test matters
        SCENARIO: Describe the test scenario
        ASSERTIONS: What conditions must hold
        """
        # Arrange
        engine = BacktestEngine(...)
        
        # Act
        result = engine.run(...)
        
        # Assert
        assert result.something == expected
```

### Test Naming Convention

```
test_<what>_<when>_<expected_outcome>
```

Examples:
- `test_sell_before_buy_execution_order()`
- `test_cash_never_goes_negative()`
- `test_weights_sum_to_one_with_three_positions()`

### Required Documentation

Every test must have:
1. **Docstring** explaining:
   - What it tests
   - Why it matters
   - Expected behavior

2. **Clear assertions** with helpful messages:
   ```python
   assert cash >= 0, f"Cash went negative: ${cash:.2f}"
   ```

3. **Comments** for non-obvious logic

---

## Test Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_long_running_backtest():
    pass

# Mark integration tests
@pytest.mark.integration
def test_full_system():
    pass

# Skip conditionally
@pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
def test_unix_specific():
    pass
```

Run specific markers:

```bash
# Run only fast tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

---

## Debugging Failed Tests

### 1. Run with verbose output

```bash
pytest tests/test_file.py -vv
```

### 2. Show print statements

```bash
pytest tests/test_file.py -s
```

### 3. Stop on first failure

```bash
pytest tests/test_file.py -x
```

### 4. Drop into debugger on failure

```bash
pytest tests/test_file.py --pdb
```

### 5. Show locals in tracebacks

```bash
pytest tests/test_file.py -l
```

### 6. Combine options

```bash
pytest tests/test_file.py -vv -s -x --pdb
```

---

## Continuous Testing (Watch Mode)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically on file changes
cd dual_momentum_system
ptw tests/ src/
```

---

## Coverage Goals

### Minimum Requirements

- **Overall coverage**: 70%
- **Critical modules**: 90%
  - `src/backtesting/engine.py`
  - `src/strategies/dual_momentum.py`
- **New code**: 80%

### Check coverage

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# Fail if below threshold
pytest --cov=src --cov-fail-under=70
```

### View uncovered lines

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Common Issues

### Issue: Tests pass locally but fail in CI

**Cause**: Different Python versions or dependencies

**Solution**:
```bash
# Use same Python version as CI
pyenv install 3.10
pyenv local 3.10

# Use exact dependency versions
pip install -r requirements.txt --no-cache-dir
```

### Issue: Tests are slow

**Cause**: Large datasets, inefficient tests

**Solution**:
```bash
# Mark slow tests
@pytest.mark.slow
def test_long_backtest():
    pass

# Run fast tests only
pytest -m "not slow"

# Parallelize
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

### Issue: Flaky tests

**Cause**: Random data, timing issues, external dependencies

**Solution**:
```python
# Use fixed random seeds
np.random.seed(42)

# Mock external dependencies
from unittest.mock import Mock

# Use pytest-rerunfailures
pip install pytest-rerunfailures
pytest --reruns 3  # Retry failed tests 3 times
```

---

## Best Practices

### 1. Test Independence
- Each test should run independently
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Test Data
- Use small, focused datasets
- Store complex test data in `tests/data/`
- Version control test data

### 3. Assertions
- One logical assertion per test (when possible)
- Clear assertion messages
- Use pytest assertions (not `unittest`)

### 4. Test Organization
- Group related tests in classes
- One test file per module
- Mirror source structure in `tests/`

### 5. Documentation
- Every test needs a docstring
- Explain the "why", not just "what"
- Reference bug IDs for regression tests

---

## Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Hypothesis](https://hypothesis.readthedocs.io/)
- [pre-commit](https://pre-commit.com/)

### Tutorials
- [Real Python: Testing](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)

### Examples
- See `tests/test_rebalancing_execution_order.py`
- See `tests/test_cash_management_integration.py`

---

## Getting Help

### Check test output
```bash
pytest tests/ -vv --tb=long
```

### Run specific test with debugging
```bash
pytest tests/test_file.py::test_name -vv -s --pdb
```

### Ask for help
- Include: test name, error message, full traceback
- Share: minimal reproducible example
- Provide: pytest version, Python version

---

**Last Updated:** 2025-10-23
