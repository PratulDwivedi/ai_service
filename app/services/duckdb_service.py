import duckdb
import pandas as pd
from typing import Any, List, Optional, Dict
import json
import os
import tempfile
import hashlib

# DuckDB base path for multi-tenant support
DB_BASE_PATH = os.getenv("DUCKDB_PATH", ":memory:")

class DuckDBService:
    """Service for managing DuckDB operations with multi-tenant isolation."""
    
    def __init__(self, user_id: str, db_base_path: str = DB_BASE_PATH):
        """
        Initialize DuckDB connection with per-user isolation.
        
        Args:
            user_id: Unique identifier for the user (from JWT token)
            db_base_path: Base path for database storage
        """
        self.user_id = user_id
        self.db_base_path = db_base_path
        
        # Create user-specific database path
        if db_base_path == ":memory:":
            # Use in-memory with user isolation
            self.db_path = f":memory:?user={user_id}"
        else:
            # Create user-specific file path
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
            db_dir = os.path.join(db_base_path, f"user_{user_hash}")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "data.duckdb")
        
        self.conn = duckdb.connect(self.db_path)
        self._init_metadata_table()
    
    def _init_metadata_table(self):
        """Initialize metadata table for tracking user's tables."""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS _metadata (
                    table_name VARCHAR,
                    rpc_name VARCHAR,
                    created_at TIMESTAMP,
                    row_count INTEGER,
                    PRIMARY KEY (table_name)
                )
            """)
        except:
            pass
    
    def _flatten_nested_objects(self, records: List[Dict]) -> List[Dict]:
        """
        Flatten nested objects in data records.
        
        Converts nested dicts like:
            {"id": 1, "category": {"name": "Electronics"}}
        To:
            {"id": 1, "category_name": "Electronics"}
        
        Args:
            records: List of records with nested objects
            
        Returns:
            List of flattened records
        """
        flattened = []
        
        for record in records:
            flat_record = {}
            
            for key, value in record.items():
                if isinstance(value, dict) and value:
                    # Flatten nested dict
                    for nested_key, nested_value in value.items():
                        if not isinstance(nested_value, (dict, list)):
                            flat_key = f"{key}_{nested_key}"
                            flat_record[flat_key] = nested_value
                        else:
                            # Skip complex nested structures
                            flat_key = f"{key}_{nested_key}"
                            flat_record[flat_key] = json.dumps(nested_value) if nested_value else None
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # Convert list of dicts to JSON
                    flat_record[key] = json.dumps(value)
                else:
                    flat_record[key] = value
            
            flattened.append(flat_record)
        
        return flattened
    
    def create_table_from_response(self, table_name: str, data: Any) -> bool:
        """
        Create a DuckDB table from API response data.
        
        Handles Supabase-style responses with nested objects.
        
        Args:
            table_name: Name of the table to create
            data: API response data (list of dicts, dict with 'data' key, or pandas DataFrame)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract actual data from Supabase response format
            records = []
            
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Handle Supabase response format: {"data": [...], "paging": {...}, "message": "..."}
                if "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                else:
                    # Single record
                    records = [data]
            elif isinstance(data, pd.DataFrame):
                df = data
                # Drop table if already exists
                try:
                    self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                except:
                    pass
                self.conn.register(table_name, df)
                self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
                return True
            else:
                return False
            
            if not records:
                return False
            
            # Flatten nested objects (vendor, category, location, etc.)
            flattened_records = self._flatten_nested_objects(records)
            
            # Convert to DataFrame
            df = pd.DataFrame(flattened_records)
            
            # Drop table if already exists
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            except:
                pass
            
            # Create table from dataframe
            self.conn.register(table_name, df)
            
            # Persist to disk
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
            
            # Update metadata
            row_count = len(df)
            try:
                self.conn.execute(f"""
                    INSERT OR REPLACE INTO _metadata 
                    (table_name, rpc_name, created_at, row_count)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                """, [table_name, table_name, row_count])
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def query_table(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute a SQL query on DuckDB.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query result as dict with columns and data
        """
        try:
            result = self.conn.execute(query).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            
            if result:
                return {
                    "columns": columns,
                    "data": [dict(zip(columns, row)) for row in result]
                }
            return {"columns": columns, "data": []}
        except Exception as e:
            return None
    
    def get_table_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get schema of a table."""
        try:
            schema = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            return {row[0]: row[1] for row in schema}
        except:
            return None
    
    def get_table_info(self, table_name: str) -> Optional[str]:
        """Get detailed table information for context."""
        try:
            schema = self.get_table_schema(table_name)
            count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchall()
            count = count_result[0][0] if count_result else 0
            
            schema_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in schema.items()])
            return f"Table '{table_name}' has {count} rows with columns:\n{schema_str}"
        except:
            return None
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            result = self.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
            return [row[0] for row in result]
        except:
            return []
    
    def sql_to_natural_language(self, sql_query: str) -> str:
        """
        Convert SQL query to natural language explanation.
        
        Args:
            sql_query: SQL query to explain
            
        Returns:
            Natural language explanation of the query
        """
        sql_upper = sql_query.upper().strip()
        
        # Simple pattern matching for common queries
        explanations = {
            "SELECT COUNT": "Count the number of records",
            "SELECT DISTINCT": "Get unique values",
            "GROUP BY": "Group results by",
            "ORDER BY": "Sort results by",
            "WHERE": "Filter records where",
            "JOIN": "Combine data from multiple tables",
            "LIMIT": "Return a limited number of results",
            "LIKE": "Match text patterns",
        }
        
        explanation = "Query: "
        for keyword, desc in explanations.items():
            if keyword in sql_upper:
                explanation += f"{desc}. "
        
        return explanation if explanation != "Query: " else "Execute database query"
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Create an embedding for text (requires OpenAI API).
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def add_embeddings_column(self, table_name: str, text_column: str, embedding_column: str = "embedding") -> bool:
        """
        Add embeddings for a text column (expensive operation).
        
        Args:
            table_name: Table to update
            text_column: Column containing text to embed
            embedding_column: Name of new embedding column
            
        Returns:
            True if successful
        """
        try:
            # Check if column already exists
            schema = self.get_table_schema(table_name)
            if embedding_column in schema:
                return True
            
            # Get unique texts from the column
            result = self.conn.execute(f"SELECT DISTINCT {text_column} FROM {table_name} WHERE {text_column} IS NOT NULL LIMIT 1000").fetchall()
            
            if not result:
                return False
            
            # Create embeddings for each unique text
            embeddings_dict = {}
            for (text,) in result:
                if text not in embeddings_dict:
                    embedding = self.create_embedding(str(text))
                    if embedding:
                        embeddings_dict[text] = embedding
            
            # Create a temporary table with embeddings
            embedding_records = [
                {text_column: text, embedding_column: json.dumps(emb)}
                for text, emb in embeddings_dict.items()
            ]
            
            temp_df = pd.DataFrame(embedding_records)
            temp_table_name = f"_{table_name}_embeddings"
            
            self.conn.register(temp_table_name, temp_df)
            self.conn.execute(f"CREATE TABLE {temp_table_name} AS SELECT * FROM {temp_table_name}")
            
            return True
        except Exception as e:
            print(f"Error adding embeddings: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


# Global connection storage - one per user
_user_dbs: Dict[str, DuckDBService] = {}

def get_db(user_id: str) -> DuckDBService:
    """
    Get or create a DuckDB service instance for a specific user.
    
    This ensures complete data isolation between users.
    
    Args:
        user_id: Unique identifier for the user (from JWT token)
        
    Returns:
        User-specific DuckDBService instance
    """
    global _user_dbs
    
    if user_id not in _user_dbs:
        _user_dbs[user_id] = DuckDBService(user_id)
    
    return _user_dbs[user_id]

def close_db(user_id: str):
    """
    Close the database connection for a specific user.
    
    Args:
        user_id: User identifier
    """
    global _user_dbs
    
    if user_id in _user_dbs:
        _user_dbs[user_id].close()
        del _user_dbs[user_id]

def close_all_dbs():
    """Close all database connections."""
    global _user_dbs
    
    for user_id in list(_user_dbs.keys()):
        _user_dbs[user_id].close()
    
    _user_dbs.clear()
