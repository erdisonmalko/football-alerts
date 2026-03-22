"""
Celery tasks for match syncing and alert dispatch.
"""

import asyncio
from sqlalchemy import text
from app.v1.tasks.celery_app import celery_app
from app.v1.tasks.async_task import AsyncTask
from app.v1.core.logger import get_logger

logger = get_logger(__name__)


# ───────────────────────────────────────────────────────────
# Celery tasks
# ───────────────────────────────────────────────────────────


@celery_app.task(
    name="app.v1.tasks.alert_tasks.sync_matches_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def sync_matches_task(self):
    logger.info("[sync_matches_task] START")
    try:
        return self.run_async(_sync_matches())
    except Exception as exc:
        logger.exception("[sync_matches_task] FAILED: %s", exc)
        raise self.retry(exc=exc, countdown=300)  # retry after 5 min


@celery_app.task(
    name="app.v1.tasks.alert_tasks.dispatch_alerts_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def dispatch_alerts_task(self):
    logger.info("[dispatch_alerts_task] START")
    try:
        return self.run_async(_dispatch_alerts())
    except Exception as exc:
        logger.exception("[dispatch_alerts_task] FAILED: %s", exc)
        raise self.retry(exc=exc, countdown=120)  # retry after 2 min


@celery_app.task(
    name="app.v1.tasks.alert_tasks.update_match_statuses_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def update_match_statuses_task(self):
    logger.info("[update_match_statuses_task] START")
    try:
        return self.run_async(_update_match_statuses())
    except Exception as exc:
        logger.exception("[update_match_statuses_task] FAILED: %s", exc)
        raise self.retry(exc=exc, countdown=60)  # retry after 1 min


@celery_app.task(
    name="app.v1.tasks.alert_tasks.sync_calendar_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def sync_calendar_task(self):
    logger.info("[sync_calendar_task] START")
    try:
        return self.run_async(_sync_calendars())
    except Exception as exc:
        logger.exception("[sync_calendar_task] FAILED: %s", exc)
        raise self.retry(exc=exc, countdown=120)  # retry after 2 min


# ───────────────────────────────────────────────────────────
# Async implementations
# ───────────────────────────────────────────────────────────


async def _sync_matches():
    logger.debug("[_sync_matches] Opening DB session")

    from app.v1.db.celery_session import CelerySessionLocal
    from app.v1.services.match_service import (
        sync_all_leagues,
        cleanup_past_match_subscriptions,
    )

    async with CelerySessionLocal() as db:
        logger.debug("[_sync_matches] DB session opened")
        results = await sync_all_leagues(db)
        logger.debug("[_sync_matches] sync_all_leagues() returned: %s", results)

        deleted = await cleanup_past_match_subscriptions(db)
        logger.debug("[_sync_matches] cleanup result: %s deleted", deleted)

        await db.commit()
        logger.info("[_sync_matches] Match sync complete: %s", results)

        if deleted:
            logger.info(
                "[_sync_matches] Cleaned up %s past match subscription(s)", deleted
            )

    logger.debug("[_sync_matches] DB session closed")


async def _dispatch_alerts():
    logger.info("[_dispatch_alerts] coroutine started")

    from app.v1.db.celery_session import CelerySessionLocal
    from app.v1.models.models import AlertType
    from app.v1.services.match_service import (
        get_matches_due_for_alerts,
        get_subscribed_user_ids_for_match,
        has_alert_been_sent,
        record_alert_sent,
    )
    from app.v1.services.user_service import get_user_by_id
    from app.v1.services.email_service import send_match_alert

    logger.info("[_dispatch_alerts] opening DB session")

    async with CelerySessionLocal() as db:
        logger.info("[_dispatch_alerts] DB session acquired")

        await db.execute(text("SELECT 1"))
        logger.info("[_dispatch_alerts] DB connection verified")

        for alert_type in AlertType:
            logger.info("[_dispatch_alerts] checking alert type %s", alert_type)
            matches = await get_matches_due_for_alerts(db, alert_type)
            logger.info("[_dispatch_alerts] %s matches found", len(matches))

            for match in matches:
                user_ids = await get_subscribed_user_ids_for_match(db, match)

                for user_id in user_ids:
                    already_sent = await has_alert_been_sent(
                        db, user_id, match.id, alert_type
                    )
                    if already_sent:
                        continue

                    user = await get_user_by_id(db, user_id)
                    if not user or not user.is_active:
                        continue

                    success = await send_match_alert(user, match, alert_type)
                    if success:
                        await record_alert_sent(db, user_id, match.id, alert_type)
                        logger.info(
                            "[_dispatch_alerts] sent %s alert → %s",
                            alert_type,
                            user.email,
                        )
                        await asyncio.sleep(0.6)  # stay under 2 req/sec

        await db.commit()

    logger.info("[_dispatch_alerts] dispatch complete")


async def _update_match_statuses():
    logger.debug("[_update_match_statuses] Opening DB session")

    from app.v1.db.celery_session import CelerySessionLocal
    from app.v1.services.match_service import update_live_and_recent_matches

    async with CelerySessionLocal() as db:
        results = await update_live_and_recent_matches(db)
        await db.commit()
        logger.info("[_update_match_statuses] Updated: %s", results)


async def _sync_calendars():
    logger.info("[_sync_calendars] started")

    from app.v1.db.celery_session import CelerySessionLocal
    from app.v1.models.models import GoogleToken, CalendarEvent
    from app.v1.services.match_service import get_matches_for_user
    from app.v1.services.google_calendar_service import sync_subscriptions_to_calendar
    from app.v1.services.user_service import get_user_by_id
    from sqlalchemy import select

    async with CelerySessionLocal() as db:
        result = await db.execute(select(GoogleToken))
        tokens = result.scalars().all()
        logger.info("[_sync_calendars] %s users with Google Calendar", len(tokens))

        for token in tokens:
            user = await get_user_by_id(db, token.user_id)
            if not user or not user.is_active:
                continue

            match_data = await get_matches_for_user(db, token.user_id)
            upcoming = match_data["upcoming"]

            existing_result = await db.execute(
                select(CalendarEvent.match_id).where(CalendarEvent.user_id == user.id)
            )
            existing_match_ids = set(existing_result.scalars().all())
            new_matches = [m for m in upcoming if m.id not in existing_match_ids]

            if not new_matches:
                continue

            added = await sync_subscriptions_to_calendar(db, user, new_matches)
            logger.info(
                "[_sync_calendars] user %s: added %s calendar events", user.email, added
            )

        await db.commit()

    logger.info("[_sync_calendars] complete")
