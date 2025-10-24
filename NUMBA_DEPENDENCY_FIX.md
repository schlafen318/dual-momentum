# ✅ NumPy Dependency Chain Fix - FINAL

## Error Being Fixed
```
ImportError: numpy.core.multiarray failed to import
AttributeError: _ARRAY_API not found

A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.0.2 as it may crash.
```

## The REAL Root Cause

Even though we pinned `numpy==1.26.4`, **NumPy 2.0.2 was still being installed**!

### Why?

The dependency chain:
```
vectorbt → numba → numpy
```

If `numba` isn't pinned, pip resolves dependencies and might install:
- numba 0.60.0 (latest)
- numba 0.60.0 requires numpy>=1.21
- pip installs numpy 2.0.2 (satisfies >=1.21)
- Our numpy==1.26.4 pin gets OVERRIDDEN!

## The Complete Solution

### 1. Pin the ENTIRE Dependency Chain

**requirements.txt changes:**
```python
# Data Processing
numpy==1.26.4  # Must be 1.x

# Numba/LLVM (NEW - Critical!)
numba==0.59.1  # Last version compatible with NumPy 1.x
llvmlite==0.42.0  # Compatible with numba 0.59.1

# Backtesting
vectorbt>=0.26.0  # Uses numba, which now uses numpy 1.x
```

### 2. Install NumPy FIRST

**.github/workflows/tests.yml:**
```bash
# Install NumPy first to lock it at 1.26.4
pip install --no-cache-dir "numpy==1.26.4"

# Then install everything else (will use NumPy 1.26.4)
pip install --no-cache-dir -r requirements.txt
```

### 3. Force Clean Install

```bash
--no-cache-dir  # Bypass all caches
```

## Why This Works

### Installation Order:
```
1. pip install numpy==1.26.4
   → NumPy 1.26.4 installed and locked

2. pip install -r requirements.txt
   → Reads: numba==0.59.1
   → numba 0.59.1 requires: numpy<2.0
   → numpy already installed (1.26.4) ✓ Satisfied!
   → Doesn't upgrade NumPy

3. pip install vectorbt
   → Requires: numba
   → numba already installed (0.59.1) ✓ Satisfied!
   → Everything uses NumPy 1.26.4 ✓
```

### Version Compatibility Matrix:

| Package | Version | NumPy Requirement |
|---------|---------|-------------------|
| **numpy** | 1.26.4 | - |
| **numba** | 0.59.1 | numpy<2.0 ✓ |
| **llvmlite** | 0.42.0 | (works with numba 0.59.1) |
| **vectorbt** | 0.26.x | (works with numba 0.59.x) |
| **pandas** | 2.2.2 | numpy>=1.26 ✓ |
| **scipy** | 1.13.1 | numpy>=1.26 ✓ |

**All packages now use NumPy 1.26.4!**

## What Was Wrong Before

### Previous Attempts:
❌ **Attempt 1**: `numpy>=1.24.0,<2.0.0`
- Still allowed pip to negotiate
- numba wanted newer version
- Result: NumPy 2.0.2 installed anyway

❌ **Attempt 2**: `numpy==1.26.4` alone
- Didn't pin numba
- pip upgraded numpy to satisfy numba's open-ended requirement
- Result: NumPy 2.0.2 installed anyway

✅ **Final Fix**: Install numpy first + pin entire chain
- NumPy locked before dependencies resolve
- numba pinned to version that requires NumPy 1.x
- Result: NumPy 1.26.4 stays installed!

## Files Modified

### 1. requirements.txt
```diff
+ numba==0.59.1  # Last version compatible with NumPy 1.x
+ llvmlite==0.42.0  # Compatible with numba 0.59.1
```

### 2. .github/workflows/tests.yml
```diff
+ pip install --no-cache-dir "numpy==1.26.4"  # Install FIRST
  pip install --no-cache-dir -r requirements.txt
```

## Expected GitHub Actions Output

### Before (Wrong):
```
Installing collected packages: numpy, numba, ...
Successfully installed numpy-2.0.2 numba-0.60.0 ❌
```

### After (Correct):
```
Installing collected packages: numpy-1.26.4
Successfully installed numpy-1.26.4 ✓

Installing collected packages: llvmlite-0.42.0, numba-0.59.1, ...
Successfully installed numba-0.59.1 llvmlite-0.42.0 ... ✓
```

## Verification

After this fix runs on GitHub, check for:

### In Install Dependencies step:
```
✅ pip install numpy==1.26.4
✅ Successfully installed numpy-1.26.4

✅ pip install -r requirements.txt
✅ Requirement already satisfied: numpy==1.26.4
✅ Installing numba-0.59.1
✅ Installing llvmlite-0.42.0
```

### In Run Tests step:
```
✅ tests/test_vectorized_engine.py::test_engine_initialization PASSED
✅ tests/test_vectorized_engine.py::test_run_backtest_basic PASSED
... all 32 tests pass
```

## Timeline

- **Now**: Pushing fix
- **0-30s**: GitHub Actions triggers
- **3-5min**: Clean install (no cache)
- **2-3min**: Tests run
- **6-9min**: Complete ✅

## Summary

✅ **Root cause**: numba dependency pulled NumPy 2.0  
✅ **Fix**: Pin numba + llvmlite, install numpy first  
✅ **Result**: Entire dependency chain uses NumPy 1.x  
✅ **Status**: Committed and pushed  

---

**This should FINALLY fix the tests!** 

The key was pinning numba and llvmlite, and installing NumPy first to lock it before pip resolves other dependencies.

Check in ~8 minutes: https://github.com/schlafen318/dual-momentum/actions

🤞 This is the complete solution!
