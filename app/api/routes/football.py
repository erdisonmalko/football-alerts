import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.logger import get_logger
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    LeagueOut,
    PaginatedMatches,
    MatchOutWithSubscribed,
    TeamOut,
)
from app.services.football_service import SUPPORTED_LEAGUES, football_client
from app.services.google_calendar_service import(
     get_user_token, 
     add_match_to_calendar, 
     remove_match_from_calendar
    )

from app.services.match_service import (
    get_upcoming_matches_for_browse,
    get_user_match_subscriptions,
    get_match_by_id,
    create_calendar_event,
    get_calendar_event,
)

router = APIRouter(prefix="/football", tags=["football"])

logger = get_logger(__name__)


@router.get("/leagues", response_model=list[LeagueOut])
async def list_leagues(_: User = Depends(get_current_user)):
    """Returns all leagues available for subscription."""
    return await football_client.get_leagues()


@router.get("/leagues/{league_code}/teams", response_model=list[TeamOut])
async def list_teams(
    league_code: str = Path(..., description="e.g. PL, SA, BL1"),
    _: User = Depends(get_current_user),
):
    """Returns all teams in a league."""
    valid_codes = {lg["code"] for lg in SUPPORTED_LEAGUES}
    if league_code.upper() not in valid_codes:
        raise HTTPException(
            status_code=404, detail=f"League '{league_code}' not supported"
        )

    return await football_client.get_teams_by_league(league_code.upper())


@router.get("/matches/upcoming", response_model=PaginatedMatches)
async def list_upcoming_matches(
    league_code: Optional[str] = Query(
        default=None, description="Filter by league code, e.g. PL"
    ),
    days: int = Query(
        default=14, ge=1, le=30, description="How many days ahead to look"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=5, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse upcoming matches with pagination.
    Returns items, total count, and pagination metadata.
    """
    if league_code:
        valid_codes = {lg["code"] for lg in SUPPORTED_LEAGUES}
        if league_code.upper() not in valid_codes:
            raise HTTPException(
                status_code=404, detail=f"League '{league_code}' not supported"
            )

    matches, total = await get_upcoming_matches_for_browse(
        db,
        days_ahead=days,
        league_code=league_code,
        page=page,
        page_size=page_size,
    )

    subscribed_ids = await get_user_match_subscriptions(db, current_user.id)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedMatches(
        items=[
            MatchOutWithSubscribed(
                **{c.key: getattr(m, c.key) for c in m.__table__.columns},
                is_subscribed=str(m.external_id) in subscribed_ids,
            )
            for m in matches
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

# ── Match Details Endpoint (for calendar sync) ─────────────────────────────
@router.post("/matches/calendar/add-match/{external_match_id}")
async def add_match_to_calendar_endpoint(
    external_match_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    token = await get_user_token(db, user.id)
    logger.debug(
        "User %s requested to add match %s to calendar. Token found: %s",
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
        "Match details for %s: %s vs %s at %s",
        external_match_id,
        match.home_team,
        match.away_team,
        match.kickoff_utc,
    )
    # ✅ Prevent duplicates
    existing = await get_calendar_event(db, user.id, match.id)
    if existing:
        logger.info(
            "Match %s already has a calendar event for user %s: %s",
            match.id,
            user.email,
            existing.google_event_id,
        )
        return {"event_id": existing.google_event_id}

    event_id = add_match_to_calendar(token, match)

    if not event_id:
        raise HTTPException(status_code=500, detail="FAILED_TO_CREATE_EVENT")

    # ✅ Persist mapping
    await create_calendar_event(
        db,
        user_id=user.id,
        match_id=match.id,
        event_id=event_id,
    )

    await db.commit()

    return {"event_id": event_id}

@router.delete("/matches/calendar/remove-match/{match_id}")
async def remove_match_from_calendar_endpoint(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    token = await get_user_token(db, user.id)

    # If no token → nothing to delete externally, but still OK
    # (user might have disconnected)
    
    event = await get_calendar_event(db, user.id, match_id)

    # Idempotent: nothing to delete
    if not event:
        return {"status": "ok"}

    if token:
        success = remove_match_from_calendar(token, event.google_event_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="FAILED_TO_DELETE_EVENT",
            )

    # Always remove local record
    await db.delete(event)
    await db.commit()

    return {"status": "deleted"}