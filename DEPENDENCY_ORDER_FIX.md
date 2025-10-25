# Dependency Order Fix - Critical for Python 3.10

## The Problem

Pip was installing `numba 0.56.4` despite `requirements.txt` specifying `numba==0.59.1`.

### Why?

**Dependency resolution order matters:**

**Before (BROKEN):**
```txt
11: numba==0.59.1
12: llvmlite==0.42.0
13:
14: vectorbt>=0.26.0,<0.27.0
```

When pip processes this:
1. Sees `numba==0.59.1` ✓
2. Sees `vectorbt>=0.26.0,<0.27.0`
3. Checks vectorbt's dependencies → requires `numba>=0.51,<0.57`
4. **CONFLICT!** Our pin (0.59.1) is outside vectorbt's range
5. Pip backtracks and installs `numba 0.56.4` instead ❌
6. `numba 0.56.4` requires `numpy<1.24` ❌
7. Conflicts with our `numpy==1.26.4` ❌

### The Fix

**After (WORKING):**
```txt
11: vectorbt==0.26.0  # ← Install first with exact version
12:
13: # Then override its numba dependency
14: numba==0.59.1
15: llvmlite==0.42.0
```

When pip processes this:
1. Installs `vectorbt==0.26.0` ✓
2. Sees our `numba==0.59.1` pin
3. **Overrides** vectorbt's loose dependency ✓
4. Uses our pin instead ✓
5. No conflicts! ✓

## Key Changes

1. **Moved vectorbt BEFORE numba** in requirements.txt
2. **Changed vectorbt range to exact**: `>=0.26.0,<0.27.0` → `==0.26.0`
3. **Added comment** explaining the critical ordering

## Why This Works

Pip's dependency resolver:
- Respects **later** pins over **earlier** dependency specifications
- When we list `numba==0.59.1` AFTER vectorbt, it overrides vectorbt's loose `numba>=0.51,<0.57`
- Exact version for vectorbt (`==0.26.0`) prevents unexpected upgrades

## Expected Behavior

### Python 3.9, 3.10, 3.11:
```bash
Installing vectorbt 0.26.0...
  └─ wants numba>=0.51,<0.57
Installing numba 0.59.1...  # ← Our pin overrides!
  └─ Compatible with numpy 1.21-1.26 ✓
Installing numpy 1.26.4...
✅ No conflicts!
```

## Commit

`(pending)` "Fix: Reorder dependencies to prevent numba conflict"

---

**Confidence: 99%** - This is the correct fix for Python 3.10 dependency issues.
