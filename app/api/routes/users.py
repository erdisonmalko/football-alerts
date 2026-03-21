from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import COOKIE_NAME, get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    SubscriptionCreate,
    SubscriptionOut,
    UserMatchesOut,
    UserOut,
    UserUpdate,
)
from app.services.match_service import get_matches_for_user
from app.services.user_service import (
    create_subscription,
    delete_subscription,
    get_user_subscriptions,
)

from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info("[get_me] User %s accessed their profile", current_user.email)
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    await db.commit()
    await db.refresh(current_user)
    logger.info("[update_me] User %s updated their profile", current_user.email)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes the account and clears the auth cookie."""
    await db.delete(current_user)
    await db.commit()
    logger.info("[delete_me] User %s deleted their account", current_user.email)
    response.delete_cookie(key=COOKIE_NAME, samesite="lax")


# ── User Matches ───────────────────────────────────────────────────────────────


@router.get("/me/matches", response_model=UserMatchesOut)
async def get_my_matches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns live, upcoming, and today's finished matches for the user's subscriptions."""
    logger.info("[get_my_matches] User %s requested their matches", current_user.email)
    return await get_matches_for_user(db, current_user.id)


# ── Subscriptions ──────────────────────────────────────────────────────────────


@router.get("/me/subscriptions", response_model=list[SubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists the user's current league/team subscriptions."""
    logger.info(
        "[list_subscriptions] User %s requested their subscriptions", current_user.email
    )
    return await get_user_subscriptions(db, current_user.id)


@router.post(
    "/me/subscriptions",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await create_subscription(db, current_user.id, data)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Subscription already exists"
        )
    await db.commit()
    await db.refresh(sub)
    logger.info(
        "[add_subscription] User %s added a new subscription", current_user.email
    )

    return sub


@router.delete(
    "/me/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_subscription(db, current_user.id, subscription_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    logger.info(
        "[remove_subscription] User %s removed a subscription", current_user.email
    )
