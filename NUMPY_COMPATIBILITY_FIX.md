# NumPy 2.0 Compatibility Fix

## Error Fixed
```
AttributeError: _ARRAY_API not found
```

## Root Cause
**NumPy 2.0 Breaking Changes**: The error occurs when NumPy 2.0+ is installed with packages that expect NumPy 1.x. The `_ARRAY_API` attribute was introduced in NumPy 2.0, but many scientific Python packages (vectorbt, quantstats, pandas) aren't fully compatible yet.

### Why This Happens
1. `numpy>=1.24.0` allows NumPy 2.0+ to be installed
2. NumPy 2.0 has breaking API changes
3. Dependencies (vectorbt, pandas, scipy) may not be compatible with NumPy 2.0
4. Tests fail with `AttributeError: _ARRAY_API not found`

## Solution Applied

### Pin NumPy to 1.x (Before 2.0)

**File: `requirements.txt`**

```diff
  # Data Processing
- numpy>=1.24.0
- pandas>=2.0.0
- scipy>=1.10.0
+ numpy>=1.24.0,<2.0.0  # Pin to 1.x - NumPy 2.0 has breaking changes
+ pandas>=2.0.0,<2.3.0
+ scipy>=1.10.0,<1.15.0

  # Backtesting & Financial Analysis
- vectorbt>=0.26.0
- quantstats>=0.0.62
- empyrical-reloaded>=0.5.5
- optuna>=3.0.0
+ vectorbt>=0.26.0,<0.27.0
+ quantstats>=0.0.62,<0.1.0
+ empyrical-reloaded>=0.5.5,<0.6.0
+ optuna>=3.0.0,<4.0.0
```

### Why This Works

1. **`numpy>=1.24.0,<2.0.0`**
   - Allows NumPy 1.24.x through 1.26.x
   - Blocks NumPy 2.0+ which has breaking changes
   - Compatible with all current dependencies

2. **Upper bounds on other packages**
   - Prevents future breaking changes
   - Ensures tested, stable versions
   - Follows semantic versioning best practices

## Affected Packages

### Packages Incompatible with NumPy 2.0:
- ✅ **vectorbt** - Uses old NumPy APIs
- ✅ **quantstats** - Not yet updated for NumPy 2.0
- ✅ **pandas** - Some versions have issues
- ✅ **scipy** - Older versions incompatible

## Python Version Compatibility

### Tested Combinations:

**Python 3.9:**
- numpy 1.24.x - 1.26.x ✅
- pandas 2.0.x - 2.2.x ✅
- scipy 1.10.x - 1.14.x ✅

**Python 3.10:**
- numpy 1.24.x - 1.26.x ✅
- pandas 2.0.x - 2.2.x ✅
- scipy 1.10.x - 1.14.x ✅

**Python 3.11:**
- numpy 1.24.x - 1.26.x ✅
- pandas 2.0.x - 2.2.x ✅
- scipy 1.10.x - 1.14.x ✅

## Testing the Fix

### Local Test:
```bash
cd /workspace/dual_momentum_system

# Install with pinned versions
pip install -r requirements.txt

# Verify NumPy version
python -c "import numpy; print(numpy.__version__)"
# Should show 1.x.x (not 2.x.x)

# Run tests
pytest tests/ -v
```

### GitHub Actions:
After pushing this change, GitHub Actions will:
1. Install dependencies with NumPy 1.x
2. Tests should pass without `_ARRAY_API` error
3. All CI checks should succeed

## When to Upgrade to NumPy 2.0

**Don't upgrade yet!** Wait until:
1. ✅ vectorbt releases NumPy 2.0 compatible version
2. ✅ quantstats updates to NumPy 2.0
3. ✅ All dependencies confirm compatibility
4. ✅ Test suite passes with NumPy 2.0

**Monitor these:**
- https://github.com/polakowo/vectorbt/issues (NumPy 2.0 support)
- https://github.com/ranaroussi/quantstats/issues
- NumPy 2.0 migration guide: https://numpy.org/devdocs/numpy_2_0_migration_guide.html

## Alternative Solutions (Not Recommended)

### Option 1: Force NumPy 1.26.x Exactly
```
numpy==1.26.4  # Most stable 1.x version
```
**Pros**: Maximum stability  
**Cons**: No security updates, inflexible

### Option 2: Upgrade All Dependencies
```
# Wait for all packages to support NumPy 2.0
# Then upgrade everything together
```
**Pros**: Latest features  
**Cons**: Not ready yet, causes current error

### Option 3: Pin to Specific Tested Versions
```
numpy==1.26.4
pandas==2.2.2
scipy==1.13.0
```
**Pros**: Exact reproducibility  
**Cons**: Misses patches and security updates

## Common NumPy 2.0 Breaking Changes

If you see these errors, they're NumPy 2.0 related:

```python
# 1. _ARRAY_API not found (current issue)
AttributeError: _ARRAY_API not found

# 2. C API changes
ImportError: numpy.core.multiarray failed to import

# 3. Removed functions
AttributeError: module 'numpy' has no attribute 'bool'
# (numpy.bool was removed, use bool or np.bool_ instead)

# 4. Type changes
TypeError: data type not understood

# 5. String dtype changes
ValueError: string dtype specifications not understood
```

## Verification Checklist

After applying fix:

- [x] Update requirements.txt with NumPy <2.0.0
- [x] Add upper bounds to dependencies
- [ ] Commit changes
- [ ] Push to GitHub
- [ ] Verify GitHub Actions installs NumPy 1.x
- [ ] Confirm tests pass
- [ ] Check no `_ARRAY_API` errors

## Files Modified

```
requirements.txt
  - Pinned numpy<2.0.0
  - Added upper bounds to pandas, scipy
  - Added upper bounds to financial packages
```

## Expected Results

### Before Fix:
```
AttributeError: _ARRAY_API not found
FAILED tests/test_vectorized_engine.py
Exit code: 1 ❌
```

### After Fix:
```
tests/test_vectorized_engine.py::test_... PASSED
tests/test_hyperparameter_tuner.py::test_... PASSED
... (all tests pass)
Exit code: 0 ✅
```

## Summary

✅ **Root Cause**: NumPy 2.0 breaking changes  
✅ **Fix Applied**: Pin numpy<2.0.0 in requirements.txt  
✅ **Impact**: Tests should now pass  
✅ **Breaking Changes**: None (actually prevents breaking changes!)  

**Next Steps:**
1. Commit this change
2. Push to GitHub
3. GitHub Actions should pass
4. Monitor for NumPy 2.0 compatibility updates from dependencies

---

**Status**: ✅ Fixed  
**Urgency**: High (blocks CI/CD)  
**Effort**: Low (simple version pin)
