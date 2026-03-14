from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import COOKIE_NAME, get_current_user
from app.core.logger import get_logger
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import SubscriptionCreate, SubscriptionOut, UserOut, UserUpdate
from app.services.user_service import (
    create_subscription,
    delete_subscription,
    get_user_subscriptions,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
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
    logger.info(f"User updated: {current_user.email} (id={current_user.id})")
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
    response.delete_cookie(key=COOKIE_NAME, samesite="lax")
    logger.warning(f"User deleted: {current_user.email} (id={current_user.id})")


# ── Subscriptions ──────────────────────────────────────────────────────────────


@router.get("/me/subscriptions", response_model=list[SubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
