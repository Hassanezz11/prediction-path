from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CS Student Career Platform")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    token_ttl_minutes: int = int(os.getenv("TOKEN_TTL_MINUTES", "720"))
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'career_platform.db'}")
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    default_ollama_model: str = os.getenv("DEFAULT_OLLAMA_MODEL", "llama3.2")
    cors_origins: list[str] = None

    def __post_init__(self) -> None:
        if self.cors_origins is None:
            raw = os.getenv("CORS_ORIGINS", "*")
            self.cors_origins = [item.strip() for item in raw.split(",") if item.strip()]
        self.upload_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
