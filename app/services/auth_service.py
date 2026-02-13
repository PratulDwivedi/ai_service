from typing import Optional

from app.core import security
from app.core.config import settings
from app.core.http import http_client
from app.schemas import user as user_schemas
from app.db.supabase import get_supabase_client


# simple service interacting with supabase users table (used for signup)
supabase = get_supabase_client()


def register_user(user: user_schemas.UserCreate) -> user_schemas.UserOut:
    hashed = security.get_password_hash(user.password)
    data = {"email": user.email, "hashed_password": hashed}
    response = supabase.table("users").insert(data).execute()
    record = response.data[0]
    return user_schemas.UserOut(id=record.get("id"), email=record.get("email"))


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
        headers = {
            "apikey": settings.supabase_key,
            "Content-Type": "application/json",
        }
        
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
        headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Call the RPC endpoint (POST with empty JSON body)
        response = await http_client.post(
            profile_url,
            json={},
            headers=headers,
        )

        return response

    except Exception:
        # Return None on any error (invalid token, network error, etc.)
        return None
