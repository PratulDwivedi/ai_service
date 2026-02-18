# User Data Isolation - Summary for Questions

## ❓ Your Question: "How is one user's data separate from other users in DuckDB?"

## ✅ Simple Answer

**Each user gets their own DuckDB instance.**

When User A makes a request:
1. We extract their `user_id` from their JWT token
2. We get/create their own ChatService (for User A only)
3. That service accesses User A's own DuckDB (for User A only)
4. User B's data is in a completely different DuckDB instance
5. **Impossible for User A to see User B's data**

---

## 🎯 The Flow

```
User A Request                        User B Request
(token has sub="user_a_123")          (token has sub="user_b_456")
         │                                    │
         ▼                                    ▼
Extract user_id="user_a_123"    Extract user_id="user_b_456"
         │                                    │
         ▼                                    ▼
ChatService(user_a_123)         ChatService(user_b_456)
    ↓                               ↓
DuckDB(user_a_123)              DuckDB(user_b_456)
  ├─ tickets                      ├─ tickets
  │  (User A's data)             │  (User B's data, not visible to A)
  └─ projects                    └─ projects
     (User A's data)                (User B's data, not visible to A)
```

---

## 🔐 Three Levels of Isolation

### 1. Service Level
```python
_chat_services = {
    "user_a_123": ChatService(for User A only),
    "user_b_456": ChatService(for User B only),  ← Different instance!
}
```

### 2. Database Level
```python
_user_dbs = {
    "user_a_123": DuckDB(for User A only),
    "user_b_456": DuckDB(for User B only),  ← Different DuckDB!
}
```

### 3. Storage Level
```
/data/duckdb/
├── user_abc123/data.duckdb    ← User A's database
└── user_def456/data.duckdb    ← User B's database (completely separate file!)
```

---

## 📊 Concrete Example

### Scenario: Both users create "tickets" table

**User A:**
```
POST /api/chat/init
Authorization: Bearer <token for user_a_123>
{
  "table_name": "tickets",
  "rpc_name": "fn_get_tickets"
}

→ DuckDB instance for user_a_123
→ Creates table "tickets" with User A's data
→ Stored in: /data/duckdb/user_abc123/data.duckdb
```

**User B:**
```
POST /api/chat/init  
Authorization: Bearer <token for user_b_456>
{
  "table_name": "tickets",
  "rpc_name": "fn_get_tickets"
}

→ DuckDB instance for user_b_456  (DIFFERENT instance!)
→ Creates table "tickets" with User B's data
→ Stored in: /data/duckdb/user_def456/data.duckdb  (DIFFERENT file!)
```

**Result:**
- Both have "tickets" table ✓
- No conflict (different DuckDB files)
- User A's "tickets" has User A's data
- User B's "tickets" has User B's data
- User A cannot see User B's "tickets"
- User B cannot see User A's "tickets"

---

## 🚫 Attack Prevention

### Attack: User A tries to see User B's data

```
User A's Request:
Authorization: Bearer <user_a_token>
POST /api/chat/query
{"table_name": "tickets", "message": "show all"}

Processing:
1. Extract user_a_123 from token
2. Get ChatService("user_a_123")
3. Get DuckDB("user_a_123")
4. Query on DuckDB("user_a_123")
   → Only sees User A's tables
   → User B's tables don't exist here

Result: User B's data is invisible
```

### Attack: User A tries to guess User B's table names

```
Even if User A knows User B has a "projects" table:

User A's Request:
{"table_name": "projects", "message": "show all"}

Processing:
1. Extract user_a_123
2. Get DuckDB("user_a_123")
3. Query on DuckDB("user_a_123")
   → Looks for "projects" table
   → Not found (only User A's tables here)

Result: Error - "Table 'projects' not found"
```

---

## 💡 How User ID is Extracted

```python
# JWT token from Supabase looks like:
{
  "sub": "user_a_123",        ← This is the user_id!
  "email": "user@example.com",
  "iat": 1676000000
}

# In every request:
@router.post("/chat/init")
async def init_chat(
    request: ChatInitRequest,
    user_id: str = Depends(get_user_id_from_token)  # ← Extracts 'sub'
):
    # user_id is now "user_a_123"
    # Used to get user-specific services
```

---

## 📝 Code Example - Complete Flow

```python
# 1. User makes request with token
POST /api/chat/init
Authorization: Bearer eyJhbGc...sub=user_a_123...

# 2. FastAPI processes request
@router.post("/init")
async def init_chat(
    request: ChatInitRequest,
    user_id: str = Depends(get_user_id_from_token)
):
    # 3. Extract user_id from JWT
    # user_id = "user_a_123"
    
    # 4. Get user-specific chat service
    chat_service = get_chat_service(user_id)
    # Returns ChatService("user_a_123")
    
    # 5. Chat service uses user's database
    # (Inside chat_service)
    result = await self.initialize_from_api(...)
        # (Inside initialize_from_api)
        self.db.create_table(...)
        # (Inside DuckDBService)
        db = get_db(user_id)
        # Returns DuckDB("user_a_123")
        # All queries happen HERE
        
    return result

# Result: Data stored ONLY in User A's DuckDB
```

---

## ✨ Key Points

| Aspect | Before | After |
|--------|--------|-------|
| **DuckDB Instances** | 1 for all users | 1 per user |
| **User A sees User B's data** | ✓ Yes (security hole) | ✗ No (isolated) |
| **Table name conflicts** | ✓ Possible | ✗ Impossible |
| **Where data is stored** | Single file/memory | User-specific directory/memory |
| **Multi-tenant support** | ✗ No | ✓ Yes |

---

## 🎓 The Pattern

```
Every Request:
1. Contains JWT token with user_id in 'sub' claim
2. Extract user_id from token
3. Get user-specific service using user_id
4. Service gets user-specific database using user_id  
5. All operations happen ONLY on that user's data
6. Other users' data is completely invisible
```

This pattern is applied to:
- ✅ Chat initialization
- ✅ Chat queries
- ✅ Table listing
- ✅ Table info
- ✅ All endpoints

---

## 📚 Documents for More Info

1. **[ISOLATION_GUIDE.md](ISOLATION_GUIDE.md)** - Visual guide with examples
2. **[ISOLATION_DIAGRAMS.md](ISOLATION_DIAGRAMS.md)** - Architecture diagrams
3. **[USER_DATA_ISOLATION.md](USER_DATA_ISOLATION.md)** - Complete technical details
4. **[ISOLATION_IMPLEMENTATION.md](ISOLATION_IMPLEMENTATION.md)** - What code changed

---

## ✅ Final Answer

**User data is separated by giving each user their own DuckDB instance.**

```
User_A.db (User A's tables only)
User_B.db (User B's tables only)
User_C.db (User C's tables only)

They never mix. Complete isolation. ✅
```
