from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn
from pydantic import SecretStr


class Settings(BaseSettings):
    REDIS_URL: RedisDsn
    SECRET_KEY: str
    MEMBERSHIP_SERVICE_URL: str
    QR_TTL_SECONDS: int = 30
    QR_SCANNER_API_KEY: SecretStr
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()