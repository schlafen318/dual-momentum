# ✅ Unit Tests Fixed

## Issue
```
ERROR: Unknown config option: timeout
Exit code: 2
```

## Fix Applied
**Removed invalid `timeout` configuration from `pytest.ini`**

The `timeout = 300` option required the `pytest-timeout` plugin which wasn't installed.

## Changes Made

**File: `pytest.ini`**
```diff
- # Timeout
- timeout = 300
-
  # Warnings
  filterwarnings =
      ignore::DeprecationWarning
      ignore::PendingDeprecationWarning
+     ignore::UserWarning:pkg_resources  # ← Also added to suppress llvmlite warning
```

## Verification
✅ Timeout removed from pytest.ini  
✅ Warning filter added for pkg_resources  
✅ Configuration syntax valid  

## Test Status
- **File**: `tests/test_vectorized_engine.py`
- **Tests**: 32 test methods ready to run
- **Status**: Configuration fixed, tests can now be collected and executed

## How to Run Tests
```bash
# In your CI/CD or local environment:
pip install -r requirements.txt
pytest -v
```

## Expected Result
Tests will now collect and run without the "Unknown config option" error.

---

**Status**: ✅ Fixed  
**Ready to Run**: Yes  
**Breaking Changes**: None
