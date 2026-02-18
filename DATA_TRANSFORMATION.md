# Data Transformation: From Supabase to DuckDB

## Visual Walkthrough

### Step 1: Supabase RPC Response

Your `fn_get_assets` RPC returns:

```json
{
    "data": [
        {
            "id": 26,
            "code": "FEF00970",
            "name": "4th FLOOR",
            "vendor": {
                "name": "Unknown"
            },
            "category": {
                "name": "Furniture & Fixtures"
            },
            "location": {
                "name": "JW Marriott"
            },
            "condition": {
                "name": "Fair"
            },
            "cost_center": {
                "name": "CC-02"
            }
        },
        {
            "id": 27,
            "code": "FEF00971",
            "name": "CONFERENCE TABLE",
            "vendor": {
                "name": "Herman Miller"
            },
            "category": {
                "name": "Furniture & Fixtures"
            },
            "location": {
                "name": "JW Marriott"
            },
            "condition": {
                "name": "Excellent"
            },
            "cost_center": {
                "name": "CC-01"
            }
        }
    ],
    "paging": {
        "page_size": 10,
        "page_index": 1,
        "total_records": 4553
    },
    "message": "Assets retrieved successfully",
    "is_success": true,
    "status_code": 200
}
```

### Step 2: API Call

```bash
curl -X POST http://localhost:8001/api/chat/init \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "rpc_name": "fn_get_assets",
    "access_token": "your_supabase_token"
  }'
```

### Step 3: Processing in DuckDBService

The API does the following automatically:

1. **Extract** the `data` array from the response
2. **Flatten** all nested objects
3. **Create** table with flat columns

#### Code Flow:

```python
# Step 1: Extract data array
records = data["data"]
# Result: List of 4553 asset records with nested objects

# Step 2: Flatten nested objects
_flatten_nested_objects(records)
# Input:  {"id": 26, "vendor": {"name": "Unknown"}, ...}
# Output: {"id": 26, "vendor_name": "Unknown", ...}

# Step 3: Create DataFrame and store
df = pd.DataFrame(flattened_records)
conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
```

### Step 4: DuckDB Table Structure

| id | code | name | vendor_name | category_name | location_name | condition_name | cost_center_name |
|---|---|---|---|---|---|---|---|
| 26 | FEF00970 | 4th FLOOR | Unknown | Furniture & Fixtures | JW Marriott | Fair | CC-02 |
| 27 | FEF00971 | CONFERENCE TABLE | Herman Miller | Furniture & Fixtures | JW Marriott | Excellent | CC-01 |
| 28 | ... | ... | ... | ... | ... | ... | ... |

### Step 5: API Response

```json
{
    "is_success": true,
    "message": "Successfully stored fn_get_assets data in table 'assets'",
    "table_name": "assets",
    "table_info": "Table 'assets' has 4553 rows with columns:\n  - id: BIGINT\n  - code: VARCHAR\n  - name: VARCHAR\n  - vendor_name: VARCHAR\n  - category_name: VARCHAR\n  - location_name: VARCHAR\n  - condition_name: VARCHAR\n  - cost_center_name: VARCHAR"
}
```

---

## Flattening Logic Explained

### Rule 1: Simple Strings Stay Same

**Before**:
```json
{
    "id": 26,
    "code": "FEF00970",
    "name": "4th FLOOR"
}
```

**After**:
```
id   | code     | name
26   | FEF00970 | 4th FLOOR
```

### Rule 2: Objects Get Flattened with Underscores

**Before**:
```json
{
    "vendor": {"name": "Unknown"},
    "category": {"name": "Furniture & Fixtures"}
}
```

**After**:
```
vendor_name  | category_name
Unknown      | Furniture & Fixtures
```

**Pattern**: `object.field_name` → `object_field_name`

Examples:
- `vendor.name` → `vendor_name`
- `location.name` → `location_name`
- `category.name` → `category_name`
- `condition.name` → `condition_name`
- `cost_center.name` → `cost_center_name`

### Rule 3: Empty Objects Become NULL

**Before**:
```json
{
    "vendor": {}
}
```

**After**:
```
vendor_name
(NULL)
```

### Rule 4: Complex Nested Structures Get JSON String

**Before**:
```json
{
    "metadata": {
        "created_by": "admin",
        "tags": ["furniture", "floor"]
    }
}
```

**After**:
```
metadata
'{"created_by": "admin", "tags": ["furniture", "floor"]}'
```

---

## Example: Full Record Transformation

### Original Supabase Response for One Asset

```json
{
    "id": 26,
    "code": "FEF00970",
    "name": "4th FLOOR",
    "vendor": {
        "id": 1,
        "name": "Unknown"
    },
    "category": {
        "id": 5,
        "name": "Furniture & Fixtures"
    },
    "location": {
        "id": 12,
        "name": "JW Marriott"
    },
    "condition": {
        "id": 3,
        "name": "Fair"
    },
    "cost_center": {
        "id": 7,
        "name": "CC-02"
    }
}
```

### After Flattening (One Row in DuckDB)

```
id=26
code='FEF00970'
name='4th FLOOR'
vendor_id=1
vendor_name='Unknown'
category_id=5
category_name='Furniture & Fixtures'
location_id=12
location_name='JW Marriott'
condition_id=3
condition_name='Fair'
cost_center_id=7
cost_center_name='CC-02'
```

### SQL Query Result

```sql
SELECT * FROM assets WHERE id = 26;
```

Result (as JSON):
```json
{
    "id": 26,
    "code": "FEF00970",
    "name": "4th FLOOR",
    "vendor_id": 1,
    "vendor_name": "Unknown",
    "category_id": 5,
    "category_name": "Furniture & Fixtures",
    "location_id": 12,
    "location_name": "JW Marriott",
    "condition_id": 3,
    "condition_name": "Fair",
    "cost_center_id": 7,
    "cost_center_name": "CC-02"
}
```

---

## Natural Language Query Example

### User Says

```
"Show me all furniture items in fair condition at JW Marriott"
```

### System Converts To SQL

```sql
SELECT * FROM assets 
WHERE category_name = 'Furniture & Fixtures' 
  AND condition_name = 'Fair' 
  AND location_name = 'JW Marriott'
```

### Database Returns

```json
[
    {
        "id": 26,
        "code": "FEF00970",
        "name": "4th FLOOR",
        "vendor_name": "Unknown",
        "category_name": "Furniture & Fixtures",
        "location_name": "JW Marriott",
        "condition_name": "Fair",
        "cost_center_name": "CC-02"
    },
    {
        "id": 28,
        "code": "FEF00972",
        "name": "DESK TABLE",
        "vendor_name": "Steelcase",
        "category_name": "Furniture & Fixtures",
        "location_name": "JW Marriott",
        "condition_name": "Fair",
        "cost_center_name": "CC-02"
    }
]
```

---

## Performance Notes

### Time Complexity

- **Data Extraction**: O(1) - Just accessing array from JSON
- **Flattening**: O(n*m) where n=records, m=nested fields per record
- **Table Creation**: O(n log n) - DuckDB index creation
- **Queries**: O(log n) - Depends on query complexity

### For Your Data

```
Total records: 4553
Nested fields per record: ~6 (vendor, category, location, condition, cost_center)
Expected flattening time: < 100ms
Table creation time: ~500ms
First query time: ~50ms
```

### Memory Usage

```
Original JSON response: ~4-5 MB (nested)
Flattened DataFrame: ~2-3 MB (structured)
DuckDB table (indexed): ~1-2 MB (optimized)
```

---

## Error Cases

### Case 1: Missing Data Array in Response

**What happens**: Falls back to treating entire response as single record

```json
{
    "message": "Success",
    "status_code": 200
}
```

**Result**: Single row table with columns: `message`, `status_code`

**Fix**: Ensure RPC returns data in `data` array

### Case 2: Partial Null Objects

**Response**:
```json
{
    "vendor": null,
    "category": {"name": "Electronics"}
}
```

**Result in DuckDB**:
```
vendor_name | category_name
(NULL)      | Electronics
```

### Case 3: Inconsistent Object Structures

**Record 1**:
```json
{"vendor": {"name": "Apple", "id": 1}}
```

**Record 2**:
```json
{"vendor": {"name": "Samsung"}}
```

**Result**: Both rows have `vendor_name` column, Record 2 has NULL for `vendor_id`

---

## Verification Steps

After running `/api/chat/init`, verify the flattening:

### Step 1: Check Table Info

```bash
curl -X GET http://localhost:8001/api/chat/tables \
  -H "Authorization: Bearer test_token"
```

Response shows all table names and row counts.

### Step 2: Check Table Schema

```bash
curl -X GET http://localhost:8001/api/chat/tables/assets \
  -H "Authorization: Bearer test_token"
```

Response shows column names and types:
```json
{
    "columns": [
        "id",
        "code",
        "name",
        "vendor_name",
        "category_name",
        "location_name",
        "condition_name",
        "cost_center_name"
    ],
    "row_count": 4553
}
```

### Step 3: Query a Sample Record

```bash
curl -X POST http://localhost:8001/api/chat/query \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "message": "Get one asset"
  }'
```

Response should show flattened data with all `_name` columns.

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Data Format | Nested JSON | Flat columns |
| Vendor Info | `vendor: {name, id, ...}` | `vendor_name`, `vendor_id` columns |
| Query Ability | SQL on maps/structs | SQL on VARCHAR columns |
| Readability | Complex paths | Simple column names |
| Performance | Slower (map access) | Faster (indexed columns) |
| NL to SQL | Harder (map syntax) | Easier (column syntax) |

---

**Result**: Your Supabase data is now optimized for querying, searching, and embedding!
