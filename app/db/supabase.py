from supabase import create_client

from app.core.config import settings


def get_supabase_client():
    return create_client(settings.supabase_url, settings.supabase_key)
