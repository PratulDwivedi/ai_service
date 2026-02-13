import os
from pydantic_settings import BaseSettings, SettingsConfigDict


ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


class Settings(BaseSettings):
    environment: str = ENVIRONMENT
    app_name: str
    debug: bool = False

    supabase_url: str
    supabase_key: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=f".env.{ENVIRONMENT}",
        extra="ignore"
    )


settings = Settings()
