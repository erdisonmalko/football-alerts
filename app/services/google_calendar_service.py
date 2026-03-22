"""
Google Calendar integration service.

Handles OAuth token management and calendar event creation/deletion.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import CalendarEvent, GoogleToken, Match, User

from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


# SCOPES = ["https://www.googleapis.com/auth/calendar"]
# less privileged scope that only allows managing events, not full calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CALENDAR_ID = "primary"


def get_oauth_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


def get_authorization_url() -> tuple[str, str]:
    """Returns (authorization_url, state) for the OAuth redirect."""
    flow = get_oauth_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url, state


def exchange_code_for_tokens(code: str) -> dict:
    """Exchanges the authorization code for access + refresh tokens."""
    flow = get_oauth_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_expiry": creds.expiry,
    }


def _build_credentials(token: GoogleToken) -> Credentials:
    return Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )


def _refresh_if_needed(creds: Credentials) -> Credentials:
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


async def get_user_token(db: AsyncSession, user_id: int) -> Optional[GoogleToken]:
    result = await db.execute(select(GoogleToken).where(GoogleToken.user_id == user_id))
    return result.scalar_one_or_none()


async def save_user_token(
    db: AsyncSession,
    user_id: int,
    access_token: str,
    refresh_token: str,
    token_expiry: datetime,
) -> GoogleToken:
    existing = await get_user_token(db, user_id)
    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expiry = token_expiry
        token = existing
    else:
        token = GoogleToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
        )
        db.add(token)
    await db.flush()
    return token


async def delete_user_token(db: AsyncSession, user_id: int) -> None:
    token = await get_user_token(db, user_id)
    if token:
        await db.delete(token)
        await db.flush()


def _match_to_event(match: Match) -> dict:
    """Converts a Match object to a Google Calendar event dict."""
    kickoff = match.kickoff_utc
    end_time = kickoff + timedelta(hours=2)
    title = f"⚽ {match.home_team_name} vs {match.away_team_name}"
    description = (
        f"{match.league_name}\nKickoff: {kickoff.strftime('%A, %d %B %Y at %H:%M UTC')}"
    )
    if match.matchday:
        description += f"\nMatchday {match.matchday}"

    return {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": kickoff.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 15},
            ],
        },
        "extendedProperties": {
            "private": {
                "footballAlerts": "true",
                "matchExternalId": str(match.external_id),
            }
        },
    }


def add_match_to_calendar(token: GoogleToken, match: Match) -> Optional[str]:
    """
    Adds a match event to the user's Google Calendar.
    Returns the Google Calendar event ID on success, None on failure.
    """
    try:
        creds = _build_credentials(token)
        creds = _refresh_if_needed(creds)
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        event = (
            service.events()
            .insert(
                calendarId=CALENDAR_ID,
                body=_match_to_event(match),
            )
            .execute()
        )
        logger.info(
            "Added calendar event for match %s user %s event_id=%s",
            match.external_id,
            token.user_id,
            event.get("id"),
        )
        return event.get("id")
    except Exception as exc:
        logger.error(
            "Failed to add calendar event for match %s user %s: %s",
            match.external_id,
            token.user_id,
            exc,
        )
        return None


def remove_match_from_calendar(token: GoogleToken, event_id: str) -> bool:
    """
    Deletes an event from Google Calendar.
    Returns True if deleted or already gone, False on failure.
    """
    try:
        creds = _build_credentials(token)
        creds = _refresh_if_needed(creds)

        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        service.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event_id,
        ).execute()

        logger.info(
            "Deleted calendar event %s for user %s",
            event_id,
            token.user_id,
        )

        return True

    except Exception as exc:
        # Important: handle "already deleted" case gracefully
        if "Not Found" in str(exc):
            logger.warning(
                "Event %s already deleted for user %s",
                event_id,
                token.user_id,
            )
            return True

        logger.error(
            "Failed to delete event %s for user %s: %s",
            event_id,
            token.user_id,
            exc,
        )
        return False


async def get_calendar_event(db: AsyncSession, user_id: int, match_id: int):
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == user_id,
            CalendarEvent.match_id == match_id,
        )
    )
    event = result.scalar_one_or_none()
    logger.debug(
        "[get_calendar_event] Queried calendar event: user_id=%s, match_id=%s, found=%s",
        user_id,
        match_id,
        event is not None,
    )
    return event


async def create_calendar_event(
    db: AsyncSession, user_id: int, match_id: int, event_id: str
) -> CalendarEvent:

    event = CalendarEvent(
        user_id=user_id,
        match_id=match_id,
        google_event_id=event_id,
    )
    db.add(event)
    await db.flush()
    logger.debug(
        "[create_calendar_event] Created calendar event: user_id=%s, match_id=%s, event_id=%s",
        user_id,
        match_id,
        event_id,
    )
    return event


async def sync_subscriptions_to_calendar(
    db: AsyncSession, user: User, matches: list[Match]
) -> int:
    """
    Adds all provided matches to the user's Google Calendar.
    Skips matches already in the past.
    Returns the number of events added.
    """

    token = await get_user_token(db, user.id)
    if not token:
        return 0

    now = datetime.now(timezone.utc)
    added = 0

    for match in matches:
        if match.kickoff_utc <= now:
            continue

        event_id = add_match_to_calendar(token, match)

        if event_id:
            await create_calendar_event(
                db,
                user_id=user.id,
                match_id=match.id,
                event_id=event_id,
            )
            added += 1

    # Update token if it was refreshed
    creds = _build_credentials(token)
    if creds.expiry and creds.expiry != token.token_expiry:
        token.access_token = creds.token
        token.token_expiry = creds.expiry
        await db.flush()

    return added
