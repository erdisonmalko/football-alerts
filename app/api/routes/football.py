from fastapi import APIRouter, Depends, HTTPException, Path

from app.core.security import get_current_user
from app.models.models import User
from app.schemas.schemas import LeagueOut, TeamOut
from app.services.football_service import SUPPORTED_LEAGUES, football_client

router = APIRouter(prefix="/football", tags=["football"])

from app.core.logger import _logger
logger = _logger()

@router.get("/leagues", response_model=list[LeagueOut])
async def list_leagues(_: User = Depends(get_current_user)):
    """Returns all leagues available for subscription."""
    logger.info("[app.api.routes.football.list_leagues] Fetching list of all leagues.")
    return await football_client.get_leagues()


@router.get("/leagues/{league_code}/teams", response_model=list[TeamOut])
async def list_teams(
    league_code: str = Path(..., description="e.g. PL, SA, BL1"),
    _: User = Depends(get_current_user),
):
    """Returns all teams in a league — use to subscribe to a specific team."""
    logger.info(f"[app.api.routes.football.list_teams] Fetching teams for league: {league_code}")

    valid_codes = {lg["code"] for lg in SUPPORTED_LEAGUES}
    if league_code.upper() not in valid_codes:
        logger.warning(f"[app.api.routes.football.list_teams] Attempt to fetch teams for unsupported league code: {league_code}")
        raise HTTPException(status_code=404, detail=f"League '{league_code}' not supported")

    teams = await football_client.get_teams_by_league(league_code.upper())
    logger.info(f"[app.api.routes.football.list_teams] Retrieved teams for league: {league_code}")
    return teams
