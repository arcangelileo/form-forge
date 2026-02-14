from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FormForge"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./formforge.db"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Email (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@formforge.dev"
    smtp_use_tls: bool = True

    # Rate limiting
    submissions_per_minute: int = 10

    # Base URL for generating form endpoint URLs
    base_url: str = "http://localhost:8000"

    model_config = {"env_prefix": "FORMFORGE_", "env_file": ".env"}


settings = Settings()
