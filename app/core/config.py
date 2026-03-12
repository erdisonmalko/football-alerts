import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL")

    # Football Data API
    FOOTBALL_DATA_API_KEY: str = os.getenv("FOOTBALL_DATA_API_KEY")
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "alerts@yourdomain.com"
    EMAIL_FROM_NAME: str = "Football Alerts"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


settings = Settings()
