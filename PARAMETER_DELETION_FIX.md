# Parameter Deletion Fix

## Issue
Parameter deletion was not working in the Hyperparameter Tuning page. When users clicked the 🗑️ button to delete a parameter, Streamlit would get confused and the parameter wouldn't be removed properly.

## Root Cause
The issue was caused by using **index-based widget keys** (`key=f"delete_param_{idx}"`). When a parameter was deleted:
1. The list indices would shift
2. Streamlit would rerun the page
3. The widget keys would change because they were based on indices
4. This caused Streamlit's widget state management to break

### Example of the Problem:
```python
# Before deletion:
params = [
    {name: 'lookback', ...},      # idx=0, key="delete_param_0"
    {name: 'position_count', ...}, # idx=1, key="delete_param_1"
    {name: 'threshold', ...}       # idx=2, key="delete_param_2"
]

# After deleting idx=1, on next render:
params = [
    {name: 'lookback', ...},      # idx=0, key="delete_param_0" ✓
    {name: 'threshold', ...}       # idx=1, key="delete_param_1" ✗ (was 2!)
]
# Streamlit gets confused because the widget keys don't match the content
```

## Solution
Changed from **index-based keys** to **unique ID-based keys**. Each parameter now has a permanent unique ID that doesn't change when other parameters are deleted.

### Changes Made:

#### 1. Added ID Counter to Session State
```python
if 'tune_param_id_counter' not in st.session_state:
    st.session_state.tune_param_id_counter = 0
```

#### 2. Assign Unique ID When Adding Parameters
```python
if st.button("➕ Add Parameter", use_container_width=True):
    st.session_state.tune_param_id_counter += 1
    st.session_state.tune_param_space.append({
        'id': st.session_state.tune_param_id_counter,  # ← Unique ID
        'name': 'lookback_period',
        'type': 'int',
        'values': [126, 189, 252, 315],
    })
    st.rerun()
```

#### 3. Use ID for Widget Keys
```python
for idx, param in enumerate(st.session_state.tune_param_space):
    param_id = param.get('id', idx)  # Use ID instead of index
    
    with st.expander(f"Parameter {idx + 1}: {param.get('name', 'Unnamed')}", expanded=True):
        # All widget keys now use param_id instead of idx
        param_name = st.selectbox(
            "Parameter Name",
            options=[...],
            key=f"param_name_{param_id}",  # ← ID-based key
            ...
        )
```

#### 4. Delete by ID Instead of Index
```python
if st.button("🗑️", key=f"delete_param_{param_id}", help="Delete this parameter"):
    # Remove parameter by ID, not index
    st.session_state.tune_param_space = [
        p for p in st.session_state.tune_param_space if p.get('id') != param_id
    ]
    st.rerun()
```

#### 5. Backward Compatibility
Added code to ensure existing parameters without IDs get assigned one:
```python
# Ensure all parameters have IDs (for backward compatibility)
for idx, param in enumerate(st.session_state.tune_param_space):
    if 'id' not in param:
        st.session_state.tune_param_id_counter += 1
        param['id'] = st.session_state.tune_param_id_counter
```

## How It Works Now

### Example with New System:
```python
# Initial state:
params = [
    {id: 1, name: 'lookback', ...},      # key="delete_param_1"
    {id: 2, name: 'position_count', ...}, # key="delete_param_2"
    {id: 3, name: 'threshold', ...}       # key="delete_param_3"
]

# After deleting ID=2, on next render:
params = [
    {id: 1, name: 'lookback', ...},      # key="delete_param_1" ✓
    {id: 3, name: 'threshold', ...}       # key="delete_param_3" ✓
]
# Keys remain consistent! Deletion works perfectly.
```

## Files Modified

1. **`frontend/pages/hyperparameter_tuning.py`**
   - Added `tune_param_id_counter` to session state
   - Changed widget keys from index-based to ID-based
   - Updated deletion logic to use IDs
   - Added backward compatibility for existing parameters

2. **`frontend/pages/backtest_results.py`**
   - Updated `_prepare_tuning_from_backtest()` to assign IDs when creating parameters
   - Ensures pre-populated parameters have IDs

## Testing

✅ **Syntax Check**: All files compile successfully  
✅ **Linting**: No linting errors  
✅ **Backward Compatibility**: Old parameters without IDs automatically get assigned one  
✅ **Add Parameter**: Works correctly, assigns unique IDs  
✅ **Delete Parameter**: Now works correctly with ID-based lookup  
✅ **Clear All**: Works correctly  
✅ **Reset to Defaults**: Works correctly with pre-assigned IDs  

## User Impact

### Before Fix:
- ❌ Clicking delete button would fail
- ❌ Parameters would remain in the list
- ❌ UI would show confusing behavior
- ❌ Users had to use "Clear All" and start over

### After Fix:
- ✅ Delete button works instantly
- ✅ Parameters are removed immediately
- ✅ UI behaves as expected
- ✅ Smooth user experience

## Additional Benefits

1. **More Robust**: IDs are permanent and don't change
2. **Better State Management**: Streamlit handles widgets correctly
3. **Scalable**: Works with any number of parameters
4. **Maintainable**: Clear separation between display index and unique ID

## Migration

No migration needed! The fix is backward compatible:
- Existing parameters without IDs will automatically get one
- No user action required
- No data loss

## Related Buttons

All parameter management buttons now work correctly:

| Button | Functionality | Status |
|--------|---------------|--------|
| ➕ Add Parameter | Adds new parameter with unique ID | ✅ Working |
| 🗑️ Delete (individual) | Deletes specific parameter by ID | ✅ **FIXED** |
| 🔄 Reset to Defaults | Resets to 3 default parameters with IDs | ✅ Working |
| 🗑️ Clear All | Removes all parameters | ✅ Working |

## Technical Notes

### Why ID-based Instead of Index-based?

| Approach | Pros | Cons |
|----------|------|------|
| **Index-based** (old) | Simple to implement | Breaks when list changes |
| **ID-based** (new) | Stable across changes | Requires counter management |

The ID-based approach is the standard solution for dynamic lists in Streamlit and React-style frameworks.

### ID Counter Management

The counter always increments, never resets (except on "Reset to Defaults"):
- Ensures IDs are always unique
- No conflicts even with add/delete cycles
- Simple and reliable

## Future Enhancements

Potential improvements:
- [ ] Add undo/redo for parameter changes
- [ ] Add parameter reordering (drag & drop)
- [ ] Add parameter duplication
- [ ] Add parameter templates/presets

---

**Status**: ✅ **FIXED and TESTED**  
**Date**: 2025-10-23  
**Impact**: Critical UX improvement
