"""
Example usage of the Chat API with DuckDB integration.

This script demonstrates how to:
1. Authenticate a user
2. Initialize a chat session by storing API data in DuckDB
3. Query the stored data using natural language
"""

import httpx
import json
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
EMAIL = "user@example.com"
PASSWORD = "password123"

class ChatAPIClient:
    """Client for interacting with the Chat API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.client = httpx.Client()
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate and get access token."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/auth/token",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            return bool(self.access_token)
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _get_headers(self) -> dict:
        """Get headers with authorization token."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def init_chat(self, table_name: str, rpc_name: str = "fn_get_tickets") -> dict:
        """Initialize chat by storing API data in DuckDB."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/chat/init",
                headers=self._get_headers(),
                json={
                    "table_name": table_name,
                    "rpc_name": rpc_name
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"is_success": False, "message": str(e)}
    
    def query(self, table_name: str, message: str) -> dict:
        """Query stored data using natural language."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/chat/query",
                headers=self._get_headers(),
                json={
                    "table_name": table_name,
                    "message": message
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"is_success": False, "message": str(e)}
    
    def list_tables(self) -> dict:
        """List all available tables."""
        try:
            response = self.client.get(
                f"{self.base_url}/api/chat/tables",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"tables": [], "count": 0, "error": str(e)}
    
    def get_table_info(self, table_name: str) -> dict:
        """Get information about a table."""
        try:
            response = self.client.get(
                f"{self.base_url}/api/chat/tables/{table_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"is_success": False, "message": str(e)}
    
    def close(self):
        """Close the client."""
        self.client.close()


def print_result(result: dict, title: str = "Result"):
    """Pretty print a result."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))


def main():
    """Main example flow."""
    client = ChatAPIClient()
    
    try:
        # Step 1: Authenticate
        print("Step 1: Authenticating...")
        if not client.authenticate(EMAIL, PASSWORD):
            print("Authentication failed!")
            return
        print("✓ Authenticated successfully")
        
        # Step 2: Initialize chat with tickets data
        print("\nStep 2: Initializing chat with tickets data...")
        init_result = client.init_chat("tickets", "fn_get_tickets")
        print_result(init_result, "Init Chat Result")
        
        if not init_result.get("is_success"):
            print("Failed to initialize chat")
            return
        
        # Step 3: List available tables
        print("\nStep 3: Listing available tables...")
        tables = client.list_tables()
        print_result(tables, "Available Tables")
        
        # Step 4: Get table information
        print("\nStep 4: Getting table information...")
        table_info = client.get_table_info("tickets")
        print_result(table_info, "Tickets Table Schema")
        
        # Step 5: Query examples
        queries = [
            "Show me all tickets",
            "How many tickets are there?",
            "Show the latest 5 tickets",
            "Show open tickets",
            "Count tickets by status"
        ]
        
        for query in queries:
            print(f"\nStep 5.{queries.index(query)+1}: Querying: '{query}'")
            result = client.query("tickets", query)
            print_result(result, f"Query: {query}")
            
            if result.get("is_success") and result.get("result"):
                print(f"\n📊 Found {result.get('count', 0)} results")
                print(f"Generated SQL: {result.get('query')}")
                print("\nData Preview (first 3 rows):")
                for i, row in enumerate(result["result"]["data"][:3]):
                    print(f"  {i+1}. {json.dumps(row)}")
        
    finally:
        client.close()
        print("\n✓ Client closed")


if __name__ == "__main__":
    main()
