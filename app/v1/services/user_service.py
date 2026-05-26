from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.v1.core.security import hash_password
from app.v1.models.models import Subscription, User, SubscriptionType, ServerMember
from app.v1.schemas.schemas import SubscriptionCreate, UserRegister

from app.v1.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


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
    await db.flush()
    logger.info(f"User created: {user.email} (id={user.id})")
    return user


# ── Subscriptions ─────────────────────────────────────────────────────────────


async def get_user_subscriptions(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 100,
    subscription_type: Optional[SubscriptionType] = None,
) -> tuple[list[Subscription], int]:
    """Return a page of subscriptions and the total count.

    Returns (items, total)
    """
    base_where = (Subscription.user_id == user_id,)
    if subscription_type is not None:
        count_q = (
            select(func.count())
            .select_from(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.subscription_type == subscription_type,
            )
        )
        data_q = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.subscription_type == subscription_type,
            )
            .order_by(Subscription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    else:
        count_q = (
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user_id)
        )
        data_q = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

    total_res = await db.execute(count_q)
    total = int(total_res.scalar_one())
    result = await db.execute(data_q)
    items = list(result.scalars().all())
    return items, total


async def get_user_profile_stats(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(Subscription.subscription_type, func.count())
        .where(Subscription.user_id == user_id)
        .group_by(Subscription.subscription_type)
    )
    type_counts = {
        SubscriptionType.LEAGUE.value: 0,
        SubscriptionType.TEAM.value: 0,
        SubscriptionType.MATCH.value: 0,
    }
    total = 0
    for subscription_type, count in result.all():
        type_counts[subscription_type] = int(count)
        total += int(count)

    server_result = await db.execute(
        select(func.count())
        .select_from(ServerMember)
        .where(ServerMember.user_id == user_id)
    )
    server_count = int(server_result.scalar_one())

    return {
        "total_alerts": total,
        "league_alerts": type_counts[SubscriptionType.LEAGUE.value],
        "team_alerts": type_counts[SubscriptionType.TEAM.value],
        "match_alerts": type_counts[SubscriptionType.MATCH.value],
        "servers_joined": server_count,
    }


async def create_subscription(
    db: AsyncSession, user_id: int, data: SubscriptionCreate
) -> Subscription:
    existing = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.subscription_type == data.subscription_type,
            Subscription.external_id == data.external_id,
        )
    )
    sub = existing.scalar_one_or_none()
    if sub:
        logger.debug(
            f"Subscription already exists for user {user_id}: {data.subscription_type.value}"
        )
        return None  # Caller will handle the conflict response

    sub = Subscription(
        user_id=user_id,
        subscription_type=data.subscription_type,
        external_id=data.external_id,
        display_name=data.display_name,
    )
    db.add(sub)
    await db.flush()
    logger.info(
        f"Subscription created for user {user_id}: {data.subscription_type.value}"
    )
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
        logger.debug(f"Subscription {subscription_id} not found for user {user_id}")
        return False
    await db.delete(sub)
    logger.info(f"Subscription {subscription_id} deleted for user {user_id}")
    return True
