from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import SubscriptionCreate, SubscriptionOut, UserOut, UserUpdate
from app.services.user_service import (
    create_subscription,
    delete_subscription,
    get_user_subscriptions,
)

router = APIRouter(prefix="/users", tags=["users"])

from app.core.logger import _logger
logger = _logger()

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info(f"[app.api.routes.get_me] Fetching user info for: {current_user.email}")
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
    logger.info(f"[app.api.routes.update_me] Updated user info for: {current_user.email}(ID: {current_user.id})")
    return current_user


# ── Subscriptions ──────────────────────────────────────────────────────────────

@router.get("/me/subscriptions", response_model=list[SubscriptionOut])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):  
    logger.info(f"[app.api.routes.list_subscriptions] Fetching subscriptions for user: {current_user.email}(ID: {current_user.id})")
    return await get_user_subscriptions(db, current_user.id)


@router.post("/me/subscriptions",response_model=SubscriptionOut,status_code=status.HTTP_201_CREATED)
async def add_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[app.api.routes.add_subscription] Adding subscription for user: {current_user.email}(ID: {current_user.id}), league: {data.league_code}, team: {data.team_id}")
    sub = await create_subscription(db, current_user.id, data)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/me/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):  
    logger.info(f"""
    [app.api.routes.remove_subscription] 
    Removing subscription ID: {subscription_id} for user: {current_user.email}(ID: {current_user.id})
    """)
    deleted = await delete_subscription(db, current_user.id, subscription_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
