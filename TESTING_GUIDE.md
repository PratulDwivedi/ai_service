# Testing the Chat API with Nested Data

## Server Status

✅ **Running on `http://localhost:8001`**

### Available Endpoints

**Chat Endpoints**:
- `POST /api/chat/init` - Initialize from Supabase RPC
- `POST /api/chat/query` - Query data with natural language
- `GET /api/chat/tables` - List tables
- `GET /api/chat/tables/{table_name}` - Get table info

**Documentation Endpoints**:
- `GET /api/docs/procedures` - List all procedures
- `GET /api/docs/procedures/{rpc_name}` - Get procedure documentation
- `GET /api/docs/procedures/{rpc_name}/markdown` - Get as Markdown
- `GET /api/docs/all-procedures/markdown` - Export all as Markdown
- `POST /api/docs/sql/explain` - Explain SQL queries
- `POST /api/docs/embeddings` - Create text embeddings
- `POST /api/docs/table/{table_name}/embeddings` - Add embeddings to table
- `GET /api/docs/field/{rpc_name}/{field_name}` - Explain a field

---

## Test 1: View API Documentation

Open in browser or run:

```bash
curl http://localhost:8001/docs
```

This opens the interactive Swagger UI with all endpoints and request/response examples.

---

## Test 2: Get Asset Procedure Documentation

**Request**:
```bash
curl -X GET http://localhost:8001/api/docs/procedures/fn_get_assets \
  -H "Authorization: Bearer test_token"
```

**Expected Response**:
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
    ...
  ],
  "fields_explained": {
    "id": "Unique identifier for the asset",
    "code": "Asset code (e.g., 'FEF00970')",
    "name": "Asset name or description (e.g., '4th FLOOR')",
    "vendor_name": "Vendor/manufacturer information",
    "category_name": "Asset category (e.g., 'Furniture & Fixtures')",
    "location_name": "Physical location (e.g., 'JW Marriott')",
    "condition_name": "Current condition (e.g., 'Fair')",
    "cost_center_name": "Cost center (e.g., 'CC-02')"
  }
}
```

---

## Test 3: Export Procedure Docs as Markdown

**Request**:
```bash
curl -X GET http://localhost:8001/api/docs/all-procedures/markdown \
  -H "Authorization: Bearer test_token"
```

**Save to File**:
```bash
curl -X GET http://localhost:8001/api/docs/all-procedures/markdown \
  -H "Authorization: Bearer test_token" \
  | jq -r '.markdown' > RPC_PROCEDURES.md

# View the generated file
cat RPC_PROCEDURES.md
```

This creates a GitHub-ready Markdown documentation file!

---

## Test 4: Explain a SQL Query

**Request**:
```bash
curl -X POST http://localhost:8001/api/docs/sql/explain \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT COUNT(*) FROM assets WHERE category_name = \"Furniture & Fixtures\""
  }'
```

**Expected Response**:
```json
{
  "sql_query": "SELECT COUNT(*) FROM assets WHERE category_name = 'Furniture & Fixtures'",
  "explanation": "Query: Count the number of records. Filter records where category_name = 'Furniture & Fixtures'."
}
```

---

## Test 5: Initialize Chat with Your Asset Data

This is the **key test** - it shows the nested data flattening in action.

**Request**:
```bash
curl -X POST http://localhost:8001/api/chat/init \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "rpc_name": "fn_get_assets",
    "access_token": "your_supabase_key"
  }'
```

**What Happens**:
1. Calls Supabase RPC: `fn_get_assets`
2. Gets your response with nested objects
3. **Extracts** the `data` array
4. **Flattens** nested objects (vendor → vendor_name, category → category_name, etc.)
5. **Stores** as DuckDB table with 4553 rows and flat columns

**Expected Response**:
```json
{
  "is_success": true,
  "message": "Successfully stored fn_get_assets data in table 'assets'",
  "table_name": "assets",
  "table_info": "Table 'assets' has 4553 rows with columns:\n  - id: BIGINT\n  - code: VARCHAR\n  - name: VARCHAR\n  - vendor_name: VARCHAR\n  - category_name: VARCHAR\n  - location_name: VARCHAR\n  - condition_name: VARCHAR\n  - cost_center_name: VARCHAR"
}
```

**Verify the Columns** - Notice:
- ✅ `vendor_name` instead of `vendor` (object)
- ✅ `category_name` instead of `category` (object)  
- ✅ `location_name` instead of `location` (object)
- ✅ `condition_name` instead of `condition` (object)
- ✅ `cost_center_name` instead of `cost_center` (object)

---

## Test 6: Query Your Data (Natural Language)

**Request**:
```bash
curl -X POST http://localhost:8001/api/chat/query \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "message": "Show me all furniture items in fair condition"
  }'
```

**Expected Response** (actual data!):
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
    },
    ...more results...
  ],
  "row_count": 247
}
```

---

## Test 7: Get Specific Field Explanation

**Request**:
```bash
curl -X GET http://localhost:8001/api/docs/field/fn_get_assets/category_name \
  -H "Authorization: Bearer test_token"
```

**Response**:
```json
{
  "rpc_name": "fn_get_assets",
  "field_name": "category_name",
  "explanation": "Asset category (object with name, e.g., 'Furniture & Fixtures')"
}
```

---

## Test 8: Create Text Embeddings

**Request** (requires OPENAI_API_KEY):
```bash
curl -X POST http://localhost:8001/api/docs/embeddings \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "4th FLOOR furniture fixture at JW Marriott location fair condition"
  }'
```

**Expected Response**:
```json
{
  "text": "4th FLOOR furniture fixture at JW Marriott location fair condition",
  "embedding": [
    0.00123456,
    -0.00567890,
    0.00234567,
    ...1536 total dimensions...
  ],
  "model": "text-embedding-3-small"
}
```

**Use Case**: These embeddings enable semantic search - find similar assets by meaning, not just keywords!

---

## Test 9: Add Embeddings to Table

**Request** (expensive operation - OpenAI API calls per unique text):
```bash
curl -X POST http://localhost:8001/api/docs/table/assets/embeddings \
  -H "Authorization: Bearer test_token"
```

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

Now you can do semantic search on asset names!

---

## Full Workflow Example

Complete script to test everything:

```bash
#!/bin/bash

TOKEN="test_token"
BASE_URL="http://localhost:8001"

echo "1️⃣ Get procedure documentation..."
curl -s -X GET "$BASE_URL/api/docs/procedures/fn_get_assets" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo ""
echo "2️⃣ Export procedure docs as Markdown..."
curl -s -X GET "$BASE_URL/api/docs/all-procedures/markdown" \
  -H "Authorization: Bearer $TOKEN" | jq '.markdown' > RPC_PROCEDURES.md
echo "✅ Saved to RPC_PROCEDURES.md"

echo ""
echo "3️⃣ Initialize chat with assets..."
curl -s -X POST "$BASE_URL/api/chat/init" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "rpc_name": "fn_get_assets",
    "access_token": "your_supabase_key"
  }' | jq '.'

echo ""
echo "4️⃣ Query assets with natural language..."
curl -s -X POST "$BASE_URL/api/chat/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "assets",
    "message": "How many furniture items are in fair condition?"
  }' | jq '.'

echo ""
echo "✅ All tests complete!"
```

Save as `test_chat_api.sh` and run:
```bash
chmod +x test_chat_api.sh
./test_chat_api.sh
```

---

## Key Features Summary

✅ **Nested Data Flattening**
- Automatically extracts `data` array from Supabase response
- Flattens nested objects (vendor.name → vendor_name)
- Creates clean, queryable columns

✅ **Natural Language Querying**
- Ask questions in English
- Converted to SQL automatically
- Results returned immediately

✅ **Procedure Documentation**
- Get full explanation of RPC functions
- Field-by-field descriptions
- Export as Markdown for GitHub
- Parameter and return type documentation

✅ **SQL Explanations**
- Convert SQL queries to English
- Understand complex queries easily

✅ **Text Embeddings**
- Convert text to semantic vectors
- Enable similarity search
- Find related assets by meaning

---

## Troubleshooting

### Issue: "Table not found" error

**Solution**: Make sure you ran `/api/chat/init` first to create the table

### Issue: Nested objects showing as objects, not flattened

**Solution**: Ensure the Supabase response includes the nested objects in the responses, e.g.:
```json
{
  "category": {"name": "Furniture & Fixtures"}
}
```

Not:
```json
{
  "category_name": "Furniture & Fixtures"
}
```

### Issue: OpenAI embeddings failing

**Solution**: Set environment variable before starting server:
```bash
export OPENAI_API_KEY=sk-...
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Issue: Authorization failing

**Solution**: For testing, the token just needs to be valid JWT format. It can be a test token like:
```
Bearer test_token
```

In production, it should be a real JWT with `sub` claim for user ID.

---

## Next Steps

1. ✅ Test all endpoints above with your Supabase data
2. ✅ Verify nested objects are flattened correctly
3. ✅ Export procedure documentation to GitHub
4. ✅ Add embeddings for semantic search
5. ✅ Integrate into your application
6. ✅ Monitor logs for any issues

**Documentation**: All Markdown files are ready to commit to GitHub!
