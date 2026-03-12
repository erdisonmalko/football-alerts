"""
Client for https://www.football-data.org (free tier).

Supported leagues on the free tier:
  PL  - Premier League (England)
  PD  - La Liga (Spain)
  SA  - Serie A (Italy)
  BL1 - Bundesliga (Germany)
  FL1 - Ligue 1 (France)
  CL  - UEFA Champions League
  EL  - UEFA Europa League
  EC  - European Championship
  WC  - FIFA World Cup
  PPL - Primeira Liga (Portugal)
  DED - Eredivisie (Netherlands)
  BSA - Brasileirão (Brazil)
"""

from datetime import date, timedelta
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

from app.core.logger import _logger
logger = _logger()


# Human-readable metadata for the leagues we expose in the UI
SUPPORTED_LEAGUES: list[dict] = [
    {"code": "PL",  "name": "Premier League",       "country": "England"},
    {"code": "PD",  "name": "La Liga",               "country": "Spain"},
    {"code": "SA",  "name": "Serie A",               "country": "Italy"},
    {"code": "BL1", "name": "Bundesliga",            "country": "Germany"},
    {"code": "FL1", "name": "Ligue 1",               "country": "France"},
    {"code": "CL",  "name": "Champions League",      "country": "Europe"},
    {"code": "EL",  "name": "Europa League",         "country": "Europe"},
    {"code": "PPL", "name": "Primeira Liga",         "country": "Portugal"},
    {"code": "DED", "name": "Eredivisie",            "country": "Netherlands"},
]


class FootballDataClient:
    def __init__(self):
        self.base_url = settings.FOOTBALL_DATA_BASE_URL
        self.headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        logger.debug(f"[FootballDataClient._get] Making API call to {path} with params {params}")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_leagues(self) -> list[dict]:
        """Return hardcoded supported league metadata (no API call needed)."""
        logger.debug("Fetching supported leagues.")
        return SUPPORTED_LEAGUES

    async def get_teams_by_league(self, league_code: str) -> list[dict]:
        """Fetch all teams in a given league for the current season."""
        logger.debug(f"[FootballDataClient.get_teams_by_league] Fetching teams for league: {league_code}")
        data = await self._get(f"/competitions/{league_code}/teams")
        logger.debug(f"[FootballDataClient.get_teams_by_league] Received {len(data.get('teams', []))} teams for league {league_code}")
        return [
            {
                "id": team["id"],
                "name": team["name"],
                "short_name": team.get("shortName"),
                "crest_url": team.get("crest"),
            }
            for team in data.get("teams", [])
        ]

    async def get_upcoming_matches(
        self,
        league_code: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[dict]:
        """
        Fetch upcoming scheduled matches for a league.
        Default window: today → +14 days.
        """
        date_from = date_from or date.today()
        date_to = date_to or (date_from + timedelta(days=14))

        data = await self._get(
            f"/competitions/{league_code}/matches",
            params={
                "dateFrom": date_from.isoformat(),
                "dateTo": date_to.isoformat(),
                "status": "SCHEDULED",
            },
        )
        logger.debug(f"[FootballDataClient.get_upcoming_matches] Received {len(data.get('matches', []))} matches for league {league_code} between {date_from} and {date_to}")
        return self._normalize_matches(data.get("matches", []), league_code)

    async def get_upcoming_matches_by_team(
        self,
        team_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[dict]:
        """Fetch upcoming matches for a specific team."""
        date_from = date_from or date.today()
        date_to = date_to or (date_from + timedelta(days=14))

        data = await self._get(
            f"/teams/{team_id}/matches",
            params={
                "dateFrom": date_from.isoformat(),
                "dateTo": date_to.isoformat(),
                "status": "SCHEDULED",
            },
        )
        logger.debug(f"[FootballDataClient.get_upcoming_matches_by_team] Received {len(data.get('matches', []))} matches for team {team_id} between {date_from} and {date_to}")
        return self._normalize_matches(data.get("matches", []))

    def _normalize_matches(self, raw: list[dict], league_code: str = "") -> list[dict]:
        """Flatten the API response into a consistent internal shape."""
        normalized = []
        for m in raw:
            competition = m.get("competition", {})
            normalized.append(
                {
                    "external_id": m["id"],
                    "league_code": competition.get("code", league_code),
                    "league_name": competition.get("name", ""),
                    "home_team_id": m["homeTeam"]["id"],
                    "home_team_name": m["homeTeam"]["name"],
                    "away_team_id": m["awayTeam"]["id"],
                    "away_team_name": m["awayTeam"]["name"],
                    "kickoff_utc": m["utcDate"],  # ISO 8601 string
                    "matchday": m.get("matchday"),
                    "stage": m.get("stage"),
                    "status": m.get("status", "SCHEDULED"),
                }
            )
        logger.debug(f"[FootballDataClient._normalize_matches] Normalized {len(normalized)} matches for league {league_code}")
        return normalized


# Singleton — import and use this everywhere
football_client = FootballDataClient()
