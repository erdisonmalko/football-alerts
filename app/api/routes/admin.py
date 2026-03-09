"""
Internal/admin routes — protected by a simple API key header.
Useful for manual triggering from a cron job or during development.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.models import AlertType
from app.services.match_service import get_matches_due_for_alerts, sync_all_leagues

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")


@router.post("/sync-matches", dependencies=[Depends(verify_admin_key)])
async def trigger_sync(db: AsyncSession = Depends(get_db)):
    """Manually trigger a match sync from football-data.org."""
    results = await sync_all_leagues(db)
    await db.commit()
    return {"status": "ok", "synced": results}


@router.get("/upcoming-alerts", dependencies=[Depends(verify_admin_key)])
async def preview_alerts(db: AsyncSession = Depends(get_db)):
    """Preview which matches are in each alert window right now (dry run)."""
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
    return preview
