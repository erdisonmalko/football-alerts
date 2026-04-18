from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.v1.services.challenge_service import validate_prediction
from app.v1.models.models import (
    AlertType,
    ChallengeEntryResult,
    ChallengeEntryStatus,
    ChallengeStatus,
    ServerRole,
    SubscriptionType,
    JoinRequestStatus,
)


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
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    model_config = {"from_attributes": True}


class MatchOutWithSubscribed(MatchOut):
    """MatchOut extended with a flag showing if the current user is subscribed."""

    is_subscribed: bool = False


class PaginatedMatches(BaseModel):
    items: list[MatchOutWithSubscribed]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserMatchesOut(BaseModel):
    live: list[MatchOut]
    upcoming: list[MatchOut]
    finished: list[MatchOut]


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


# ── Server ────────────────────────────────────────────────────────────────────


class ServerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    is_public: bool = True


class ServerUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    is_public: bool = True


class ServerMemberOut(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    role: ServerRole
    joined_at: datetime
    total_points: int
    total_wins: int
    total_losses: int
    total_draws: int
    challenge_count: int

    model_config = {"from_attributes": True}


class JoinRequestOut(BaseModel):
    id: int
    server_id: int
    user_id: int
    status: JoinRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ServerUpdateOut(BaseModel):
    id: int
    name: str
    is_public: bool
    invite_code: str

    model_config = {"from_attributes": True}


class ServerOut(BaseModel):
    id: int
    name: str
    invite_code: str
    created_by_id: int
    created_at: datetime
    # Populated when fetching a single server — omitted in list views
    members: list[ServerMemberOut] = []

    model_config = {"from_attributes": True}


class ServerListOut(BaseModel):
    """Lightweight version used when listing all servers a user belongs to."""

    id: int
    name: str
    invite_code: str
    member_count: int
    your_points: int  # caller's total_points in this server
    your_rank: int  # caller's rank by points in this server

    model_config = {"from_attributes": True}


# ── Challenge ─────────────────────────────────────────────────────────────────


class ChallengeCreate(BaseModel):
    match_id: int = Field(description="Internal match ID from our DB")
    stake: str = Field(
        min_length=1,
        max_length=255,
        examples=["50 pushups", "Buy me a beer"],
    )
    prediction: str = Field(
        min_length=1,
        max_length=100,
        examples=["Real Madrid 2-1"],
        description="Creator's own prediction — stored as their ChallengeEntry",
    )
    # If empty → all current server members are invited
    invited_user_ids: list[int] = Field(
        default=[],
        description="Subset of server members to invite. Empty means everyone.",
    )

    @field_validator("prediction")
    @classmethod
    def prediction_must_be_valid_score(cls, v: str) -> str:
        if not validate_prediction(v):
            raise ValueError("Prediction must be a valid score format e.g. '2-1'")
        return v.strip()


class ChallengeEntryOut(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: str = ""
    prediction: Optional[str]
    status: ChallengeEntryStatus
    points_earned: int
    result: Optional[ChallengeEntryResult]
    responded_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ChallengeOut(BaseModel):
    id: int
    server_id: int
    match_id: int
    created_by_id: int
    stake: str
    status: ChallengeStatus
    expires_at: datetime
    settled_at: Optional[datetime]
    created_at: datetime
    entries: list[ChallengeEntryOut] = []

    model_config = {"from_attributes": True}


class ChallengeWithMatch(ChallengeOut):
    """Used in list views — embeds match details so the UI doesn't need a second call."""

    match: MatchOut


class ChallengeAccept(BaseModel):
    prediction: str = Field(min_length=1, max_length=20)

    @field_validator("prediction")
    @classmethod
    def prediction_must_be_valid_score(cls, v: str) -> str:
        if not validate_prediction(v):
            raise ValueError("Prediction must be a valid score format e.g. '2-1'")
        return v.strip()


# ── Server leaderboard ────────────────────────────────────────────────────────


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    full_name: Optional[str]
    email: str
    total_points: int
    total_wins: int
    total_losses: int
    total_draws: int
    challenge_count: int

    model_config = {"from_attributes": True}


class ServerLeaderboard(BaseModel):
    server_id: int
    server_name: str
    entries: list[LeaderboardEntry]
