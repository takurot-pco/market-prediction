"""
Application settings.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://market:market@localhost:5432/market",
        alias="DATABASE_URL",
    )

    # JWT Settings
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )
    jwt_expire_minutes: int = Field(
        default=60 * 24,  # 24 hours
        alias="JWT_EXPIRE_MINUTES",
    )

    # Auth Provider (mock for development, azure for production)
    auth_provider: str = Field(
        default="mock",
        alias="AUTH_PROVIDER",
    )


settings = Settings()
