# Chat API with Nested Data Support

## Overview

The Chat API has been updated to properly handle Supabase RPC responses with nested objects (vendor, category, location, condition, cost_center, etc.).

### What Changed

**Before**: Nested objects stored as maps/structs, making them hard to query
**After**: Automatically flattened into individual columns with underscored names

## How the Data Flattening Works

### Your Supabase Response

```json
{
    "data": [
        {
            "id": 26,
            "code": "FEF00970",
            "name": "4th FLOOR",
            "vendor": {"name": "Unknown"},
            "category": {"name": "Furniture & Fixtures"},
            "location": {"name": "JW Marriott"},
            "condition": {"name": "Fair"},
            "cost_center": {"name": "CC-02"}
        }
    ],
    "paging": {...},
    "message": "...",
    "is_success": true,
    "status_code": 200
}
```

### What Gets Stored in DuckDB

The data is automatically extracted and flattened:

```
id          | code      | name       | vendor_name          | category_name         | location_name | condition_name | cost_center_name
26          | FEF00970  | 4th FLOOR  | Unknown              | Furniture & Fixtures  | JW Marriott   | Fair           | CC-02
```

### Column Naming Convention

Nested objects are flattened using underscore notation:
- `vendor.name` → `vendor_name`
- `category.name` → `category_name`
- `location.name` → `location_name`
- `condition.name` → `condition_name`
- `cost_center.name` → `cost_center_name`

## API Endpoints

### 1. Initialize Chat (Extract and Store Data)

**Endpoint**: `POST /api/chat/init`

**Request**:
```json
{
    "table_name": "assets",
    "rpc_name": "fn_get_assets",
    "access_token": "your_supabase_token"
}
```

**What Happens**:
1. Calls Supabase RPC endpoint `fn_get_assets`
2. Receives response with nested objects
3. **Extracts** the `data` array
4. **Flattens** nested objects (vendor, category, location, etc.)
5. **Stores** flattened data in DuckDB as `assets` table

**Response**:
```json
{
    "is_success": true,
    "message": "Successfully stored fn_get_assets data in table 'assets'",
    "table_name": "assets",
    "table_info": "Table 'assets' has 4553 rows with columns:\n  - id: BIGINT\n  - code: VARCHAR\n  - name: VARCHAR\n  - vendor_name: VARCHAR\n  - category_name: VARCHAR\n  - location_name: VARCHAR\n  - condition_name: VARCHAR\n  - cost_center_name: VARCHAR"
}
```

**Note**: Instead of the old response showing MAP/STRUCT types, you now get clean VARCHAR columns!

### 2. Query Data (Natural Language -> SQL)

**Endpoint**: `POST /api/chat/query`

**Request**:
```json
{
    "table_name": "assets",
    "message": "Show me all furniture in JW Marriott"
}
```

**Response**:
```json
{
    "is_success": true,
    "message": "Query executed successfully",
    "data": [
        {
            "id": 26,
            "code": "FEF00970",
            "name": "4th FLOOR",
            "vendor_name": "Unknown",
            "category_name": "Furniture & Fixtures",
            "location_name": "JW Marriott",
            "condition_name": "Fair",
            "cost_center_name": "CC-02"
        }
    ],
    "row_count": 1
}
```

### 3. List Tables

**Endpoint**: `GET /api/chat/tables`

**Response**:
```json
{
    "is_success": true,
    "tables": ["assets"],
    "count": 1
}
```

## Documentation API Endpoints

### 1. Get Procedure Documentation

**Endpoint**: `GET /api/docs/procedures/fn_get_assets`

**Response**:
```json
{
    "rpc_name": "fn_get_assets",
    "description": "Retrieve a list of assets with pagination and filtering support",
    "parameters": {
        "page_size": "integer - Number of records per page (default 10)",
        "page_index": "integer - Page number (1-based)",
        "search": "string - Search term for asset name or code",
        "status": "string - Filter by asset status"
    },
    "returns": "JSON object containing paginated asset records with associated metadata",
    "use_cases": [
        "Get list of all assets in the system",
        "Search for specific assets by name or code",
        "Filter assets by condition or location",
        "Implement pagination in UI",
        "Build asset inventory reports"
    ],
    "fields_explained": {
        "id": "Unique identifier for the asset",
        "code": "Asset code (e.g., 'FEF00970')",
        "name": "Asset name or description (e.g., '4th FLOOR')",
        "category": "Asset category (object with name, e.g., 'Furniture & Fixtures')",
        "location": "Physical location of asset (object with name, e.g., 'JW Marriott')",
        "condition": "Current condition status (object with name, e.g., 'Fair')",
        ...
    },
    "example_response": {...}
}
```

### 2. Get All Procedures as Markdown

**Endpoint**: `GET /api/docs/all-procedures/markdown`

**Response**:
```json
{
    "markdown": "# RPC Procedures Documentation\n\n## fn_get_assets\n\n...",
    "format": "markdown",
    "note": "Save this markdown content to GitHub as RPC_PROCEDURES.md"
}
```

**Use Case**: Copy the markdown and save to GitHub as `RPC_PROCEDURES.md` for complete documentation.

### 3. Explain SQL Query

**Endpoint**: `POST /api/docs/sql/explain`

**Request**:
```json
{
    "sql_query": "SELECT COUNT(*) FROM assets WHERE category_name = 'Furniture & Fixtures'"
}
```

**Response**:
```json
{
    "sql_query": "SELECT COUNT(*) FROM assets WHERE category_name = 'Furniture & Fixtures'",
    "explanation": "Query: Count the number of records. Filter records where category_name = 'Furniture & Fixtures'."
}
```

### 4. Create Text Embeddings

**Endpoint**: `POST /api/docs/embeddings`

**Request**:
```json
{
    "text": "4th FLOOR furniture fixture at JW Marriott"
}
```

**Response**:
```json
{
    "text": "4th FLOOR furniture fixture at JW Marriott",
    "embedding": [0.001234, -0.005678, ...],
    "model": "text-embedding-3-small"
}
```

**Note**: Requires `OPENAI_API_KEY` environment variable to be set.

### 5. Add Embeddings to Table Column

**Endpoint**: `POST /api/docs/table/assets/embeddings?text_column=name`

**Response**:
```json
{
    "table_name": "assets",
    "text_column": "name",
    "embedding_column": "embedding",
    "message": "Embeddings added successfully",
    "note": "Embeddings stored in embedding column as JSON"
}
```

**Note**: This is expensive (API call per unique text). Best used once for indexing.

## Example Workflow

### Step 1: Initialize Chat with Your Assets Data

```bash
curl -X POST http://localhost:8001/api/chat/init \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "rpc_name": "fn_get_assets",
    "access_token": "your_supabase_token"
  }'
```

Response:
```json
{
    "is_success": true,
    "message": "Successfully stored fn_get_assets data in table 'assets'",
    "table_name": "assets",
    "table_info": "Table 'assets' has 4553 rows with columns:\n  - id: BIGINT\n  - code: VARCHAR\n  - name: VARCHAR\n  - vendor_name: VARCHAR\n  - category_name: VARCHAR\n  - location_name: VARCHAR\n  - condition_name: VARCHAR\n  - cost_center_name: VARCHAR"
}
```

### Step 2: Query Your Data with Natural Language

```bash
curl -X POST http://localhost:8001/api/chat/query \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "message": "How many furniture items are in fair condition?"
  }'
```

Response with actual results!

### Step 3: Get Procedure Documentation

```bash
curl -X GET http://localhost:8001/api/docs/procedures/fn_get_assets \
  -H "Authorization: Bearer your_jwt_token"
```

### Step 4: Export Markdown Documentation to GitHub

```bash
curl -X GET http://localhost:8001/api/docs/all-procedures/markdown \
  -H "Authorization: Bearer your_jwt_token" \
  | jq -r '.markdown' > RPC_PROCEDURES.md

# Commit and push to GitHub
git add RPC_PROCEDURES.md
git commit -m "Add RPC procedures documentation"
git push
```

## Configuration

### Environment Variables

```bash
# Required
JWT_SECRET=your_secret_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Optional
OPENAI_API_KEY=sk-... (for embeddings)
DUCKDB_PATH=:memory: (or /path/to/db)
```

### Dependencies

Make sure these are in `requirements.txt`:
```
duckdb>=0.9.0
pandas>=2.0.0
openai>=1.0.0
fastapi
uvicorn
httpx
```

## Advanced Features

### 1. SQL Procedures → Natural Language

The API converts SQL to English automatically:

```
SELECT COUNT(*) FROM assets WHERE condition_name = 'Fair'
↓
"Count the number of records. Filter records where condition_name = 'Fair'."
```

### 2. Text-to-Embedding

Convert asset names/descriptions to embeddings for semantic search:

```
"4th FLOOR furniture at JW Marriott"
↓
[0.001234, -0.005678, 0.002345, ...] (1536 dimensions)
```

Use this to find similar assets across your inventory!

### 3. Field Explanations

Request explanations for response fields:

```bash
GET /api/docs/field/fn_get_assets/category_name
```

Response:
```json
{
    "rpc_name": "fn_get_assets",
    "field_name": "category_name",
    "explanation": "Asset category (object with name, e.g., 'Furniture & Fixtures')"
}
```

## Performance Notes

- **Data Flattening**: Automatic, happens during table creation
- **Embeddings**: Expensive (OpenAI API calls), cache the results
- **SQL Explanation**: Lightweight, uses pattern matching
- **Documentation**: Pre-generated at startup, instant retrieval

## Troubleshooting

### Data Not Flattening Properly

Check that your response has the expected structure:
```json
{
    "data": [...],
    "paging": {...},
    "message": "...",
    "is_success": true,
    "status_code": 200
}
```

### Missing Columns After Storage

If you don't see `vendor_name`, `category_name`, etc.:
1. Check the original Supabase response has those nested objects
2. Make sure the API endpoint returns the full response format
3. Check DuckDB table schema with `GET /api/chat/tables`

### Embeddings Not Working

1. Set `OPENAI_API_KEY` environment variable
2. Check OpenAI account has API credits
3. Try creating a single embedding first with `/api/docs/embeddings`

## Full Documentation Export Example

```bash
#!/bin/bash
TOKEN="your_jwt_token"

# Get all procedures markdown
curl -X GET http://localhost:8001/api/docs/all-procedures/markdown \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.markdown' > RPC_PROCEDURES.md

# Get assets procedure specifically
curl -X GET http://localhost:8001/api/docs/procedures/fn_get_assets \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.' > fn_get_assets.json

# Create embeddings for asset names
curl -X POST http://localhost:8001/api/docs/table/assets/embeddings \
  -H "Authorization: Bearer $TOKEN" \
  -d 'text_column=name'

echo "✅ Documentation exported and embeddings created!"
```

---

## Next Steps

1. **Test** with your actual Supabase token and RPC functions
2. **Configure** OpenAI API key if using embeddings
3. **Export** documentation to GitHub
4. **Query** your data using natural language
5. **Monitor** API logs for issues

The data flattening happens automatically - no additional configuration needed!
