from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import AlertType, SubscriptionType


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)


# ── Subscription ──────────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    subscription_type: SubscriptionType
    external_id: str = Field(max_length=50)
    display_name: str = Field(max_length=255)


class SubscriptionOut(BaseModel):
    id: int
    subscription_type: SubscriptionType
    external_id: str
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Match ─────────────────────────────────────────────────────────────────────

class MatchOut(BaseModel):
    id: int
    external_id: int
    league_code: str
    league_name: str
    home_team_name: str
    away_team_name: str
    kickoff_utc: datetime
    matchday: Optional[int]
    status: str

    model_config = {"from_attributes": True}


class MatchOutWithSubscribed(MatchOut):
    """MatchOut extended with a flag showing if the current user is subscribed."""
    is_subscribed: bool = False


# ── Leagues & Teams (from football-data.org) ──────────────────────────────────

class LeagueOut(BaseModel):
    code: str
    name: str
    country: str
    emblem_url: Optional[str] = None


class TeamOut(BaseModel):
    id: int
    name: str
    short_name: Optional[str]
    crest_url: Optional[str] = None


# ── Alert Log ─────────────────────────────────────────────────────────────────

class AlertLogOut(BaseModel):
    id: int
    match_id: int
    alert_type: AlertType
    sent_at: datetime

    model_config = {"from_attributes": True}