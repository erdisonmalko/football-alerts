from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import LeagueOut, MatchOutWithSubscribed, TeamOut
from app.services.football_service import SUPPORTED_LEAGUES, football_client
from app.services.match_service import (
    get_upcoming_matches_for_browse,
    get_user_match_subscriptions,
)

router = APIRouter(prefix="/football", tags=["football"])


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
        raise HTTPException(status_code=404, detail=f"League '{league_code}' not supported")

    return await football_client.get_teams_by_league(league_code.upper())


@router.get("/matches/upcoming", response_model=list[MatchOutWithSubscribed])
async def list_upcoming_matches(
    league_code: Optional[str] = Query(default=None, description="Filter by league code, e.g. PL"),
    days: int = Query(default=14, ge=1, le=30, description="How many days ahead to look"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse upcoming matches. Each match includes an is_subscribed flag
    so the UI can show whether the user already has an alert set for it.
    """
    if league_code:
        valid_codes = {lg["code"] for lg in SUPPORTED_LEAGUES}
        if league_code.upper() not in valid_codes:
            raise HTTPException(status_code=404, detail=f"League '{league_code}' not supported")

    matches = await get_upcoming_matches_for_browse(db, days_ahead=days, league_code=league_code)

    # Get all match external_ids the user is directly subscribed to
    subscribed_ids = await get_user_match_subscriptions(db, current_user.id)

    return [
        MatchOutWithSubscribed(
            **{c.key: getattr(m, c.key) for c in m.__table__.columns},
            is_subscribed=str(m.external_id) in subscribed_ids,
        )
        for m in matches
    ]