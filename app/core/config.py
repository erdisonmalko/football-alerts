from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str                        # required — no default
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"
    ADMIN_KEY: str                         # required — no default

    # Database
    DATABASE_URL: str                      # required — no default
    DATABASE_URL_SYNC: str                 # required — no default

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Football Data API
    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_FROM_NAME: str = "Football Alerts"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()