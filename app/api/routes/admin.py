"""
Internal/admin routes — protected by a simple API key header.
Useful for manual triggering from a cron job or during development.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.db.session import get_db
from app.models.models import AlertType
from app.services.match_service import get_matches_due_for_alerts, sync_all_leagues

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")
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
    from app.tasks.alert_tasks import dispatch_alerts_task
    dispatch_alerts_task.delay()
    return {"status": "ok", "message": "Alert dispatch queued"}


@router.post("/update-match-statuses", dependencies=[Depends(verify_admin_key)])
async def trigger_update_statuses():
    """Manually trigger live match status and score update."""
    from app.tasks.alert_tasks import update_match_statuses_task
    update_match_statuses_task.delay()
    return {"status": "ok", "message": "Match status update queued"}


@router.post("/sync-calendars", dependencies=[Depends(verify_admin_key)])
async def trigger_sync_calendars():
    """Manually trigger Google Calendar sync for all connected users."""
    from app.tasks.alert_tasks import sync_calendar_task
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