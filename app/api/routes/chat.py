"""Chat endpoints for querying stored API data with per-user isolation."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import chat as chat_schemas
from app.services.chat_service import get_chat_service
from app.services.duckdb_service import get_db
from app.core.auth import get_access_token, get_user_id_from_token
from app.core.config import settings

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/init", response_model=chat_schemas.ChatInitResponse)
async def init_chat(
    request: chat_schemas.ChatInitRequest,
    user_id: str = Depends(get_user_id_from_token),
    access_token: str = Depends(get_access_token)
):
    """
    Initialize chat by calling an RPC endpoint and storing data in DuckDB.
    
    Data is stored in a user-specific DuckDB instance.
    Each user's data is completely isolated from other users.
    
    Example:
    - Call fn_get_tickets RPC and store in 'tickets' table
    - Data is stored in user's private database
    - Then users can chat about their own tickets data
    """
    chat_service = get_chat_service(user_id)
    
    result = await chat_service.initialize_from_api(
        access_token=access_token,
        api_endpoint=settings.supabase_url,
        table_name=request.table_name,
        rpc_name=request.rpc_name
    )
    
    if not result.get("is_success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to initialize chat")
        )
    
    return chat_schemas.ChatInitResponse(**result)


@router.post("/query", response_model=chat_schemas.ChatResponse)
async def chat_query(
    request: chat_schemas.ChatMessage,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Chat with the stored data using natural language queries.
    
    Queries are executed only on the current user's data.
    
    Examples:
    - "Show me all tickets"
    - "How many open tickets are there?"
    - "List the top 5 most recent tickets"
    - "Show tickets with status 'closed'"
    """
    chat_service = get_chat_service(user_id)
    
    result = await chat_service.chat(
        table_name=request.table_name,
        user_message=request.message
    )
    
    if not result.get("is_success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to process query")
        )
    
    return chat_schemas.ChatResponse(**result)


@router.get("/tables", response_model=chat_schemas.TableListResponse)
async def list_tables(user_id: str = Depends(get_user_id_from_token)):
    """
    List all available tables in the user's DuckDB instance.
    
    Only tables created by this user are returned.
    """
    db = get_db(user_id)
    tables = db.list_tables()
    
    return chat_schemas.TableListResponse(
        tables=tables,
        count=len(tables)
    )


@router.get("/tables/{table_name}", response_model=chat_schemas.TableInfoResponse)
async def get_table_info(
    table_name: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Get information about a specific table in the user's DuckDB.
    
    Returns 404 if the table doesn't exist for this user.
    """
    db = get_db(user_id)
    info = db.get_table_info(table_name)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{table_name}' not found"
        )
    
    return chat_schemas.TableInfoResponse(
        table_name=table_name,
        info=info
    )
