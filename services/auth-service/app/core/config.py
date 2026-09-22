from pydantic import (
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()