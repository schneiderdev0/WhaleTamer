from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# .env params.
class Settings(BaseSettings):
    port: int = 8000
    reload: bool = False

    postgres_host: str = "127.0.0.1"
    postgres_db: str = "dev_db"
    postgres_user: str = "root"
    postgres_password: str = "qwerty"
    postgres_port: int = 5432

    jwt_secret_key: str = "SECRET_KEY"

    gemini_api_key: str = "GEMINI_API_KEY"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = ""

    # Frontend base URL for OAuth redirects (e.g. http://localhost:5173)
    frontend_base_url: str = ""

    # CORS
    backend_cors_origins: List[str] = []

    model_config = SettingsConfigDict(env_file=".env")


s = Settings()
