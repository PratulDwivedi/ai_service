# User Data Isolation - Architecture Diagrams

## 1. Request Flow with Isolation

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  CLIENT REQUEST                                                    │
│  POST /api/chat/init                                              │
│  Authorization: Bearer eyJ...sub=user_a_123...                    │
│  Body: {"table_name": "tickets", "rpc_name": "fn_get_tickets"}    │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FastAPI Dependency Injection                                      │
│                                                                     │
│  @Depends(get_user_id_from_token)                                 │
│      ├─ Extract Authorization header                              │
│      ├─ Parse: "Bearer <token>"                                   │
│      ├─ Decode JWT token                                          │
│      ├─ payload['sub'] = "user_a_123"                             │
│      └─ Return: "user_a_123"                                      │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                ▼     user_id = "user_a_123"
┌──────────────────────────────────────────────────────────────────────┐
│  Route Handler: init_chat()                                         │
│                                                                     │
│  async def init_chat(                                              │
│      request: ChatInitRequest,                                    │
│      user_id: str = "user_a_123"  ← Injected                     │
│  ):                                                                │
│      chat_service = get_chat_service(user_id)                    │
│      # Returns ChatService instance for "user_a_123" only         │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ChatService Cache                                                 │
│  _chat_services = {                                               │
│      "user_a_123": <ChatService with user_a's db>,              │
│      "user_b_456": <ChatService with user_b's db>,              │
│      ...                                                           │
│  }                                                                 │
│                                                                     │
│  get_chat_service("user_a_123")                                  │
│      → Returns _chat_services["user_a_123"]                      │
│      → This service ONLY accesses User A's data                  │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ChatService Instance for User A                                   │
│                                                                     │
│  class ChatService:                                                │
│      def __init__(self, user_id="user_a_123"):                  │
│          self.user_id = "user_a_123"                             │
│          self.db = get_db("user_a_123")                          │
│          # Get ONLY User A's database                             │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DuckDB Service Cache                                              │
│  _user_dbs = {                                                    │
│      "user_a_123": <DuckDBService(user_a's connection)>,         │
│      "user_b_456": <DuckDBService(user_b's connection)>,         │
│      ...                                                           │
│  }                                                                 │
│                                                                     │
│  get_db("user_a_123")                                            │
│      → Returns _user_dbs["user_a_123"]                           │
│      → Connection to ONLY User A's database                      │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DuckDB Instance for User A                                        │
│                                                                     │
│  class DuckDBService:                                              │
│      def __init__(self, user_id="user_a_123"):                  │
│          if ":memory:":                                           │
│              db_path = ":memory:?user=user_a_123"               │
│          else:                                                     │
│              db_path = "/data/duckdb/user_abc123/data.duckdb"   │
│          self.conn = duckdb.connect(db_path)                     │
│          # Only User A's data accessible                          │
│                                                                     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DuckDB Operations                                                 │
│                                                                     │
│  self.conn.execute(f"CREATE TABLE {table_name} AS ...")         │
│      ├─ Executes ONLY on User A's connection                     │
│      ├─ CREATE TABLE tickets (stores User A's data)              │
│      └─ User B's connection has no visibility                    │
│                                                                     │
│  If User B tries same operation:                                  │
│      └─ Uses different connection (user_b_456)                   │
│         Creates table in DIFFERENT database                       │
│         No conflict                                                │
│                                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-User Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API SERVER                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                Request Handler                                   │  │
│  │                                                                  │  │
│  │  Request A                       Request B                       │  │
│  │  Token: user_a_123               Token: user_b_456              │  │
│  │    │                               │                             │  │
│  │    ├─ Extract user_id            ├─ Extract user_id           │  │
│  │    │   = "user_a_123"            │   = "user_b_456"           │  │
│  │    │                               │                             │  │
│  │    ▼                               ▼                             │  │
│  │  ┌──────────────────┐          ┌──────────────────┐            │  │
│  │  │ ChatService(A)   │          │ ChatService(B)   │            │  │
│  │  │ .user_id = a_123 │          │ .user_id = b_456 │            │  │
│  │  │ .db = db(a_123)  │          │ .db = db(b_456)  │            │  │
│  │  └──────────┬───────┘          └───────┬─────────┘            │  │
│  │             │                          │                       │  │
│  │             ▼                          ▼                       │  │
│  │    ┌──────────────────┐      ┌──────────────────┐            │  │
│  │    │ DuckDB (A)       │      │ DuckDB (B)       │            │  │
│  │    │ path: /user_a... │      │ path: /user_b... │            │  │
│  │    │ Tables:          │      │ Tables:          │            │  │
│  │    │ - tickets        │      │ - tickets        │            │  │
│  │    │ - projects       │      │ - projects       │            │  │
│  │    └──────────────────┘      └──────────────────┘            │  │
│  │             │                          │                       │  │
│  │             ▼                          ▼                       │  │
│  │    ┌──────────────────┐      ┌──────────────────┐            │  │
│  │    │ User A's Data    │      │ User B's Data    │            │  │
│  │    │ tickets: 25 rows │      │ tickets: 15 rows │            │  │
│  │    │ projects: 5      │      │ projects: 8      │            │  │
│  │    └──────────────────┘      └──────────────────┘            │  │
│  │                                                                  │  │
│  │  ✓ Completely Isolated                                        │  │
│  │  ✓ Same table names, different databases                     │  │
│  │  ✓ User A can't see User B's data                            │  │
│  │  ✓ User B can't see User A's data                            │  │
│  │                                                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Global Caches:                                                      │
│  ┌─────────────────────────┬──────────────────────┐                 │
│  │ _chat_services = {      │ _user_dbs = {        │                 │
│  │   "user_a_123": ◄─ ┐    │   "user_a_123": ◄─ ┐│                 │
│  │   "user_b_456": ◄─┐│    │   "user_b_456": ◄─┐││                 │
│  │ }                 ││    │ }                  │││                 │
│  └─────────────────────┬──────────────────────┘││                 │
│                        │                       │││                 │
│                        └───────┬───────────────┘││                 │
│                                │               ││                 │
└────────────────────────────────┼───────────────┼┼─────────────────┘
                                 │               ││
                                 ▼               ▼▼
                        Actually Different Connections
                        No Cross-User Data Access
```

---

## 3. File System Organization (Persistent Storage)

```
/data/duckdb/
│
├── user_abc123/              ← User A (hash of user_id)
│   └── data.duckdb          ← User A's database file
│       ├── tickets table    ← User A's tickets
│       └── projects table   ← User A's projects
│
├── user_def456/              ← User B (hash of user_id)
│   └── data.duckdb          ← User B's database file
│       ├── tickets table    ← User B's tickets  (different file!)
│       └── projects table   ← User B's projects (different file!)
│
├── user_ghi789/              ← User C
│   └── data.duckdb
│       └── ... (User C's tables)
│
└── user_jkl012/              ← User D
    └── data.duckdb
        └── ... (User D's tables)

Key Points:
✓ Each user has separate directory
✓ Each user has separate data.duckdb file
✓ Same table names don't conflict (different files)
✓ OS-level file permissions can provide additional security
✓ Backup/restore is per-user easy
```

---

## 4. In-Memory Organization

```
Python Process Memory
│
├─ _chat_services (Dict)
│  │
│  ├─ "user_a_123" → ChatService(user_id="user_a_123")
│  │                    └─ db → DuckDBService(user_id="user_a_123")
│  │                             └─ conn → duckdb.Connection(":memory:?user=user_a_123")
│  │                                          └─ Tables: tickets, projects
│  │                                             Data: User A's rows
│  │
│  ├─ "user_b_456" → ChatService(user_id="user_b_456")
│  │                    └─ db → DuckDBService(user_id="user_b_456")
│  │                             └─ conn → duckdb.Connection(":memory:?user=user_b_456")
│  │                                          └─ Tables: tickets, projects
│  │                                             Data: User B's rows
│  │
│  └─ "user_c_789" → ChatService(user_id="user_c_789")
│                       └─ db → DuckDBService(user_id="user_c_789")
│                                └─ conn → duckdb.Connection(":memory:?user=user_c_789")
│                                             └─ Tables: tickets, projects
│                                                Data: User C's rows
│
└─ _user_dbs (Dict) [referenced by ChatServices above]
   │
   ├─ "user_a_123" → DuckDBService(...)
   ├─ "user_b_456" → DuckDBService(...)
   └─ "user_c_789" → DuckDBService(...)

Key Points:
✓ Each connection is separate in memory
✓ Isolation is by DuckDB connection pool
✓ Tables only exist in their connection
✓ Zero cross-user data visibility
✓ Data lost on server restart (unless persisted to file)
```

---

## 5. Query Isolation Example

```
┌─────────────────────────────────────────────────────────────┐
│  SCENARIO: User A and User B both have "tickets" table     │
└─────────────────────────────────────────────────────────────┘

User A:
  POST /api/chat/init with token_a
  → create_table("tickets", user_a_data)
  → Stored in: _user_dbs["user_a_123"].conn
      └─ CREATE TABLE tickets (25 rows from user_a_tickets)
  
  Result: ✓ User A's "tickets" created

User B:
  POST /api/chat/init with token_b
  → create_table("tickets", user_b_data)
  → Stored in: _user_dbs["user_b_456"].conn
      └─ CREATE TABLE tickets (15 rows from user_b_tickets)
  
  Result: ✓ User B's "tickets" created
  
  No conflict! Different connections, different tables.

User A queries:
  POST /api/chat/query with token_a
  {"table_name": "tickets", "message": "show all"}
  
  → chat_service = _chat_services["user_a_123"]
  → db = _user_dbs["user_a_123"]
  → db.query("SELECT * FROM tickets")
     └─ Executes on User A's connection
     └─ Sees 25 rows (User A's data only)
  
  Result: ✓ User A gets User A's data

User B queries:
  POST /api/chat/query with token_b  
  {"table_name": "tickets", "message": "show all"}
  
  → chat_service = _chat_services["user_b_456"]
  → db = _user_dbs["user_b_456"]
  → db.query("SELECT * FROM tickets")
     └─ Executes on User B's connection
     └─ Sees 15 rows (User B's data only)
  
  Result: ✓ User B gets User B's data

User A tries to see User B's data:
  POST /api/chat/query with token_a
  {"table_name": "tickets", "message": "show all"}
  
  → chat_service = _chat_services["user_a_123"]
  → db = _user_dbs["user_a_123"]
  → db.query("SELECT * FROM tickets")
     └─ Executes on User A's connection only
     └─ User A's "tickets" table exists with 25 rows
     └─ User B's connection is completely separate
     └─ User B's 15 rows are invisible
  
  Result: ✓ User A cannot see User B's data
          ✓ User A only sees their own 25 rows
```

---

## 6. Security Layers

```
┌────────────────────────────────────────────────┐
│ Layer 1: Token Authentication                 │
│ ────────────────────────────────────────────┬─│
│  Authorization header → "Bearer token"       │ │
│  Invalid/Missing → 401 Unauthorized          │ │
└────────────────────────────────────────────┼─┘
                                             │
                                             ▼
┌────────────────────────────────────────────────┐
│ Layer 2: User ID Extraction                   │
│ ────────────────────────────────────────────┬─│
│  JWT decode → Extract 'sub' claim           │ │
│  user_id = "user_a_123"                     │ │
│  Invalid token → Exception, 401             │ │
└────────────────────────────────────────────┼─┘
                                             │
                                             ▼
┌────────────────────────────────────────────────┐
│ Layer 3: Service Isolation                    │
│ ────────────────────────────────────────────┬─│
│  get_chat_service(user_id)                  │ │
│  → ChatService instance for THIS user only  │ │
│  → Other users' services are separate       │ │
└────────────────────────────────────────────┼─┘
                                             │
                                             ▼
┌────────────────────────────────────────────────┐
│ Layer 4: Database Isolation                   │
│ ────────────────────────────────────────────┬─│
│  get_db(user_id)                            │ │
│  → DuckDB connection for THIS user only    │ │
│  → Other users' connections are separate   │ │
│  → Even same queries return different data │ │
└────────────────────────────────────────────┼─┘
                                             │
                                             ▼
┌────────────────────────────────────────────────┐
│ Layer 5: Data Confidentiality                 │
│ ────────────────────────────────────────────┬─│
│  Query executes on THIS user's database    │ │
│  Results only contain THIS user's data     │ │
│  Other users' tables are invisible         │ │
└────────────────────────────────────────────┬─┘
```

---

## 7. Comparison: Before vs After

```
BEFORE (❌ INSECURE):
═════════════════

        All Users
           │
           ▼
    ┌─────────────┐
    │ Single DB   │
    │ ├─ tickets  │ ← User A's data, visible to all!
    │ ├─ projects │ ← User B's data, visible to all!
    │ └─ users    │ ← User C's data, visible to all!
    └─────────────┘

Problem: 
- User A can query User B's data
- No isolation at all
- Data privacy violation
- GDPR/HIPAA non-compliant

═════════════════════════════════════════════════════════════

AFTER (✅ SECURE):
═════════════════

User A Request     User B Request     User C Request
       │                  │                  │
       ▼                  ▼                  ▼
┌────────────┐    ┌────────────┐    ┌────────────┐
│ DuckDB A   │    │ DuckDB B   │    │ DuckDB C   │
│ ├─ tickets │    │ ├─ tickets │    │ ├─ tickets │
│ └─ projects│    │ └─ projects│    │ └─ projects│
└────────────┘    └────────────┘    └────────────┘

Isolated:
- User A can only see their data
- User B can only see their data
- User C can only see their data
- Complete multi-tenant isolation
- GDPR/HIPAA compliant
```

---

## 8. JWT Token Extraction

```
HTTP Request:
┌────────────────────────────────────────────────────┐
│ POST /api/chat/init                               │
│ Authorization: Bearer eyJhbGciOiJIUzI1NiIs...    │
│ Content-Type: application/json                    │
│                                                     │
│ {"table_name": "tickets", ...}                    │
└─────────────────────┬──────────────────────────────┘
                      │
                      ▼
          Extract Bearer Token
          "eyJhbGciOiJIUzI1NiIs..."
                      │
                      ▼
          Decode JWT Token
          {
            "sub": "user_a_123",        ← This is extracted!
            "email": "user@example.com",
            "iat": 1676000000,
            "exp": 1676003600
          }
                      │
                      ▼
          Get user_id from 'sub' claim
          user_id = "user_a_123"
                      │
                      ▼
          Pass to dependency injection
          async def init_chat(..., user_id: str):
                      │
                      ▼
          Use user_id for isolation
          chat_service = get_chat_service(user_id)
```

This ensures every request is tied to a specific user for complete data isolation.
