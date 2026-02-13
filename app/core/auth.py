from typing import Optional
from fastapi import Header, HTTPException, status
from typing import Dict
from app.core.config import settings


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
