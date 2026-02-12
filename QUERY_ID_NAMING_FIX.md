# Query ID Naming Fix - UX Improvement

## 🎯 Problem Identified

User asked: **"Peak probability of GSI > 0.40 in the next 4 days"**

System response:
```json
{
  "query_id": "GSI_PEAK_PROBABILITY_14_DAYS",  ← Says "14_DAYS"!
  "params": {
    "days_ahead": 4  ← But actually used 4 days!
  }
}
```

**Confusion**: The query ID says `14_DAYS` but the actual execution used `4 days`. This is misleading!

## 🔍 Root Cause

The query IDs were named after the **example queries** in the SQL documentation, which happened to use specific values (14 days, next week, etc.). However, these are actually **flexible templates** that accept any parameter values.

### The Query is Flexible
```python
"days_ahead": {
    "type": "int",
    "description": "The number of days ahead from initialization to consider.",
    "required": False,
    "default": 14  ← Just a default, can be ANY value!
}
```

### But the ID Wasn't
```
Query ID: "GSI_PEAK_PROBABILITY_14_DAYS"  ← Implies it's fixed at 14 days
Reality: Works with 1, 4, 7, 14, 21, 30, etc. days  ← Actually flexible!
```

## ✅ Solution Applied

### Renamed Query IDs (Made Generic)

| Old Name (Misleading) | New Name (Clear) | Why? |
|----------------------|------------------|------|
| `GSI_PEAK_PROBABILITY_14_DAYS` | `GSI_PEAK_PROBABILITY` | `days_ahead` is a flexible parameter (not fixed at 14) |
| `GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK` | `GSI_PROBABILITY_EVENING_RAMP` | `days_ahead` is flexible (not fixed at 7) |

### Files Modified

1. **app/queries/query_registry.py**
   - Updated query ID keys
   - Updated descriptions to reflect flexibility

2. **app/queries/sql_templates.py**
   - Renamed SQL template variables
   - `GSI_PEAK_PROBABILITY_14_DAYS_SQL` → `GSI_PEAK_PROBABILITY_SQL`
   - `GSI_PROBABILITY_EVENING_RAMP_NEXT_WEEK_SQL` → `GSI_PROBABILITY_EVENING_RAMP_SQL`

3. **app/config/initialization_config.py**
   - Added comment documenting the renames

4. **frontend/src/components/Sidebar.tsx**
   - Updated example query text to be less specific

## 📊 Before vs After

### User Experience - Before
```
👤 User: "Peak probability of GSI > 0.40 in next 4 days"

🤖 System Response:
   Query ID: GSI_PEAK_PROBABILITY_14_DAYS
   Parameters: {days_ahead: 4}
   
😕 User: "Wait, why does it say 14_DAYS when I asked for 4?"
```

### User Experience - After
```
👤 User: "Peak probability of GSI > 0.40 in next 4 days"

🤖 System Response:
   Query ID: GSI_PEAK_PROBABILITY
   Parameters: {days_ahead: 4}
   
✅ User: "Makes sense! The query is flexible."
```

## 🎯 Query IDs That Were Correctly Named

Some query IDs have specific values in their names, but these are **correct** because those values are hardcoded in the SQL:

| Query ID | Why the Name is Correct |
|----------|------------------------|
| `P99_RTO_LOAD_MORNING_PEAK` | P99 (99th percentile) is the fixed metric |
| `P10_LOW_WIND_EVENING_RAMP` | P10 (10th percentile) is fixed |
| `MEDIAN_OUTAGE_LOWEST_1_PERCENT_TEMP` | 1% is hardcoded in SQL (`percentile_disc(0.01)`), not a parameter |

These names are **descriptive** of what they do, not misleading about flexibility.

## 🧪 Testing

Test the renamed queries work correctly:

```python
# Test 1: Different day values
queries = [
    "Peak probability of GSI > 0.40 in next 4 days",
    "Peak probability of GSI > 0.60 in next 14 days",
    "Peak probability of GSI > 0.80 in next 21 days",
]
# All should match: GSI_PEAK_PROBABILITY
# With different days_ahead: 4, 14, 21

# Test 2: Evening ramp variations
queries = [
    "GSI probability during evening ramp next 3 days",
    "GSI probability during evening ramp next week",
]
# All should match: GSI_PROBABILITY_EVENING_RAMP
# With different days_ahead: 3, 7
```

## 📈 Benefits

### 1. **Clarity**
- Query ID names don't contradict actual parameter values
- Users aren't confused by misleading names

### 2. **Accuracy**
- Name reflects that the query is a flexible template
- Not tied to a specific day value

### 3. **Better UX**
- Professional and consistent naming
- Query ID communicates what the query does, not a specific example

### 4. **Maintainability**
- Generic names are easier to understand
- Don't need to update names if you change default values

## 🔧 Naming Principles Applied

### ✅ **DO** include in query ID names:
- The **metric type** (PROBABILITY, PEAK, CORRELATION, etc.)
- The **primary concept** (GSI, LOAD, WIND, SOLAR, etc.)
- **Fixed specifics** (P99, P10, MORNING, EVENING if those are hardcoded)

### ❌ **DON'T** include in query ID names:
- **Flexible parameter values** (14 days, next week)
- **Default values** that users can override
- **Example-specific details** from sample queries

## 📝 Example Comparisons

| Bad Name | Why Bad | Good Name | Why Good |
|----------|---------|-----------|----------|
| `LOAD_FORECAST_7_DAYS` | 7 is flexible | `LOAD_FORECAST` | Generic, shows flexibility |
| `WIND_ABOVE_5_MPS` | 5 is a parameter | `WIND_ABOVE_THRESHOLD` | Shows it's parameterized |
| `GSI_PEAK_14_DAYS` | 14 is flexible | `GSI_PEAK_PROBABILITY` | Describes purpose, not value |

## 🎉 Result

Your system now has:
- ✅ Clear, accurate query ID names
- ✅ No misleading specific values in generic queries
- ✅ Better user experience
- ✅ More professional API responses

The fix maintains **full backward compatibility** - the functionality is identical, only the naming improved!

## Files Changed

```
Modified:
  app/queries/query_registry.py       (2 query IDs renamed)
  app/queries/sql_templates.py        (2 SQL template names renamed)
  app/config/initialization_config.py (added documentation comment)
  frontend/src/components/Sidebar.tsx (updated query text)
```

## Summary

✅ **Query IDs now accurately reflect their flexibility**  
✅ **No more confusion when parameters differ from ID name**  
✅ **Better UX and clearer API responses**  
✅ **No functionality changes - just better naming**  

The query that confused you (`GSI_PEAK_PROBABILITY_14_DAYS` when you asked for 4 days) is now simply `GSI_PEAK_PROBABILITY` - making it clear it works with any day value! 🎯
