"""Central configuration for the Clean Mailbox API.

Two layers of config live here:

1. ``Settings`` (env-driven, via ``apps/api/.env``) — secrets, URLs, limits.
2. Module-level constants — non-secret app behavior (scopes, categories,
   cookie name, log level). Edit these in code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Env-driven settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Session
    session_secret: str = "dev-only-change-me"
    session_cookie_name: str = "cm_session"
    session_cookie_secure: bool = False  # set True behind HTTPS
    session_cookie_samesite: str = "lax"
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # 30 days

    # CORS / redirects
    frontend_url: str = "http://localhost:5173"

    # Storage
    cache_dir: Path = Path("./cache")

    # LLM
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "ollama/gemma3"
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: int = 60

    # Limits
    max_fetch_limit: int = 500
    default_fetch_limit: int = 50
    agent_batch_size: int = 25  # how many emails per agent invocation

    # Logging
    log_level: str = "INFO"

    def ensure_dirs(self) -> None:
        (self.cache_dir / "users").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "data").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


# ---------------------------------------------------------------------------
# Static (code-level) configuration
# ---------------------------------------------------------------------------

# Google OAuth scopes. ``gmail.modify`` is required to add labels (we never
# delete or remove labels — see ``gmail/labels.py`` for safety invariants).
GOOGLE_OAUTH_SCOPES: list[str] = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Categories the classifier agent may assign.
CATEGORIES: list[str] = [
    "Work",
    "Personal",
    "Finance",
    "Promotions",
    "Newsletter",
    "Travel",
    "Receipts",
    "Notifications",
    "Other",
]

# Forbidden Gmail modify keys — guards against accidental destructive ops.
FORBIDDEN_MODIFY_KEYS: tuple[str, ...] = ("removeLabelIds", "trash", "delete")
