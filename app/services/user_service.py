from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.models import Subscription, User
from app.schemas.schemas import SubscriptionCreate, UserRegister


# ── Users ─────────────────────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserRegister) -> User:
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()  # get the id without committing
    return user


# ── Subscriptions ─────────────────────────────────────────────────────────────

async def get_user_subscriptions(db: AsyncSession, user_id: int) -> list[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )
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
        return sub

    sub = Subscription(
        user_id=user_id,
        subscription_type=data.subscription_type,
        external_id=data.external_id,
        display_name=data.display_name,
    )
    db.add(sub)
    await db.flush()
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
        return False
    await db.delete(sub)
    return True
