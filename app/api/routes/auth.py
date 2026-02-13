from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import user as user_schemas
from app.services import auth_service

router = APIRouter()

@router.post("/signup", response_model=user_schemas.UserOut)
def signup(user: user_schemas.UserCreate):
    return auth_service.register_user(user)

@router.post("/login")
def login(form_data: user_schemas.UserLogin):
    token = auth_service.authenticate_user(form_data)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}
