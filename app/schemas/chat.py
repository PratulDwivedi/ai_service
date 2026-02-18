"""Schemas for chat endpoints."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatInitRequest(BaseModel):
    """Request to initialize chat with API data."""
    table_name: str
    rpc_name: str = "fn_get_assets"
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "assets",
                "rpc_name": "fn_get_assets"
            }
        }


class ChatInitResponse(BaseModel):
    """Response for chat initialization."""
    is_success: bool
    message: str
    table_name: Optional[str] = None
    table_info: Optional[str] = None
    status_code: Optional[int] = None


class ChatMessage(BaseModel):
    """A chat message request."""
    table_name: str
    message: str
    # If true, request a streaming response (SSE). Defaults to false.
    stream: Optional[bool] = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "assets",
                "message": "Show me category-wise asset count",
                "stream": False
            }
        }


class QueryResult(BaseModel):
    """Query result from DuckDB."""
    columns: List[str]
    data: List[Dict[str, Any]]


class ChatResponse(BaseModel):
    """Response from a chat query."""
    is_success: bool
    message: Optional[str] = None
    query: Optional[str] = None
    result: Optional[QueryResult] = None
    count: Optional[int] = None


class TableListResponse(BaseModel):
    """Response listing available tables."""
    tables: List[str]
    count: int


class TableInfoResponse(BaseModel):
    """Response with table information."""
    table_name: str
    info: str
