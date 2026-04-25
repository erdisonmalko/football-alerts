from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.v1.db.session import Base

import enum


# ── Enums ─────────────────────────────────────────────────────────────────────


class AlertType(str, enum.Enum):
    ONE_WEEK = "1_week"
    THREE_DAYS = "3_days"
    SIX_HOURS = "6_hours"


class SubscriptionType(str, enum.Enum):
    LEAGUE = "league"
    TEAM = "team"
    MATCH = "match"


# ── Server Enums ──────────────────────────────────────────────────────────────


class ServerRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ChallengeStatus(str, enum.Enum):
    OPEN = "open"  # waiting for responses, before kickoff
    LOCKED = "locked"  # kickoff passed, no more entries accepted
    SETTLED = "settled"  # match finished, results computed
    VOID = "void"  # match cancelled or postponed


class ChallengeEntryStatus(str, enum.Enum):
    PENDING = "pending"  # invited, not yet responded
    ACCEPTED = "accepted"  # placed their prediction
    DECLINED = "declined"  # passed on this one
    VOID = "void"  # voided with the parent challenge


class ChallengeEntryResult(str, enum.Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"  # tied on points with at least one other entry
    VOID = "void"


# ── User ──────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    google_token: Mapped[Optional["GoogleToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    alert_logs: Mapped[list["AlertLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── Subscription ──────────────────────────────────────────────────────────────


class Subscription(Base):
    """A user subscribing to alerts for a whole league, a specific team, or a one-off match."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "subscription_type", "external_id", name="uq_user_subscription"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    # ID from football-data.org (e.g. league code "PL", or team id 64)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")


# ── Match ─────────────────────────────────────────────────────────────────────


class Match(Base):
    """
    Cached match data from football-data.org.
    We store this locally so the scheduler can query without hitting the
    external API every time.
    """

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )

    # League info
    league_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    league_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Teams
    home_team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    home_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    away_team_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timing (always store in UTC)
    kickoff_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    matchday: Mapped[Optional[int]] = mapped_column(Integer)
    stage: Mapped[Optional[str]] = mapped_column(String(100))

    # Status: SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED, POSTPONED, CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")

    # Scores (populated once match is in play or finished)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    alert_logs: Mapped[list["AlertLog"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


# ── AlertLog ──────────────────────────────────────────────────────────────────


class AlertLog(Base):
    """
    Tracks which alerts have already been sent.
    Prevents duplicate emails if the scheduler runs multiple times.
    """

    __tablename__ = "alert_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "match_id", "alert_type", name="uq_user_match_alert"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="alert_logs")
    match: Mapped["Match"] = relationship(back_populates="alert_logs")


# ── GoogleToken ─────────────────────────────────────────────────────────────
class GoogleToken(Base):
    """
    Stores OAuth tokens for users who connect their Google Calendar.
    One row per user — updated on each token refresh.
    """

    __tablename__ = "google_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="google_token")


# ── CalendarEvent ─────────────────────────────────────────────────────────────


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    google_event_id: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Prevent duplicates (critical)
    __table_args__ = (
        UniqueConstraint("user_id", "match_id", name="uq_user_match_calendar"),
    )

    # Relationships (optional but clean)
    match = relationship("Match")
    user = relationship("User")


# ── Server ────────────────────────────────────────────────────────────────────
class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])
    members: Mapped[list["ServerMember"]] = relationship(
        back_populates="server", cascade="all, delete-orphan"
    )
    challenges: Mapped[list["Challenge"]] = relationship(
        back_populates="server", cascade="all, delete-orphan"
    )


# ServerJoinRequest


class JoinRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ServerJoinRequest(Base):
    """
    A request to join a private server.
    Created when a user clicks 'Request to Join' on a private server.
    Owner accepts or declines.
    """

    __tablename__ = "server_join_requests"
    __table_args__ = (
        UniqueConstraint("server_id", "user_id", name="uq_server_join_request"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        Enum(JoinRequestStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=JoinRequestStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    server: Mapped["Server"] = relationship()
    user: Mapped["User"] = relationship()


# ── ServerMember ──────────────────────────────────────────────────────────────


class ServerMember(Base):
    """
    Membership record linking a user to a server.
    Lifetime stats are denormalized here for fast leaderboard queries —
    updated after each challenge settles rather than aggregated on the fly.
    """

    __tablename__ = "server_members"
    __table_args__ = (
        UniqueConstraint("server_id", "user_id", name="uq_server_member"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ServerRole] = mapped_column(
        Enum(ServerRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ServerRole.MEMBER,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Denormalized lifetime stats within this server
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    challenge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    server: Mapped["Server"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


# ── Challenge ─────────────────────────────────────────────────────────────────


class Challenge(Base):
    """
    A prediction challenge created by one server member, broadcast to
    some or all other members. Each invited member gets a ChallengeEntry.
    The creator's own prediction also lives in a ChallengeEntry.
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stake: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(ChallengeStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ChallengeStatus.OPEN,
    )
    # Set to match kickoff — entries cannot be added or changed after this
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    settled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    server: Mapped["Server"] = relationship(back_populates="challenges")
    match: Mapped["Match"] = relationship()
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])
    entries: Mapped[list["ChallengeEntry"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


# ── ChallengeEntry ────────────────────────────────────────────────────────────


class ChallengeEntry(Base):
    """
    One row per invited participant per challenge.
    The challenge creator also gets an entry (auto-accepted with their prediction).
    Points and result are populated at settlement.

    Scoring:
        exact score match  → 3 points
        correct result only (win / draw / loss) → 1 point
        wrong result → 0 points
    """

    __tablename__ = "challenge_entries"
    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_challenge_entry"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Free-text prediction, e.g. "Real Madrid 2-1" — null if declined
    prediction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[ChallengeEntryStatus] = mapped_column(
        Enum(ChallengeEntryStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ChallengeEntryStatus.PENDING,
    )
    # Populated at settlement
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[ChallengeEntryResult]] = mapped_column(
        Enum(ChallengeEntryResult, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    challenge: Mapped["Challenge"] = relationship(back_populates="entries")
    user: Mapped["User"] = relationship()
