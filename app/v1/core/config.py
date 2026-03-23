from pydantic_settings import BaseSettings, SettingsConfigDict


# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "update-me-on-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"
    ADMIN_KEY: str = "update-me"

    # Separate local and prod URLs — never mixed up
    LOCAL_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/football_alerts"
    )
    LOCAL_DATABASE_URL_SYNC: str = (
        "postgresql://postgres:password@localhost:5432/football_alerts"
    )
    PROD_DATABASE_URL: str = ""
    PROD_DATABASE_URL_SYNC: str = ""

    # Docker internal URL — used by the app containers (api, worker, beat)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/football_alerts"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@db:5432/football_alerts"

    REDIS_URL: str = "redis://redis:6379/0"
    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_FROM_NAME: str = "Football Alerts"
    FRONTEND_URL: str = "http://localhost:5173"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
