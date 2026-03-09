from fastapi import APIRouter, Depends, HTTPException, Path

from app.core.security import get_current_user
from app.models.models import User
from app.schemas.schemas import LeagueOut, TeamOut
from app.services.football_service import SUPPORTED_LEAGUES, football_client

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
    """Returns all teams in a league — use to subscribe to a specific team."""
    valid_codes = {lg["code"] for lg in SUPPORTED_LEAGUES}
    if league_code.upper() not in valid_codes:
        raise HTTPException(status_code=404, detail=f"League '{league_code}' not supported")

    teams = await football_client.get_teams_by_league(league_code.upper())
    return teams
