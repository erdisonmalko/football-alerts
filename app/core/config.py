from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/football_alerts"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/football_alerts"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Football Data API
    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "alerts@yourdomain.com"
    EMAIL_FROM_NAME: str = "Football Alerts"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
