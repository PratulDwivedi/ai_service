from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.schemas import user as user_schemas
from app.services import auth_service

router = APIRouter()

@router.post("/signup", response_model=user_schemas.UserOut)
def signup(user: user_schemas.UserCreate):
    return auth_service.register_user(user)

@router.post("/token")
async def login(form_data: user_schemas.UserLogin):
    token = await auth_service.token(form_data)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/profile")
async def profile(authorization: str = Header(None)):
    """Return the user profile by forwarding the bearer token to the service."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    # Expect header like: "Bearer <token>"
    token = authorization.split(" ", 1)[1] if " " in authorization else authorization

    profile_data = await auth_service.profile(token)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return profile_data
