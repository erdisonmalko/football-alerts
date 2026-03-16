"""
Celery tasks for match syncing and alert dispatch.
"""

import asyncio
from sqlalchemy import text

from app.tasks.celery_app import celery_app
from app.tasks.async_task import AsyncTask
from app.core.logger import get_logger

logger = get_logger(__name__)


# ───────────────────────────────────────────────────────────
# Celery tasks
# ───────────────────────────────────────────────────────────


@celery_app.task(
    name="app.tasks.alert_tasks.sync_matches_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def sync_matches_task(self):
    logger.info("[sync_matches_task] START")
    return self.run_async(_sync_matches())


@celery_app.task(
    name="app.tasks.alert_tasks.dispatch_alerts_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def dispatch_alerts_task(self):
    logger.info("[dispatch_alerts_task] START")
    return self.run_async(_dispatch_alerts())


# ───────────────────────────────────────────────────────────
# Async implementations
# ───────────────────────────────────────────────────────────


async def _sync_matches():
    logger.debug("[_sync_matches] Opening DB session")

    from app.db.celery_session import CelerySessionLocal
    from app.services.match_service import (
        sync_all_leagues,
        cleanup_past_match_subscriptions,
    )

    async with CelerySessionLocal() as db:
        logger.debug("[_sync_matches] DB session opened")

        logger.debug("[_sync_matches] Starting sync_all_leagues()")
        results = await sync_all_leagues(db)
        logger.debug("[_sync_matches] sync_all_leagues() returned: %s", results)

        logger.debug("[_sync_matches] Starting cleanup_past_match_subscriptions()")
        deleted = await cleanup_past_match_subscriptions(db)
        logger.debug("[_sync_matches] cleanup result: %s deleted", deleted)

        logger.debug("[_sync_matches] Committing transaction")
        await db.commit()

        logger.info("[_sync_matches] Match sync complete: %s", results)

        if deleted:
            logger.info(
                "[_sync_matches] Cleaned up %s past match subscription(s)", deleted
            )

    logger.debug("[_sync_matches] DB session closed")


async def _dispatch_alerts():
    logger.info("[_dispatch_alerts] coroutine started")
    from app.db.celery_session import CelerySessionLocal
    from app.models.models import AlertType
    from app.services.match_service import (
        get_matches_due_for_alerts,
        get_subscribed_user_ids_for_match,
        has_alert_been_sent,
        record_alert_sent,
    )
    from app.services.user_service import get_user_by_id
    from app.services.email_service import send_match_alert

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


@celery_app.task(
    name="app.tasks.alert_tasks.update_match_statuses_task",
    bind=True,
    base=AsyncTask,
    max_retries=3,
)
def update_match_statuses_task(self):
    logger.info("[update_match_statuses_task] START")
    return self.run_async(_update_match_statuses())


async def _update_match_statuses():
    logger.debug("[_update_match_statuses] Opening DB session")
    from app.db.celery_session import CelerySessionLocal
    from app.services.match_service import update_live_and_recent_matches

    async with CelerySessionLocal() as db:
        results = await update_live_and_recent_matches(db)
        await db.commit()
        logger.info("[_update_match_statuses] Updated: %s", results)
