from typing import Optional
from app.core.config import settings
from app.core.http import http_client
from app.core.auth import build_auth_headers

async def save_agent_execution_log(run_id: str,
    node_name: str,
    event_type: str,
    payload: dict | None = None, 
    access_token: str = None) -> Optional[str]:
    """
    Log an event related to an agent run by calling the Supabase RPC `fn_save_agent_execution_log`.
    
    Args:
        run_id: The unique identifier for the agent run
        node_name: The name of the node that generated the event
        event_type: The type of event (e.g., "start", "end", "error")
        payload: Optional dictionary containing additional event data
        access_token: Optional access token for authentication
        
    Returns:
        The response from the RPC call as a dictionary, or None on error
    """
    try:

        url = f"{settings.supabase_url}/rest/v1/rpc/fn_save_agent_execution_log"

        # Set required headers with API key and Authorization
        headers = build_auth_headers(access_token)
        
        # Prepare request body
        body = {
            "p_name" : "Agent Event",
            "p_run_id": run_id,
            "p_node_name": node_name,
            "p_event_type": event_type,
            "p_data": payload
        }
        
        # Make REST API call with grant_type=password
        response = await http_client.post(
            url=url,
            json=body,
            headers=headers,
            raise_for_status=False
        )

        # response is an httpx.Response here
        status_code = response.status_code
        try:
            body_json = response.json()
        except Exception:
            body_json = {"text": response.text}

        if status_code >= 400:
            # Return Supabase's error payload where possible
            return {
                "is_success": False,
                "status_code": status_code,
                "message": "error when logging agent event",
                "data": body_json,
            }

        return body_json

    except Exception:
        # Return None on any error (invalid token, network error, etc.)
        return None
