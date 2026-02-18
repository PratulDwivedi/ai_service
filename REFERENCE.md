# DuckDB Chat API - Complete Implementation Reference

## Overview

You now have a fully functional chat API that:
1. **Calls Supabase RPC functions** (like `fn_get_tickets`)
2. **Stores responses in DuckDB** for fast querying
3. **Processes natural language** questions about the data
4. **Returns structured results** in JSON

## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# In .env.dev or .env.production
OPENAI_API_KEY=sk-...  # Optional
DUCKDB_PATH=:memory:   # or "/path/to/db.duckdb" for persistence
```

### 3. Start Server
```bash
uvicorn app.main:app --reload
```

### 4. Try It Out
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' | jq -r '.access_token')

# Init chat
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"table_name":"tickets","rpc_name":"fn_get_tickets"}'

# Ask a question
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"table_name":"tickets","message":"Show open tickets"}'
```

## Files Created

### Core Services

#### 1. `app/services/duckdb_service.py`
Manages DuckDB operations:
- `create_table_from_response(table_name, data)` - Store API data
- `query_table(query)` - Execute SQL queries
- `get_table_schema(table_name)` - Get column info
- `get_table_info(table_name)` - Get readable description
- `list_tables()` - List all tables

**Functions:**
- `get_db()` - Get singleton instance
- `close_db()` - Clean shutdown

#### 2. `app/services/chat_service.py`
Handles chat and NL-to-SQL conversion:
- `initialize_from_api(access_token, api_endpoint, table_name, rpc_name)`
  - Calls Supabase RPC
  - Stores in DuckDB
  - Returns table info
- `chat(table_name, user_message)`
  - Converts NL to SQL
  - Executes query
  - Returns results

**Features:**
- OpenAI integration for smart SQL generation
- Fallback pattern matching when OpenAI unavailable
- Full error handling

#### 3. `app/api/routes/chat.py`
Four REST endpoints:

**POST `/api/chat/init`** - Initialize chat
- Request: `{"table_name": "tickets", "rpc_name": "fn_get_tickets"}`
- Response: Table info and schema
- Auth: Bearer token required

**POST `/api/chat/query`** - Ask natural language questions
- Request: `{"table_name": "tickets", "message": "Show open tickets"}`
- Response: SQL query + results
- Auth: Bearer token required

**GET `/api/chat/tables`** - List all tables
- Response: Array of table names
- Auth: Bearer token required

**GET `/api/chat/tables/{table_name}`** - Get table info
- Response: Schema and row count
- Auth: Bearer token required

#### 4. `app/schemas/chat.py`
Pydantic models for validation:
- `ChatInitRequest` - Init request
- `ChatInitResponse` - Init response
- `ChatMessage` - Query request
- `ChatResponse` - Query response
- `TableListResponse` - Tables list
- `TableInfoResponse` - Table info
- `QueryResult` - Query results

### Modified Files

#### `app/core/config.py`
Added settings:
- `openai_api_key: str = ""` - Optional OpenAI key
- `duckdb_path: str = ":memory:"` - Database location

#### `app/main.py`
- Imported chat router
- Registered chat router
- Added shutdown event for DuckDB cleanup

#### `requirements.txt`
Added packages:
- `duckdb>=0.9.0` - Analytics database
- `pandas>=2.0.0` - Data manipulation
- `openai>=1.0.0` - LLM support

### Documentation

1. **QUICKSTART.md** - Get started in 10 minutes
2. **CHAT_API.md** - Complete API reference
3. **IMPLEMENTATION_SUMMARY.md** - Technical overview
4. **REFERENCE.md** - This file

### Examples

**examples/chat_api_example.py** - Full Python client example with:
- Authentication
- Chat initialization
- Multiple query examples
- Pretty-printed results

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    CLIENT (Frontend/Script)                   │
│                                                                │
│  1. GET /api/auth/token                                      │
│     → Returns: access_token                                  │
│                                                                │
│  2. POST /api/chat/init                                      │
│     body: {table_name: "tickets", rpc_name: "fn_get_tickets"}│
│                                                                │
│  3. POST /api/chat/query                                     │
│     body: {table_name: "tickets", message: "Show open items"} │
│                                                                │
│  4. GET /api/chat/tables                                     │
│                                                                │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ Bearer token
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        FastAPI Server                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Authentication Middleware (JWT)                     │   │
│  │  Validates access_token from header                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │
│              ┌───────────────┼───────────────┐               │
│              │               │               │               │
│              ▼               ▼               ▼               │
│  ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │ POST /chat/init │ │POST /query   │ │GET /tables   │     │
│  └────────┬────────┘ └──────┬───────┘ └──────┬───────┘     │
│           │                 │                │              │
└───────────┼─────────────────┼────────────────┼──────────────┘
            │                 │                │
            ▼                 ▼                ▼
     ┌─────────────────────────────────────────────┐
     │         Chat Service                        │
     │  • initialize_from_api()                   │
     │  • chat() / NL→SQL conversion              │
     │  • Error handling                          │
     └────────────────────┬────────────────────────┘
            │                 │
            └────────┬────────┘
                     ▼
     ┌─────────────────────────────────────────────┐
     │         DuckDB Service                      │
     │  • create_table_from_response()             │
     │  • query_table()                           │
     │  • get_table_info()                        │
     │  • list_tables()                           │
     └────────────────────┬────────────────────────┘
            │                 │
            └────────┬────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────────┐      ┌──────────────┐
    │  DuckDB     │      │  Supabase    │
    │ Database    │      │  RPC Server  │
    │ (Tables)    │      │ (fn_get_*) │
    └─────────────┘      └──────────────┘
```

## Usage Examples

### Example 1: Support Tickets
```bash
# Step 1: Get token
TOKEN="eyJ0eXAiOiJ..."

# Step 2: Initialize with tickets data
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "table_name": "support_tickets",
    "rpc_name": "fn_get_tickets"
  }'

# Step 3: Ask questions in natural language
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "table_name": "support_tickets",
    "message": "How many open tickets are assigned to alice?"
  }'

# Response:
{
  "is_success": true,
  "query": "SELECT COUNT(*) as count FROM support_tickets WHERE status='open' AND assigned_to='alice'",
  "result": {
    "columns": ["count"],
    "data": [{"count": 5}]
  },
  "count": 1
}
```

### Example 2: Analytics Data
```bash
# Initialize with analytics
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "table_name": "analytics",
    "rpc_name": "fn_get_analytics"
  }'

# Query: Get daily active users
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "table_name": "analytics",
    "message": "Show me daily active users for the last 7 days"
  }'
```

### Example 3: Multiple Tables
```bash
# Initialize first table
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"table_name": "users", "rpc_name": "fn_get_users"}'

# Initialize second table
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"table_name": "projects", "rpc_name": "fn_get_projects"}'

# List available tables
curl -X GET http://localhost:8000/api/chat/tables \
  -H "Authorization: Bearer $TOKEN"

# Response: {"tables": ["users", "projects"], "count": 2}

# Query first table
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"table_name": "users", "message": "Show active users"}'

# Query second table
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"table_name": "projects", "message": "List all projects"}'
```

## Natural Language Examples

| Question | Generated SQL |
|----------|----------------|
| "Show all tickets" | `SELECT * FROM tickets LIMIT 100` |
| "How many tickets?" | `SELECT COUNT(*) FROM tickets` |
| "Open tickets" | `SELECT * FROM tickets WHERE status='open'` |
| "Latest 5 tickets" | `SELECT * FROM tickets ORDER BY created_at DESC LIMIT 5` |
| "Count by status" | `SELECT status, COUNT(*) FROM tickets GROUP BY status` |
| "Assigned to alice" | `SELECT * FROM tickets WHERE assigned_to='alice'` |

## Configuration

### Environment Variables

```bash
# Required (existing)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
JWT_SECRET=your_secret
APP_NAME=My App

# Optional (new)
OPENAI_API_KEY=sk-...
DUCKDB_PATH=:memory:
```

### Values

- `OPENAI_API_KEY`: For smart NL→SQL. Leave empty to use fallback patterns
- `DUCKDB_PATH`: 
  - `:memory:` = in-memory (fast, data lost on restart)
  - `/path/to/db.duckdb` = persistent file storage

## Architecture Decisions

### Why DuckDB?
- ✅ Zero setup (no separate server)
- ✅ SQL interface (familiar to developers)
- ✅ Fast analytical queries
- ✅ Handles any data type
- ✅ In-memory or file-based

### Why Pandas?
- ✅ Seamless DuckDB integration
- ✅ Flexible data conversion
- ✅ Standard in Python ecosystem

### Why OpenAI?
- ✅ Optional (fallback available)
- ✅ Advanced query understanding
- ✅ Learning capability
- ✅ Handles complex questions

## Error Handling

All responses include `is_success` flag:

```json
{
  "is_success": true,
  "message": "Success message",
  "query": "SQL query executed",
  "result": { "columns": [...], "data": [...] },
  "count": 10
}
```

Or on error:

```json
{
  "is_success": false,
  "message": "Error description"
}
```

## Testing

### Using Python Client
```bash
python examples/chat_api_example.py
```

### Using curl
```bash
# Get token
export TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | jq -r '.access_token')

# Init
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"table_name":"test","rpc_name":"fn_get_tickets"}'

# Query
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"table_name":"test","message":"Show all"}'
```

### Using Python
```python
import httpx

# Get token
response = httpx.post(
    "http://localhost:8000/api/auth/token",
    json={"email": "test@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Init chat
response = httpx.post(
    "http://localhost:8000/api/chat/init",
    headers={"Authorization": f"Bearer {token}"},
    json={"table_name": "tickets", "rpc_name": "fn_get_tickets"}
)
print(response.json())

# Query
response = httpx.post(
    "http://localhost:8000/api/chat/query",
    headers={"Authorization": f"Bearer {token}"},
    json={"table_name": "tickets", "message": "Show open tickets"}
)
print(response.json())
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not authenticated" | Get new token via `/api/auth/token` |
| "Table not found" | Call `/api/chat/init` first |
| "Invalid SQL" | Use more specific language, check column names |
| "OpenAI error" | Leave OPENAI_API_KEY empty to use fallback |
| "DuckDB error" | Check DUCKDB_PATH permissions |
| "Connection refused" | Ensure server is running on port 8000 |

## Performance Tips

1. **Use LIMIT in queries:** "Show first 10" instead of "Show all"
2. **Be specific:** "Open tickets" instead of "Tickets"
3. **Add filters:** "Assigned to alice" instead of "All tickets"
4. **Enable OpenAI:** For better query understanding
5. **Use file storage:** For queries across server restarts

## Security

- ✅ All endpoints require Bearer token
- ✅ Tokens validated using JWT
- ✅ API keys stored in environment
- ✅ No credentials in logs
- ✅ Proper error messages (no data leaks)

## Next Steps

1. ✅ Review [QUICKSTART.md](./QUICKSTART.md)
2. ✅ Try [examples/chat_api_example.py](./examples/chat_api_example.py)
3. ✅ Read full docs: [CHAT_API.md](./CHAT_API.md)
4. ✅ Build your frontend
5. ✅ Customize for your use cases

---

**You're all set! Start using the Chat API. 🚀**
