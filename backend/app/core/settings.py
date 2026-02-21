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

    model_config = SettingsConfigDict(env_file=".env")


s = Settings()
