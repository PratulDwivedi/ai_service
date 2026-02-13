from typing import Optional

from fastapi import Header, HTTPException, status


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
