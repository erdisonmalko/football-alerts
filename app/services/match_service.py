from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AlertLog, AlertType, Match, Subscription, SubscriptionType
from app.services.football_service import football_client, SUPPORTED_LEAGUES


# ── Match Sync ────────────────────────────────────────────────────────────────

async def sync_league_matches(db: AsyncSession, league_code: str) -> int:
    """
    Fetches upcoming matches from football-data.org for a league,
    upserts them into the local matches table.
    Returns the number of matches upserted.
    """
    raw_matches = await football_client.get_upcoming_matches(league_code)
    count = 0

    for m in raw_matches:
        existing = await db.execute(
            select(Match).where(Match.external_id == m["external_id"])
        )
        match = existing.scalar_one_or_none()
        kickoff = datetime.fromisoformat(m["kickoff_utc"].replace("Z", "+00:00"))

        if match:
            # Update mutable fields in case of reschedule
            match.kickoff_utc = kickoff
            match.status = m["status"]
        else:
            match = Match(
                external_id=m["external_id"],
                league_code=m["league_code"],
                league_name=m["league_name"],
                home_team_id=m["home_team_id"],
                home_team_name=m["home_team_name"],
                away_team_id=m["away_team_id"],
                away_team_name=m["away_team_name"],
                kickoff_utc=kickoff,
                matchday=m["matchday"],
                stage=m["stage"],
                status=m["status"],
            )
            db.add(match)
            count += 1

    await db.flush()
    return count


async def sync_all_leagues(db: AsyncSession) -> dict[str, int]:
    """Sync matches for every supported league. Returns {league_code: count}."""
    results = {}
    for league in SUPPORTED_LEAGUES:
        code = league["code"]
        try:
            count = await sync_league_matches(db, code)
            results[code] = count
        except Exception as exc:
            results[code] = -1  # mark failure but don't abort others
    return results


# ── Alert Eligibility ─────────────────────────────────────────────────────────

ALERT_WINDOWS: dict[AlertType, tuple[timedelta, timedelta]] = {
    # (min time until kickoff, max time until kickoff)
    AlertType.ONE_WEEK:    (timedelta(days=6, hours=23), timedelta(days=7, hours=1)),
    AlertType.THREE_DAYS:  (timedelta(days=2, hours=23), timedelta(days=3, hours=1)),
    AlertType.SIX_HOURS:   (timedelta(hours=5, minutes=30), timedelta(hours=6, minutes=30)),
}


async def get_matches_due_for_alerts(
    db: AsyncSession,
    alert_type: AlertType,
) -> list[Match]:
    """
    Returns matches whose kickoff falls within the alert window for the given
    alert_type AND have not already been alerted for this type.
    """
    now = datetime.now(timezone.utc)
    min_delta, max_delta = ALERT_WINDOWS[alert_type]
    window_start = now + min_delta
    window_end   = now + max_delta

    # Matches inside the time window that are still scheduled
    result = await db.execute(
        select(Match).where(
            Match.kickoff_utc >= window_start,
            Match.kickoff_utc <= window_end,
            Match.status == "SCHEDULED",
        )
    )
    return list(result.scalars().all())


async def get_subscribed_user_ids_for_match(
    db: AsyncSession, match: Match
) -> list[int]:
    """
    Returns all user IDs that have a subscription matching this match
    (either by league or by one of the two teams).
    """
    result = await db.execute(
        select(Subscription.user_id).where(
            (
                (Subscription.subscription_type == SubscriptionType.LEAGUE) &
                (Subscription.external_id == match.league_code)
            ) | (
                (Subscription.subscription_type == SubscriptionType.TEAM) &
                (Subscription.external_id.in_([
                    str(match.home_team_id), str(match.away_team_id)
                ]))
            )
        ).distinct()
    )
    return list(result.scalars().all())


async def has_alert_been_sent(
    db: AsyncSession, user_id: int, match_id: int, alert_type: AlertType
) -> bool:
    result = await db.execute(
        select(AlertLog).where(
            AlertLog.user_id == user_id,
            AlertLog.match_id == match_id,
            AlertLog.alert_type == alert_type,
        )
    )
    return result.scalar_one_or_none() is not None


async def record_alert_sent(
    db: AsyncSession, user_id: int, match_id: int, alert_type: AlertType
) -> None:
    log = AlertLog(user_id=user_id, match_id=match_id, alert_type=alert_type)
    db.add(log)
    await db.flush()
