# server/app/settings.py
# Centralized application settings (env-driven via pydantic BaseSettings)

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Tweight API"
    ENV: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Admin
    ADMIN_TOKEN: str | None = None  # set via env: ADMIN_TOKEN="supersecret"

    # Language
    MESSAGES_PATH: str = "config/messages.json"
    DEFAULT_LANG: str = "DE"
    # Note: a 'set[str]' default is fine in pydantic
    ALLOWED_LANGS: set[str] = {"DE", "EN"}
    LANGUAGE_CONTEXT: str = "GLOBAL.CSV"

    # Config files
    QUERIES_PATH: str = "config/queries.json"
    CSV_CONFIGS_PATH: str = "config/csv_configs.json"

    # SQLite demo database path (re-used from your examples)
    SQLITE_DB_PATH: str = "test.db"

    class Config:
        env_file = ".env"
        case_sensitive = True