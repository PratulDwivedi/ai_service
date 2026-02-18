# Chat API with DuckDB Integration

This document describes how to use the Chat API to store API responses in DuckDB and query them using natural language.

## Overview

The Chat API allows you to:
1. Call Supabase RPC functions (like `fn_get_tickets`)
2. Automatically store the response in DuckDB
3. Query the stored data using natural language
4. Get structured results back

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

In your `.env.dev` or `.env.production` file, add:

```env
OPENAI_API_KEY=your_openai_api_key_here  # Optional (for natural language to SQL conversion)
DUCKDB_PATH=:memory:  # Or a file path for persistent storage
```

Or keep `DUCKDB_PATH=:memory:` for in-memory database.

## API Endpoints

### 1. Initialize Chat (Store API Data)

**Endpoint:** `POST /api/chat/init`

Initialize the chat by calling an RPC function and storing the response in DuckDB.

**Request:**
```json
{
  "table_name": "tickets",
  "rpc_name": "fn_get_tickets"
}
```

**Headers:**
```
Authorization: Bearer <your_access_token>
```

**Response:**
```json
{
  "is_success": true,
  "message": "Successfully stored fn_get_tickets data in table 'tickets'",
  "table_name": "tickets",
  "table_info": "Table 'tickets' has 25 rows with columns:\n  - id: INTEGER\n  - title: VARCHAR\n  - status: VARCHAR\n  - created_at: TIMESTAMP"
}
```

### 2. Chat Query (Natural Language)

**Endpoint:** `POST /api/chat/query`

Query the stored data using natural language.

**Request:**
```json
{
  "table_name": "tickets",
  "message": "Show me all open tickets"
}
```

**Headers:**
```
Authorization: Bearer <your_access_token>
```

**Response:**
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

### 3. List Tables

**Endpoint:** `GET /api/chat/tables`

List all available tables in the database.

**Headers:**
```
Authorization: Bearer <your_access_token>
```

**Response:**
```json
{
  "tables": ["tickets", "users", "projects"],
  "count": 3
}
```

### 4. Get Table Info

**Endpoint:** `GET /api/chat/tables/{table_name}`

Get detailed information about a specific table.

**Headers:**
```
Authorization: Bearer <your_access_token>
```

**Response:**
```json
{
  "table_name": "tickets",
  "info": "Table 'tickets' has 25 rows with columns:\n  - id: INTEGER\n  - title: VARCHAR\n  - status: VARCHAR\n  - created_at: TIMESTAMP\n  - assigned_to: VARCHAR"
}
```

## Usage Examples

### Example 1: Basic Setup and Query

```bash
# 1. Authenticate and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.access_token')

# 2. Initialize chat with tickets data
curl -X POST http://localhost:8000/api/chat/init \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "rpc_name": "fn_get_tickets"
  }'

# 3. Query the data
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "message": "How many open tickets are there?"
  }'
```

### Example 2: Advanced Queries

```bash
# Query: Get all tickets assigned to a specific user
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "message": "Show me all tickets assigned to alice@example.com"
  }'

# Query: Get latest tickets
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "message": "Show the 5 most recent tickets"
  }'

# Query: Get ticket count by status
curl -X POST http://localhost:8000/api/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "tickets",
    "message": "How many tickets are in each status?"
  }'
```

## Supported Natural Language Queries

The chat service supports various natural language query patterns:

- **Basic retrieval:** "Show all tickets", "List users", "Get projects"
- **Counting:** "How many tickets are there?", "Count of closed items"
- **Filtering:** "Show open tickets", "Get tickets for user X"
- **Sorting:** "Show the latest tickets", "Get top 5 issues", "Most recent items"
- **Grouping:** "Group by status", "Count by priority"
- **Aggregation:** "Average, sum, maximum, minimum" operations

## Architecture

### DuckDB Service (`app/services/duckdb_service.py`)

Manages:
- Table creation from API responses
- SQL query execution
- Schema information retrieval
- Database connection lifecycle

**Key Methods:**
- `create_table_from_response()` - Store API data
- `query_table()` - Execute SQL queries
- `get_table_schema()` - Get column information
- `get_table_info()` - Get readable table description
- `list_tables()` - List all tables

### Chat Service (`app/services/chat_service.py`)

Handles:
- API calls to Supabase RPC functions
- Natural language to SQL conversion (via OpenAI or fallback)
- Query execution and result formatting

**Key Methods:**
- `initialize_from_api()` - Set up chat with API data
- `chat()` - Process natural language queries

### Chat Routes (`app/api/routes/chat.py`)

Exposes:
- `/api/chat/init` - Initialize chat
- `/api/chat/query` - Send queries
- `/api/chat/tables` - List tables
- `/api/chat/tables/{table_name}` - Get table info

## Database Storage Options

### In-Memory (Default)
```python
DUCKDB_PATH=:memory:
```
Data is lost when the server restarts.

### File-Based (Persistent)
```python
DUCKDB_PATH=/path/to/database.duckdb
```
Data is persisted to disk.

## Natural Language to SQL Conversion

### With OpenAI (Recommended)
If `OPENAI_API_KEY` is set, the service uses GPT-3.5-turbo to convert natural language to SQL.

**Benefits:**
- More sophisticated query understanding
- Better handling of complex questions
- Learning capability

### Fallback (No OpenAI Required)
If OpenAI is not available, uses simple pattern matching:
- "all/show/list" → `SELECT * LIMIT 100`
- "count/how many" → `SELECT COUNT(*)`
- "top/latest/recent" → Order by first column DESC
- Default → `SELECT * LIMIT 50`

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid table, failed query)
- `401` - Unauthorized (invalid or missing token)
- `404` - Not found (table doesn't exist)
- `500` - Server error

Example error response:
```json
{
  "is_success": false,
  "message": "Table 'invalid_table' not found"
}
```

## Performance Considerations

### DuckDB Features
- Fast analytical queries
- Efficient storage
- Good for JSON/complex data
- Supports SQL window functions

### Optimization Tips
1. Use specific queries instead of selecting all columns
2. Add LIMIT clauses for large datasets
3. Use table names that reflect the data domain
4. Keep tables fresh by re-initializing when data changes

## Security

- All endpoints require bearer token authentication
- Tokens are validated using JWT
- API keys stored in environment variables
- No sensitive data logged

## Extending

### Adding New RPC Functions

Simply call init with a different `rpc_name`:

```json
{
  "table_name": "projects",
  "rpc_name": "fn_get_projects"
}
```

### Custom Table Names

Use meaningful table names:

```json
{
  "table_name": "support_tickets",
  "rpc_name": "fn_get_tickets"
}
```

### Direct SQL Queries

You can also use the DuckDB service directly for custom queries:

```python
from app.services.duckdb_service import get_db

db = get_db()
result = db.query_table("SELECT * FROM tickets WHERE priority='high'")
```

## Troubleshooting

### "Table not found" error
- Make sure you called `/api/chat/init` first
- Verify the table_name matches what you used in init

### Natural language not recognized
- Try more specific, SQL-like terms
- Check that columns exist in the table
- Use `/api/chat/tables/{table_name}` to verify schema

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and billing
- Service will fallback to simple SQL generation

### DuckDB connection errors
- Ensure `DUCKDB_PATH` directory exists (for file-based)
- Check file permissions
- Restart the server

## Future Enhancements

- [ ] Multi-table joins
- [ ] Caching for repeated queries
- [ ] Query optimization suggestions
- [ ] Export results to CSV/JSON
- [ ] Real-time data subscription
- [ ] Advanced analytics features
