"""
Internal/admin routes — protected by a simple API key header.
Useful for manual triggering from a cron job or during development.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.core.config import settings
from app.v1.db.session import get_db
from app.v1.models.models import AlertType
from app.v1.services.match_service import (
    get_matches_due_for_alerts, 
    sync_all_leagues,
    update_live_and_recent_matches
    )
from app.v1.services.challenge_service import (
    find_challenges_to_settle,
    lock_expired_challenges,
    settle_challenge,
    find_challenges_to_void,
    void_challenge,
)

from app.v1.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(...)):
    logger.debug(
        f"Received header: '{x_admin_key[:10]}...', Expected: '{settings.ADMIN_KEY}'"
    )
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key"
        )
    logger.info("Admin key verified.")


@router.post("/sync-matches", dependencies=[Depends(verify_admin_key)])
async def trigger_sync(db: AsyncSession = Depends(get_db)):
    """Manually trigger a match sync from football-data.org."""
    logger.info("Admin-triggered match sync started.")
    results = await sync_all_leagues(db)
    await db.commit()
    logger.info(f"Match sync completed. {len(results)} leagues synced.")
    return {"status": "ok", "synced": results}


@router.post("/dispatch-alerts", dependencies=[Depends(verify_admin_key)])
async def trigger_dispatch():
    """Manually trigger alert dispatch for all windows."""
    from app.v1.tasks.alert_tasks import dispatch_alerts_task

    dispatch_alerts_task.delay()
    return {"status": "ok", "message": "Alert dispatch queued"}


@router.post("/update-match-statuses", dependencies=[Depends(verify_admin_key)])
async def trigger_update_statuses(db: AsyncSession = Depends(get_db)):
    """Manually trigger live match status and score update."""
    logger.info("Admin-triggered match status update started.")
    results = await update_live_and_recent_matches()
    logger.info(f"Match status update completed. {len(results)} matches updated.")
    await db.commit()
    return {"status": "ok", "message": results}


@router.post("/sync-calendars", dependencies=[Depends(verify_admin_key)])
async def trigger_sync_calendars():
    """Manually trigger Google Calendar sync for all connected users."""
    from app.v1.tasks.alert_tasks import sync_calendar_task

    sync_calendar_task.delay()
    return {"status": "ok", "message": "Calendar sync queued"}


@router.get("/upcoming-alerts", dependencies=[Depends(verify_admin_key)])
async def preview_alerts(db: AsyncSession = Depends(get_db)):
    """Preview which matches are in each alert window right now (dry run)."""
    logger.info("Admin requested alert preview.")
    preview = {}
    for alert_type in AlertType:
        matches = await get_matches_due_for_alerts(db, alert_type)
        preview[alert_type.value] = [
            {
                "match_id": m.id,
                "fixture": f"{m.home_team_name} vs {m.away_team_name}",
                "league": m.league_name,
                "kickoff_utc": m.kickoff_utc.isoformat(),
            }
            for m in matches
        ]
        logger.debug(f"Alert window {alert_type.value}: {len(matches)} matches found.")
    return preview


@router.post("/settle-challenges", dependencies=[Depends(verify_admin_key)])
async def trigger_settle_challenges(db: AsyncSession = Depends(get_db)):
    """Manually trigger challenge settlement for expired challenges."""
    logger.info("Admin-triggered challenge settlement started.")
    locked = await lock_expired_challenges(db)
    if locked:
        logger.info("Locked %s expired challenges", locked)

    challenges = await find_challenges_to_settle(db)
    logger.info("%s challenges ready to settle", len(challenges))

    for challenge in challenges:
        try:
            await settle_challenge(db, challenge)
        except Exception:
            logger.exception(
                "Failed settling challenge %s",
                challenge.id,
            )

    await db.commit()
    logger.info(
        "Challenge settlement completed. Settled: %s, Locked: %s",
        len(challenges),
        locked,
    )
    return {"status": "ok", "settled": len(challenges), "locked": locked}


@router.post("/void-postponed-challenges", dependencies=[Depends(verify_admin_key)])
async def trigger_void_postponed_challenges(db: AsyncSession = Depends(get_db)):
    """Manually trigger voiding of challenges for postponed/cancelled matches."""
    logger.info("Admin-triggered void postponed challenges started.")
    challenges = await find_challenges_to_void(db)
    logger.info("%s challenges to void", len(challenges))

    for challenge in challenges:
        try:
            await void_challenge(db, challenge)
        except Exception:
            logger.exception(
                "Failed voiding challenge %s",
                challenge.id,
            )

    await db.commit()
    logger.info("Void postponed challenges completed. Voided: %s", len(challenges))
    return {"status": "ok", "voided": len(challenges)}
