from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Incident Response - Simulated Production App"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # PostgreSQL Database URL using asyncpg driver
    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5432/incident_response_db"

    # Global Incident Simulation Defaults
    SIMULATE_DB_TIMEOUT: bool = False
    SIMULATE_PAYMENT_FAILURE: bool = False
    SIMULATE_SLOW_API: bool = False
    SIMULATE_SLOW_API_LATENCY_MS: int = 3000
    SIMULATE_BACKGROUND_FAILURE: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
