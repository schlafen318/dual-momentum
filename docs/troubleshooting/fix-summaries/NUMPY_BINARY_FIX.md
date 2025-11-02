# NumPy Binary Incompatibility Fix

## New Error
```
ImportError: numpy.core.multiarray failed to import
```

## Root Cause
This error occurs when packages compiled against NumPy 2.0 are cached, but NumPy 1.x is now installed. The binary extensions are incompatible between versions.

### Why This Happens:
1. GitHub Actions cached packages compiled with NumPy 2.0
2. We pinned NumPy <2.0 in requirements.txt
3. NumPy 1.x was installed
4. Cached packages (scipy, pandas, vectorbt) still have NumPy 2.0 binaries
5. Binary mismatch causes import failure

## Solution Applied

### 1. Update Cache Key (in .github/workflows/tests.yml)
```yaml
# Before
key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# After - Forces new cache when NumPy version changes
key: ${{ runner.os }}-pip-numpy1-${{ hashFiles('**/requirements.txt') }}
```

### 2. Force Reinstall Without Cache
```yaml
# Before
pip install -r requirements.txt

# After - Bypasses cache to rebuild all packages
pip install --no-cache-dir -r requirements.txt
pip install --no-cache-dir pytest pytest-cov pytest-benchmark hypothesis pytest-mock
```

### 3. Pin to Exact Stable Versions
```diff
  # Data Processing
- numpy>=1.24.0,<2.0.0  # Pin to 1.x
- pandas>=2.0.0,<2.3.0
- scipy>=1.10.0,<1.15.0
+ numpy==1.26.4  # Latest stable 1.x, tested combination
+ pandas==2.2.2  # Compatible with NumPy 1.26
+ scipy==1.13.1  # Compatible with NumPy 1.26
```

## Why This Works

### Exact Versions:
- **numpy==1.26.4**: Latest stable NumPy 1.x release
- **pandas==2.2.2**: Confirmed compatible with NumPy 1.26.4
- **scipy==1.13.1**: Built for NumPy 1.26.x

### No Cache:
- `--no-cache-dir`: Forces fresh install
- Rebuilds all binary extensions against NumPy 1.26.4
- Ensures compatibility across all packages

### New Cache Key:
- Old cache with NumPy 2.0 binaries won't be used
- New cache key `numpy1` indicates NumPy 1.x
- Future runs use compatible cached packages

## Files Modified

1. **requirements.txt**: Exact version pins
2. **.github/workflows/tests.yml**: Cache key and --no-cache-dir

## Testing Locally

```bash
cd /workspace/dual_momentum_system

# Clear pip cache
pip cache purge

# Force clean install
pip install --no-cache-dir -r requirements.txt

# Verify versions
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "import pandas; print(f'Pandas: {pandas.__version__}')"
python -c "import scipy; print(f'SciPy: {scipy.__version__}')"

# Test imports
python -c "from numpy.core import multiarray; print('✅ multiarray imports OK')"

# Run tests
pytest tests/ -v
```

## Expected Results

### Before Fix:
```
ImportError: numpy.core.multiarray failed to import
DLL load failed while importing _multiarray_umath
Exit code: 1 ❌
```

### After Fix:
```
✅ Installing numpy==1.26.4
✅ Building scipy 1.13.1 against NumPy 1.26.4
✅ Building pandas 2.2.2 against NumPy 1.26.4
✅ numpy.core.multiarray imports successfully
✅ All tests pass
Exit code: 0 ✅
```

## Alternative Solutions (Not Used)

### Option 1: Only clear cache manually
```yaml
- name: Clear pip cache
  run: pip cache purge
```
**Issue**: Doesn't prevent future cache issues

### Option 2: Disable caching entirely
```yaml
# Remove cache step completely
```
**Issue**: Slower CI/CD runs (no benefit of caching)

### Option 3: Use conda instead of pip
```yaml
- uses: conda-incubator/setup-miniconda@v2
  with:
    python-version: 3.9
```
**Issue**: More complex, harder to maintain

## Why Exact Versions Are Better

### Ranges (>=X.X,<Y.Y):
- ✓ Gets security updates
- ✗ Can break unexpectedly
- ✗ Binary incompatibility possible

### Exact (==X.X.X):
- ✓ Guaranteed compatibility
- ✓ Reproducible builds
- ✓ No surprise breakages
- ✗ Need manual updates for security patches

**For CI/CD stability: Exact versions are preferred**

## Maintenance

### Update quarterly or when needed:
```bash
# Test new versions locally first
pip install numpy==1.27.0 pandas==2.3.0 scipy==1.14.0
pytest tests/ -v

# If tests pass, update requirements.txt
```

### Monitor for:
- NumPy 2.0 compatibility in dependencies
- Security advisories
- Critical bug fixes

## Summary

✅ **Fixed**: Binary incompatibility by forcing clean install  
✅ **Pinned**: Exact compatible versions  
✅ **Updated**: Cache key to prevent old binaries  
✅ **Result**: Tests should pass now  

---

**Next Steps:**
1. Commit these changes
2. Push to GitHub
3. GitHub Actions will force reinstall everything
4. Tests should pass with compatible binaries
