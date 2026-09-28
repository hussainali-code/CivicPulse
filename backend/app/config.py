from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    PORT: int = Field(default=8000)
    SECRET_KEY: str = Field(default="default_insecure_secret_key_change_in_prod")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://civicpulse_user:civicpulse_password@postgres:5432/civicpulse_db"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    
    # CORS
    ALLOWED_ORIGINS: str | list[str] = Field(
        default="http://localhost,http://localhost:80,http://localhost:5173"
    )
    
    # AI Triage
    TRIAGE_PROVIDER: str = Field(default="simulated")  # simulated, rules, groq, ollama
    GROQ_API_KEY: str = Field(default="")
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.2:1b")
    
    # Fault Injection (for testing)
    FAILURE_INJECTION: bool = Field(default=False)
    MALFORMED_INJECTION: bool = Field(default=False)

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
