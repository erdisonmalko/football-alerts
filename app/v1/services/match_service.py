from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.core.logger import get_logger
from app.v1.models.models import (
    AlertLog,
    AlertType,
    Match,
    Subscription,
    SubscriptionType,
)
from app.v1.services.football_service import football_client, SUPPORTED_LEAGUES

logger = get_logger(__name__)


# ── Match Sync ────────────────────────────────────────────────────────────────


async def sync_league_matches(db: AsyncSession, league_code: str) -> int:
    raw_matches = await football_client.get_upcoming_matches(league_code)
    count = 0

    for m in raw_matches:
        existing = await db.execute(
            select(Match).where(Match.external_id == m["external_id"])
        )
        match = existing.scalar_one_or_none()
        kickoff = datetime.fromisoformat(m["kickoff_utc"].replace("Z", "+00:00"))

        if match:
            match.kickoff_utc = kickoff
            match.status = m["status"]
            match.home_score = m.get("home_score")
            match.away_score = m.get("away_score")
            match.synced_at = datetime.now(timezone.utc)
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
    results = {}
    for league in SUPPORTED_LEAGUES:
        code = league["code"]
        try:
            count = await sync_league_matches(db, code)
            results[code] = count
        except Exception as exc:
            logger.error(f"Failed to sync league {code}: {exc}")
            results[code] = -1
    return results


# ── Browse Upcoming Matches ───────────────────────────────────────────────────


async def get_upcoming_matches_for_browse(
    db: AsyncSession,
    days_ahead: int = 14,
    league_code: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Match], int]:
    """
    Returns a page of upcoming scheduled matches for the browse UI.
    Returns (matches, total_count).
    """
    from sqlalchemy import func as sqlfunc

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=days_ahead)

    filters = [
        Match.kickoff_utc >= now,
        Match.kickoff_utc <= window_end,
        Match.status.in_(["SCHEDULED", "TIMED"]),
    ]
    if league_code:
        filters.append(Match.league_code == league_code.upper())

    # Total count
    count_result = await db.execute(
        select(sqlfunc.count()).select_from(Match).where(*filters)
    )
    total = count_result.scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Match)
        .where(*filters)
        .order_by(Match.kickoff_utc)
        .offset(offset)
        .limit(page_size)
    )
    matches = list(result.scalars().all())
    logger.debug(
        f"Browse: page {page}/{-(-total // page_size)}, {len(matches)} matches (league={league_code})"
    )
    return matches, total


async def get_user_match_subscriptions(db: AsyncSession, user_id: int) -> set[str]:
    """
    Returns the set of external_ids the user has MATCH subscriptions for.
    Used by the browse endpoint to mark already-subscribed matches.
    """
    result = await db.execute(
        select(Subscription.external_id).where(
            Subscription.user_id == user_id,
            Subscription.subscription_type == SubscriptionType.MATCH,
        )
    )
    return set(result.scalars().all())


async def update_live_and_recent_matches(db: AsyncSession) -> dict[str, int]:
    """
    Fetches today's matches for all leagues and updates status + scores
    for any match already in the DB. Runs every 15 minutes.
    """
    results = {}
    for league in SUPPORTED_LEAGUES:
        code = league["code"]
        try:
            todays_matches = await football_client.get_todays_matches(code)
            updated = 0
            for m in todays_matches:
                existing = await db.execute(
                    select(Match).where(Match.external_id == m["external_id"])
                )
                match = existing.scalar_one_or_none()
                if match:
                    match.status = m["status"]
                    match.home_score = m.get("home_score")
                    match.away_score = m.get("away_score")
                    updated += 1
            results[code] = updated
        except Exception as exc:
            logger.error(f"Failed to update live matches for {code}: {exc}")
            results[code] = -1

        # await asyncio.sleep(1)  # stay under 10 req/min free tier limit
    return results


async def get_matches_for_user(
    db: AsyncSession, user_id: int
) -> dict[str, list[Match]]:
    """
    Returns matches relevant to the user based on their subscriptions.
    Grouped into live, upcoming (next 14 days), and finished (today).
    """
    from app.v1.models.models import Subscription, SubscriptionType

    subs_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subs = subs_result.scalars().all()

    league_codes = [
        s.external_id for s in subs if s.subscription_type == SubscriptionType.LEAGUE
    ]
    team_ids = [
        int(s.external_id) for s in subs if s.subscription_type == SubscriptionType.TEAM
    ]
    match_ids = [
        int(s.external_id)
        for s in subs
        if s.subscription_type == SubscriptionType.MATCH
    ]

    if not league_codes and not team_ids and not match_ids:
        return {"live": [], "upcoming": [], "finished": []}

    from sqlalchemy import or_

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    filters = []
    if league_codes:
        filters.append(Match.league_code.in_(league_codes))
    if team_ids:
        filters.append(Match.home_team_id.in_(team_ids))
        filters.append(Match.away_team_id.in_(team_ids))
    if match_ids:
        filters.append(Match.external_id.in_(match_ids))

    result = await db.execute(
        select(Match)
        .where(
            or_(*filters),
            Match.kickoff_utc >= today_start,
            Match.kickoff_utc <= now + timedelta(days=14),
        )
        .order_by(Match.kickoff_utc)
    )
    all_matches = result.scalars().all()

    live, upcoming, finished = [], [], []
    for m in all_matches:
        if m.status in ("IN_PLAY", "PAUSED"):
            live.append(m)
        elif m.status in ("FINISHED", "AWARDED"):
            finished.append(m)
        elif m.status in ("SCHEDULED", "TIMED"):
            upcoming.append(m)

    logger.debug(
        f"User {user_id} matches: {len(live)} live, {len(upcoming)} upcoming, {len(finished)} finished"
    )

    return {"live": live, "upcoming": upcoming, "finished": finished}


# Helper to get match details by external_id (used by calendar sync)
async def get_match_by_id(db: AsyncSession, external_id: int) -> Optional[Match]:
    result = await db.execute(select(Match).where(Match.external_id == external_id))
    return result.scalar_one_or_none()


# ── Cleanup ───────────────────────────────────────────────────────────────────


async def cleanup_past_match_subscriptions(db: AsyncSession) -> int:
    """
    Deletes MATCH-type subscriptions where the linked match has already
    kicked off. Called by the sync task so stale subscriptions never accumulate.
    Returns the number of deleted rows.
    """
    now = datetime.now(timezone.utc)

    # Find external_ids of matches that have already kicked off
    past_matches_result = await db.execute(
        select(Match.external_id).where(Match.kickoff_utc < now)
    )
    past_external_ids = [str(eid) for eid in past_matches_result.scalars().all()]

    if not past_external_ids:
        return 0

    result = await db.execute(
        delete(Subscription)
        .where(
            Subscription.subscription_type == SubscriptionType.MATCH,
            Subscription.external_id.in_(past_external_ids),
        )
        .returning(Subscription.id)
    )
    deleted = len(result.scalars().all())
    if deleted:
        logger.info(f"Cleaned up {deleted} past match subscription(s)")
    return deleted


# ── Alert Eligibility ─────────────────────────────────────────────────────────

ALERT_WINDOWS: dict[AlertType, tuple[timedelta, timedelta]] = {
    AlertType.ONE_WEEK: (timedelta(days=6, hours=23), timedelta(days=7, hours=1)),
    AlertType.THREE_DAYS: (timedelta(days=2, hours=23), timedelta(days=3, hours=1)),
    AlertType.SIX_HOURS: (
        timedelta(hours=5, minutes=30),
        timedelta(hours=6, minutes=30),
    ),
}


async def get_matches_due_for_alerts(
    db: AsyncSession,
    alert_type: AlertType,
) -> list[Match]:
    now = datetime.now(timezone.utc)
    min_delta, max_delta = ALERT_WINDOWS[alert_type]
    window_start = now + min_delta
    window_end = now + max_delta

    result = await db.execute(
        select(Match).where(
            Match.kickoff_utc >= window_start,
            Match.kickoff_utc <= window_end,
            Match.status.in_(["SCHEDULED", "TIMED"]),
        )
    )
    matches = list(result.scalars().all())
    logger.info(
        f"Found {len(matches)} matches in alert window for {alert_type.value} alerts."
    )
    return matches


async def get_subscribed_user_ids_for_match(
    db: AsyncSession, match: Match
) -> list[int]:
    """
    Returns all user IDs that should receive an alert for this match.
    Covers three subscription types:
      - LEAGUE: user subscribed to the league this match belongs to
      - TEAM:   user subscribed to either the home or away team
      - MATCH:  user subscribed directly to this specific match
    """
    result = await db.execute(
        select(Subscription.user_id)
        .where(
            (
                (Subscription.subscription_type == SubscriptionType.LEAGUE)
                & (Subscription.external_id == match.league_code)
            )
            | (
                (Subscription.subscription_type == SubscriptionType.TEAM)
                & (
                    Subscription.external_id.in_(
                        [str(match.home_team_id), str(match.away_team_id)]
                    )
                )
            )
            | (
                (Subscription.subscription_type == SubscriptionType.MATCH)
                & (Subscription.external_id == str(match.external_id))
            )
        )
        .distinct()
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
