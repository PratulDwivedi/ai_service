from typing import Optional
from app.core.config import settings
from app.core.http import http_client
from app.core.auth import build_auth_headers
from app.schemas import user as user_schemas
import httpx

async def token(form_data: user_schemas.UserLogin) -> Optional[str]:
    """
    Authenticate user against Supabase REST API.
    
    Makes a request to the Supabase auth endpoint using email and password,
    and returns the access_token if successful.
    
    Args:
        form_data: User login credentials (email and password)
        
    Returns:
        Access token if authentication succeeds, None otherwise
    """
    try:
        # Construct the auth endpoint URL
        auth_url = f"{settings.supabase_url}/auth/v1/token"
        
        # Set required headers with API key
        headers = build_auth_headers()
        
        # Prepare request body
        body = {
            "email": form_data.email,
            "password": form_data.password,
        }
        
        # Make REST API call with grant_type=password
        response = await http_client.post(
            auth_url,
            json=body,
            headers=headers,
            params={"grant_type": "password"},
        )
        
        # Extract and return only the access token
        if "access_token" in response:
            return response["access_token"]
        
        return None
        
    except Exception:
        # Return None on any error (invalid credentials, network error, etc.)
        return None

async def profile(access_token: str) -> Optional[dict]:
    """
    Get user profile information by calling Supabase RPC `fn_get_user_profile`.

    Args:
        access_token: Supabase access token (Bearer token)

    Returns:
        Parsed JSON response from the RPC call or None on error
    """
    try:
        # Construct the RPC endpoint URL
        profile_url = f"{settings.supabase_url}/rest/v1/rpc/fn_get_user_profile"

        # Set required headers with API key and Authorization
        headers = build_auth_headers(access_token)

        # Call the RPC endpoint (POST with empty JSON body)
        response = await http_client.post(
            profile_url,
            json={},
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
                "message": "error when getting profile",
                "data": body_json,
            }

        return body_json

    except Exception:
        # Return None on any error (invalid token, network error, etc.)
        return None


async def register_user(user: user_schemas.UserCreate) -> Optional[dict]:
    """Create a new user using Supabase Auth REST API."""
    
    try:
        auth_url = f"{settings.supabase_url}/auth/v1/signup"

        body = {
            "email": user.email,
            "password": user.password,
        }

        headers = build_auth_headers()

        # request but do not raise on non-2xx so we can inspect Supabase error body
        response = await http_client.post(
            auth_url,
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
                "message": "error when creating user",
                "data": body_json,
            }

        return {
                "is_success": True, 
                "status_code": status_code, 
                "data": body_json, 
                "message": "user created successfully"}

    except httpx.RequestError as e:
        # Network-level error
        return {
            "is_success": False,
            "message": "Network error",
            "status_code": 400,
            "data": str(e)
        }

    except Exception as e:
        # Unexpected error
        return {
            "is_success": False,
            "message": "Unexpected error",
            "status_code": 400,
            "data": str(e)
        }