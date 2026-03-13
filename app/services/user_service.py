from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.models import Subscription, User
from app.schemas.schemas import SubscriptionCreate, UserRegister

from app.core.logger import get_logger
logger = get_logger(__name__)
# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    logger.debug(f"Fetching user by email: {email}")
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    logger.debug(f"Fetching user by ID: {user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserRegister) -> User:
    logger.debug(f"Creating user with email: {data.email}")
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()  # get the id without committing
    logger.info(f"Created user with ID: {user.id} and email: {user.email}")
    return user


# ── Subscriptions ─────────────────────────────────────────────────────────────

async def get_user_subscriptions(db: AsyncSession, user_id: int) -> list[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )
    logger.debug(f"Fetching subscriptions for user ID: {user_id}")
    return list(result.scalars().all())


async def create_subscription(
    db: AsyncSession, user_id: int, data: SubscriptionCreate
) -> Subscription:
    # Upsert-style: if it already exists just return it
    existing = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.subscription_type == data.subscription_type,
            Subscription.external_id == data.external_id,
        )
    )
    sub = existing.scalar_one_or_none()
    if sub:
        logger.debug(f"Subscription already exists for user ID: {user_id}, type: {data.subscription_type}.")
        return sub

    sub = Subscription(
        user_id=user_id,
        subscription_type=data.subscription_type,
        external_id=data.external_id,
        display_name=data.display_name,
    )
    db.add(sub)
    await db.flush()
    logger.info(f"Created subscription ID: {sub.id} for user ID: {user_id}, type: {data.subscription_type}")
    return sub


async def delete_subscription(
    db: AsyncSession, user_id: int, subscription_id: int
) -> bool:
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        logger.warning(f"Subscription ID: {subscription_id} not found for user ID: {user_id}")
        return False
    await db.delete(sub)
    logger.info(f"Deleted subscription ID: {subscription_id} for user ID: {user_id}")
    return True
