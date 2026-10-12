from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRETIUM_", env_file=".env")

    database_url: str = "postgresql+psycopg://pretium:pretium@localhost:5432/pretium"
    redis_url: str = "redis://localhost:6379/0"
    admin_api_key: str = "change-me"
    cache_ttl_list: int = 60
    cache_ttl_detail: int = 60
    cache_ttl_history: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
