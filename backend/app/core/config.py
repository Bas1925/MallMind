"""Application settings.

All settings are read from environment variables (via pydantic-settings).
A `.env` file at the project root is loaded automatically when running
outside Docker. Inside Docker, variables come from the compose file.

Design notes
------------
- We fail loudly if `DATABASE_URL` is missing. A silently-defaulted DB URL
  is a classic source of "tests pass against localhost, prod talks to a
  dev DB" incidents.
- `cors_origins` accepts either a JSON list or a comma-separated string
  for ergonomics. Validation normalises both into `list[str]`.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Identity / environment ------------------------------------------------
    app_name: str = "MallMind"
    app_version: str = "0.0.1"
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # --- Database --------------------------------------------------------------
    # Required. Example:
    #   postgresql+asyncpg://user:password@host:5432/dbname
    database_url: str = Field(..., description="SQLAlchemy async DSN for PostgreSQL")

    # --- HTTP ------------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Search / assistant ----------------------------------------------------
    # local: fastembed on this machine. openai: HTTP embeddings. none: lexical only.
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # OpenAI-compatible chat + embeddings. Empty key means template answers.
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: Any) -> Any:
        """Accept both JSON list syntax and comma-separated strings."""
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                return json.loads(s)
            return [item.strip() for item in s.split(",") if item.strip()]
        return v


settings = Settings()  # type: ignore[call-arg]  # pydantic-settings populates from env
