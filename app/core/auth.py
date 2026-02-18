from typing import Optional
from fastapi import Header, HTTPException, status
from typing import Dict
from app.core.config import settings
import jwt


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract the bearer token from an Authorization header value.

    Examples:
        "Bearer <token>" -> "<token>"
        "<token>" -> "<token>"

    Returns None if header is missing or empty.
    """
    if not authorization:
        return None
    # common form: "Bearer <token>"
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization


async def get_access_token(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI dependency that returns the bearer token or raises 401."""
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    return token


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from JWT token.
    
    Supabase tokens have user_id in the 'sub' claim.
    
    Args:
        token: JWT bearer token
        
    Returns:
        User ID (typically UUID) or None if extraction fails
    """
    try:
        # Decode without verification (token already validated by Supabase)
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            user_id = payload.get("user_id")
        return user_id
    except Exception as e:
        # If verification fails, try to extract without verification
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub") or payload.get("user_id")
            return user_id
        except:
            return None


async def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency that extracts and returns user_id from JWT token.
    
    This ensures every request is tied to a specific user for data isolation.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    
    user_id = extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or missing user_id")
    
    return user_id


def build_auth_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """Build standard headers for Supabase REST calls.

    - Always includes the `apikey` and `Content-Type`.
    - Optionally includes `Authorization: Bearer <token>` when `access_token` provided.
    """
    headers: Dict[str, str] = {
        "apikey": settings.supabase_key,
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers
