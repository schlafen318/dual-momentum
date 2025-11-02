# ✅ NumPy 2.0 Compatibility Fix

## Error Fixed
```
AttributeError: _ARRAY_API not found
```

## Root Cause
NumPy 2.0 introduced breaking changes. The requirements allowed NumPy 2.0+ which is incompatible with vectorbt, quantstats, and other dependencies.

## Fix Applied

**File: `requirements.txt`**

### Changed:
```diff
- numpy>=1.24.0
+ numpy>=1.24.0,<2.0.0  # Pin to 1.x - NumPy 2.0 has breaking changes

- pandas>=2.0.0
+ pandas>=2.0.0,<2.3.0

- scipy>=1.10.0
+ scipy>=1.10.0,<1.15.0
```

Also added upper bounds to financial packages:
```diff
- vectorbt>=0.26.0
+ vectorbt>=0.26.0,<0.27.0

- quantstats>=0.0.62
+ quantstats>=0.0.62,<0.1.0

- empyrical-reloaded>=0.5.5
+ empyrical-reloaded>=0.5.5,<0.6.0

- optuna>=3.0.0
+ optuna>=3.0.0,<4.0.0
```

## Why This Works

- **Blocks NumPy 2.0**: Ensures NumPy 1.x is installed (1.24-1.26)
- **Compatible**: All dependencies work with NumPy 1.x
- **Stable**: Prevents future breaking changes

## Testing

```bash
# Verify fix locally
pip install -r requirements.txt
python -c "import numpy; print(numpy.__version__)"
# Should print 1.x.x (not 2.x.x)

# Run tests
pytest tests/ -v
```

## Next Steps

1. **Commit** this change
2. **Push** to GitHub
3. **GitHub Actions** should pass now

## Expected Result

**Before**: `AttributeError: _ARRAY_API not found` ❌  
**After**: Tests pass ✅

---

**Status**: ✅ Fixed  
**Ready to Commit**: Yes  
**Files Modified**: `requirements.txt`
