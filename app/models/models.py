from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer,
    String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

import enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class AlertType(str, enum.Enum):
    ONE_WEEK  = "1_week"
    THREE_DAYS = "3_days"
    SIX_HOURS  = "6_hours"


class SubscriptionType(str, enum.Enum):
    LEAGUE = "league"
    TEAM   = "team"
    MATCH  = "match"


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
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
    alert_logs: Mapped[list["AlertLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── Subscription ──────────────────────────────────────────────────────────────

class Subscription(Base):
    """A user subscribing to alerts for a whole league, a specific team, or a one-off match."""
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "subscription_type", "external_id", name="uq_user_subscription"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType, values_callable=lambda x: [e.value for e in x]), nullable=False
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
    external_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    # League info
    league_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    league_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Teams
    home_team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    home_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    away_team_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timing (always store in UTC)
    kickoff_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    matchday: Mapped[Optional[int]] = mapped_column(Integer)
    stage: Mapped[Optional[str]] = mapped_column(String(100))

    # Status: SCHEDULED, LIVE, FINISHED, POSTPONED, CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")

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
        UniqueConstraint("user_id", "match_id", "alert_type", name="uq_user_match_alert"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="alert_logs")
    match: Mapped["Match"] = relationship(back_populates="alert_logs")