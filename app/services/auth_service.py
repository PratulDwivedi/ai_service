from datetime import timedelta
from typing import Optional

from app.core import security
from app.schemas import user as user_schemas
from app.db.supabase import get_supabase_client

# simple service interacting with supabase users table

supabase = get_supabase_client()


def register_user(user: user_schemas.UserCreate) -> user_schemas.UserOut:
    hashed = security.get_password_hash(user.password)
    data = {"email": user.email, "hashed_password": hashed}
    response = supabase.table("users").insert(data).execute()
    record = response.data[0]
    return user_schemas.UserOut(id=record["id"], email=record["email"])


def authenticate_user(form_data: user_schemas.UserLogin) -> Optional[str]:
    response = supabase.table("users").select("*").eq("email", form_data.email).execute()
    if not response.data:
        return None
    user = response.data[0]
    if not security.verify_password(form_data.password, user["hashed_password"]):
        return None
    access_token = security.create_access_token(
        data={"sub": str(user["id"])}
    )
    return access_token
