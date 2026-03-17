"""
Google OAuth routes for Calendar integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.services.google_calendar_service import (
    delete_user_token,
    exchange_code_for_tokens,
    get_authorization_url,
    get_user_token,
    save_user_token,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/google", tags=["google"])


@router.get("/connect")
async def google_connect(current_user: User = Depends(get_current_user)):
    """Redirects the user to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Calendar integration is not configured.",
        )
    auth_url, _ = get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Handles the OAuth callback, stores tokens, redirects to frontend."""
    try:
        tokens = exchange_code_for_tokens(code)
        await save_user_token(
            db,
            user_id=current_user.id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_expiry=tokens["token_expiry"],
        )
        await db.commit()
        logger.info("Google Calendar connected for user %s", current_user.email)
    except Exception as exc:
        logger.error(
            "Google OAuth callback failed for user %s: %s", current_user.email, exc
        )
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/subscriptions?google=error"
        )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/subscriptions?google=connected"
    )


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def google_disconnect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Removes the user's stored Google tokens."""
    await delete_user_token(db, current_user.id)
    await db.commit()
    logger.info("Google Calendar disconnected for user %s", current_user.email)


@router.get("/status")
async def google_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns whether the user has Google Calendar connected."""
    token = await get_user_token(db, current_user.id)
    return {"connected": token is not None}
