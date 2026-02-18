# Chat API - Quick Start Guide

## What's New?

The Chat API allows you to:
- ✅ Call Supabase RPC functions (like `fn_get_tickets`)
- ✅ Automatically store responses in **DuckDB**
- ✅ Query data using **natural language**
- ✅ Get beautiful, structured results

## Installation

1. **Install new dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables** in `.env.dev` or `.env.production`:
```env
# Optional: for natural language to SQL conversion
OPENAI_API_KEY=sk-...

# Optional: for persistent storage (default is :memory:)
DUCKDB_PATH=:memory:
```

3. **Start the server:**
```bash
uvicorn app.main:app --reload
```

## Basic Usage

### 1️⃣ Get Your Access Token

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Response:
```json
{"access_token": "eyJ0eXAiOiJ...", "token_type": "bearer"}
```

### 2️⃣ Initialize Chat (Store API Data)

Replace `ACCESS_TOKEN` with your token from step 1:

```bash
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "rpc_name": "fn_get_tickets"
  }'
```

Response:
```json
{
  "is_success": true,
  "message": "Successfully stored fn_get_tickets data in table 'tickets'",
  "table_name": "tickets",
  "table_info": "Table 'tickets' has 25 rows with columns:\n  - id: INTEGER\n  - title: VARCHAR\n  - status: VARCHAR\n  - created_at: TIMESTAMP"
}
```

### 3️⃣ Chat with the Data

Ask questions in natural language:

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "message": "Show me all open tickets"
  }'
```

Response:
```json
{
  "is_success": true,
  "query": "SELECT * FROM tickets WHERE status = 'open' LIMIT 100",
  "result": {
    "columns": ["id", "title", "status", "created_at"],
    "data": [
      {
        "id": 1,
        "title": "Fix login bug",
        "status": "open",
        "created_at": "2024-01-15T10:30:00"
      },
      {
        "id": 2,
        "title": "Add dark mode",
        "status": "open",
        "created_at": "2024-01-16T14:20:00"
      }
    ]
  },
  "count": 2
}
```

## Natural Language Query Examples

Try these queries:

| Query | Result |
|-------|--------|
| "Show all tickets" | All records (limit 100) |
| "How many tickets?" | COUNT(*) |
| "Show the latest 5" | ORDER BY DESC LIMIT 5 |
| "Count by status" | GROUP BY status query |
| "Open tickets assigned to alice" | Filtered and specific results |

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/chat/init` | Initialize chat with API data |
| POST | `/api/chat/query` | Send natural language query |
| GET | `/api/chat/tables` | List all tables |
| GET | `/api/chat/tables/{table_name}` | Get table info |

## Understanding the Flow

```
┌─────────────────┐
│  User/Frontend  │
└────────┬────────┘
         │
         ├─ GET /api/auth/token (authenticate)
         │
         ├─ POST /api/chat/init (store API data)
         │         │
         │         ├─ Call Supabase RPC (fn_get_tickets)
         │         │
         │         └─ Store in DuckDB table
         │
         └─ POST /api/chat/query (ask questions)
                   │
                   ├─ Convert natural language → SQL
                   │
                   ├─ Execute on DuckDB
                   │
                   └─ Return structured results
```

## Key Components

### 📁 Files Added/Modified

**New Services:**
- `app/services/duckdb_service.py` - DuckDB operations
- `app/services/chat_service.py` - Chat logic & NL-to-SQL

**New Routes:**
- `app/api/routes/chat.py` - Chat endpoints

**New Schemas:**
- `app/schemas/chat.py` - Request/response models

**Updated:**
- `app/core/config.py` - Added OpenAI key & DuckDB path
- `app/main.py` - Registered chat router & shutdown handler
- `requirements.txt` - Added duckdb, pandas, openai

**Documentation:**
- `CHAT_API.md` - Comprehensive API docs
- `examples/chat_api_example.py` - Python client example
- `QUICKSTART.md` - This file

## Database Storage

### Default: In-Memory
- Fastest performance
- Data lost on server restart
- Good for testing

### Optional: File-Based (Persistent)
```env
DUCKDB_PATH=/data/my_database.duckdb
```
- Data persists across restarts
- Slower than in-memory
- Good for production

## Natural Language Processing

### With OpenAI (Recommended)
- More sophisticated queries
- Better understanding of complex questions
- Set `OPENAI_API_KEY` in environment

### Without OpenAI (Fallback)
- Basic patterns work fine
- No external dependencies
- Good for simple queries

## Example Scenarios

### Scenario 1: Support Team Dashboard
```bash
# Initialize
curl -X POST http://localhost:8000/api/chat/init \
  -d '{"table_name": "support_tickets", "rpc_name": "fn_get_tickets"}'

# Query 1: How many high-priority tickets?
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"table_name": "support_tickets", "message": "Show high priority tickets"}'

# Query 2: Tickets waiting response
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"table_name": "support_tickets", "message": "Tickets waiting for response for more than 24 hours"}'
```

### Scenario 2: Analytics
```bash
# Initialize
curl -X POST http://localhost:8000/api/chat/init \
  -d '{"table_name": "analytics", "rpc_name": "fn_get_analytics"}'

# Query 1: Daily active users
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"table_name": "analytics", "message": "Show daily active users"}'

# Query 2: Compare this month vs last month
curl -X POST http://localhost:8000/api/chat/query \
  -d '{"table_name": "analytics", "message": "Monthly comparison"}'
```

## Troubleshooting

### "Not authenticated"
- Get a new access token using `/api/auth/token`
- Ensure token is in the `Authorization: Bearer` header

### "Table not found"
- Call `/api/chat/init` first to create the table
- Check the table name matches

### "Invalid SQL" or slow queries
- Check table schema with `GET /api/chat/tables/{table_name}`
- Verify column names and types
- Add `OPENAI_API_KEY` for better NL→SQL conversion

### DuckDB errors
- Check file permissions (for file-based storage)
- Ensure directory exists
- Restart the server

## Next Steps

1. ✅ Review full docs: [CHAT_API.md](./CHAT_API.md)
2. ✅ Try the Python client: [examples/chat_api_example.py](./examples/chat_api_example.py)
3. ✅ Explore your data with natural language queries
4. ✅ Build a frontend that consumes these APIs

## More Information

- **Full API Documentation:** See [CHAT_API.md](./CHAT_API.md)
- **Python Examples:** See [examples/chat_api_example.py](./examples/chat_api_example.py)
- **DuckDB Docs:** https://duckdb.org/docs/
- **OpenAI Docs:** https://platform.openai.com/docs/

---

**Happy Chatting! 🚀**
