from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import user as user_schemas
from app.services import auth_service
from app.core.auth import get_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup")
async def signup(user: user_schemas.UserCreate):
    return await auth_service.register_user(user)

@router.post("/token")
async def token(form_data: user_schemas.UserLogin):
    """Get the token to call API."""

    token = await auth_service.token(form_data)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/profile")
async def profile(token: str = Depends(get_access_token)):
    """Return the user profile by forwarding the bearer token to the service."""

    profile_data = await auth_service.profile(token)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return profile_data
