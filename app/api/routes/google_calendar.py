from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db

from app.services.google_calendar_service import (
    get_user_token,
    add_match_to_calendar,
    remove_match_from_calendar,
)

from app.services.match_service import (
    get_match_by_id,
    create_calendar_event,
    get_calendar_event,
)
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


# ── Match Details Endpoint (for calendar sync) ─────────────────────────────
@router.post("/matches/add-match/{external_match_id}")
async def add_match_to_calendar_endpoint(
    external_match_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    logger.info("HIT ADD MATCH ENDPOINT")
    token = await get_user_token(db, user.id)
    logger.debug(
        "[add_match_to_calendar_endpoint] User %s requested to add match %s to calendar. Token found: %s",
        user.email,
        external_match_id,
        bool(token),
    )
    if not token:
        raise HTTPException(status_code=400, detail="GOOGLE_NOT_CONNECTED")

    match = await get_match_by_id(db, external_match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    logger.debug(
        "[add_match_to_calendar_endpoint] Match details for %s: %s vs %s at %s",
        external_match_id,
        match.home_team_name,
        match.away_team_name,
        match.kickoff_utc,
    )
    # Prevent duplicates
    existing = await get_calendar_event(db, user.id, match.id)
    if existing:
        logger.info(
            "[add_match_to_calendar_endpoint] Match %s already has a calendar event for user %s: %s",
            match.id,
            user.email,
            existing.google_event_id,
        )
        return {"event_id": existing.google_event_id}

    event_id = add_match_to_calendar(token, match)

    if not event_id:
        raise HTTPException(status_code=500, detail="FAILED_TO_CREATE_EVENT")

    # Persist mapping
    await create_calendar_event(
        db,
        user_id=user.id,
        match_id=match.id,
        event_id=event_id,
    )

    await db.commit()

    return {"event_id": event_id}


@router.delete("/matches/remove-match/{external_match_id}")
async def remove_match_from_calendar_endpoint(
    external_match_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    token = await get_user_token(db, user.id)

    match = await get_match_by_id(db, external_match_id)
    if not match:
        return {"status": "ok"}

    event = await get_calendar_event(db, user.id, match.id)

    if not event:
        logger.info(
            "[remove_match_from_calendar_endpoint] No calendar event found for match %s and user %s. Nothing to delete.",
            external_match_id,
            user.email,
        )
        return {"status": "ok"}

    logger.debug(
        "[remove_match_from_calendar_endpoint] User %s removing match %s from calendar. Token found: %s",
        user.email,
        external_match_id,
        bool(token),
    )

    if token:
        success = remove_match_from_calendar(token, event.google_event_id)
        if not success:
            raise HTTPException(status_code=500, detail="FAILED_TO_DELETE_EVENT")

    await db.delete(event)
    await db.commit()
    logger.info(
        "[remove_match_from_calendar_endpoint] Successfully removed calendar event from Google and table for match %s and user %s",
        external_match_id,
        user.email,
    )
    return {"status": "deleted"}
