"""Chat service for handling natural language queries on DuckDB data."""
from typing import Optional, Dict, Any
from app.services.duckdb_service import get_db
from app.core.http import http_client
from app.core.config import settings
import json

class ChatService:
    """Service for handling chat queries on stored data with user isolation."""
    
    def __init__(self, user_id: str):
        """
        Initialize chat service for a specific user.
        
        Args:
            user_id: Unique user identifier (from JWT token)
        """
        self.user_id = user_id
        self.db = get_db(user_id)
    
    async def initialize_from_api(
        self,
        access_token: str,
        api_endpoint: str,
        table_name: str,
        rpc_name: str = "fn_get_tickets"
    ) -> Dict[str, Any]:
        """
        Call an RPC endpoint and store the response in DuckDB.
        
        Args:
            access_token: Supabase access token
            api_endpoint: Supabase URL
            table_name: Name of the table to create
            rpc_name: Name of the RPC function to call
            
        Returns:
            Result with status and table info
        """
        try:
            from app.core.auth import build_auth_headers
            
            # Build RPC URL
            rpc_url = f"{api_endpoint}/rest/v1/rpc/{rpc_name}"
            headers = build_auth_headers(access_token)
            
            # Call the RPC endpoint
            response = await http_client.post(
                rpc_url,
                json={},
                headers=headers,
                raise_for_status=False
            )
            
            status_code = response.status_code
            try:
                data = response.json()
            except:
                return {
                    "is_success": False,
                    "message": f"Failed to parse API response: {response.text}"
                }
            
            if status_code >= 400:
                return {
                    "is_success": False,
                    "message": f"API error: {data}",
                    "status_code": status_code
                }
            
            # Store response in DuckDB
            # Pass entire response - DuckDBService will extract data array
            success = self.db.create_table_from_response(table_name, data["data"] if "data" in data else data)
            
            if not success:
                return {
                    "is_success": False,
                    "message": "Failed to create table from API response"
                }
            
            # Get table info
            table_info = self.db.get_table_info(table_name)
            
            return {
                "is_success": True,
                "message": f"Successfully stored {rpc_name} data in table '{table_name}'",
                "table_name": table_name,
                "table_info": table_info
            }
        except Exception as e:
            return {
                "is_success": False,
                "message": f"Error initializing chat data: {str(e)}"
            }
    
    async def chat(
        self,
        table_name: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Process a chat message and query the stored data.
        
        Args:
            table_name: Name of the table to query
            user_message: User's natural language query
            
        Returns:
            Query result or error message
        """
        try:
            # Get table schema for context
            schema = self.db.get_table_schema(table_name)
            if not schema:
                return {
                    "is_success": False,
                    "message": f"Table '{table_name}' not found"
                }
            
            # Convert natural language to SQL using OpenAI
            sql_query = await self._convert_to_sql(
                user_message,
                table_name,
                schema
            )
            
            if not sql_query:
                return {
                    "is_success": False,
                    "message": "Could not parse query"
                }
            
            # Execute the query
            result = self.db.query_table(sql_query)
            
            if result is None:
                return {
                    "is_success": False,
                    "message": "Query execution failed"
                }
            
            return {
                "is_success": True,
                "query": sql_query,
                "result": result,
                "count": len(result.get("data", []))
            }
        except Exception as e:
            return {
                "is_success": False,
                "message": f"Error processing chat: {str(e)}"
            }
    
    async def _convert_to_sql(
        self,
        user_message: str,
        table_name: str,
        schema: Dict[str, str]
    ) -> Optional[str]:
        """
        Convert natural language query to SQL using OpenAI API.
        
        Args:
            user_message: Natural language query
            table_name: Name of the table
            schema: Table schema
            
        Returns:
            SQL query string or None
        """
        try:
            # Build schema description
            columns_desc = "\n".join([
                f"- {col} ({dtype})" for col, dtype in schema.items()
            ])
            
            prompt = f"""You are a SQL expert. Convert the following natural language query to a valid DuckDB SQL query.

Table name: {table_name}
Columns: 
{columns_desc}

User query: {user_message}

Return ONLY the SQL query without any markdown formatting or explanation. The query should start with SELECT."""
            
            # Call OpenAI API
            import openai
            
            response = await http_client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 200
                },
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json"
                },
                raise_for_status=False
            )
            
            response_data = response.json()
            
            if response.status_code >= 400:
                # Fallback: simple SQL generation
                return self._simple_sql_fallback(user_message, table_name, schema)
            
            sql = response_data["choices"][0]["message"]["content"].strip()
            
            # Clean up SQL if it has markdown
            if sql.startswith("```"):
                sql = sql.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
            return sql
        except Exception as e:
            # Fallback to simple SQL generation
            return self._simple_sql_fallback(user_message, table_name, schema)
    
    def _simple_sql_fallback(
        self,
        user_message: str,
        table_name: str,
        schema: Dict[str, str]
    ) -> str:
        """
        Simple fallback SQL generation when OpenAI is not available.
        
        Args:
            user_message: Natural language query
            table_name: Table name
            schema: Table schema
            
        Returns:
            Basic SQL query
        """
        message_lower = user_message.lower()
        columns = list(schema.keys())
        
        # Default: select all
        if "all" in message_lower or "show" in message_lower or "list" in message_lower:
            return f"SELECT * FROM {table_name} LIMIT 100"
        
        # Count query
        if "count" in message_lower or "how many" in message_lower:
            return f"SELECT COUNT(*) as total FROM {table_name}"
        
        # Sort by first column descending if "top" or "latest" mentioned
        if "top" in message_lower or "latest" in message_lower or "recent" in message_lower:
            return f"SELECT * FROM {table_name} ORDER BY {columns[0]} DESC LIMIT 10"
        
        # Default: all records with limit
        return f"SELECT * FROM {table_name} LIMIT 50"

# Cache for chat service instances (one per user)
_chat_services: Dict[str, ChatService] = {}

def get_chat_service(user_id: str) -> ChatService:
    """
    Get or create a chat service instance for a specific user.
    
    This ensures each user has their own chat service that only
    accesses their own DuckDB instance.
    
    Args:
        user_id: Unique user identifier
        
    Returns:
        User-specific ChatService instance
    """
    if user_id not in _chat_services:
        _chat_services[user_id] = ChatService(user_id)
    
    return _chat_services[user_id]
