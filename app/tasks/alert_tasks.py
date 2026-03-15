"""
Celery tasks for match syncing and alert dispatch.
"""

import asyncio
import logging
import time

from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.tasks.alert_tasks")
logger.setLevel(logging.DEBUG)


# ───────────────────────────────────────────────────────────
# Utility
# ───────────────────────────────────────────────────────────


def run_async(coro):
    """Run async coroutine from sync Celery worker."""
    logger.debug("[run_async] Creating new event loop")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        start = time.time()
        result = loop.run_until_complete(coro)
        logger.debug("[run_async] Coroutine finished in %.2fs", time.time() - start)
        return result
    finally:
        logger.debug("[run_async] Closing event loop")
        loop.close()


# ───────────────────────────────────────────────────────────
# Celery tasks
# ───────────────────────────────────────────────────────────


@celery_app.task(
    name="app.tasks.alert_tasks.sync_matches_task", bind=True, max_retries=3
)
def sync_matches_task(self):
    task_id = self.request.id
    logger.info(
        "[sync_matches_task] START task_id=%s retries=%s", task_id, self.request.retries
    )

    try:
        run_async(_sync_matches())
        logger.info("[sync_matches_task] SUCCESS task_id=%s", task_id)

    except Exception as exc:
        logger.exception("[sync_matches_task] FAILED task_id=%s error=%s", task_id, exc)
        raise self.retry(exc=exc, countdown=60 * 5)


@celery_app.task(
    name="app.tasks.alert_tasks.dispatch_alerts_task", bind=True, max_retries=3
)
def dispatch_alerts_task(self):
    task_id = self.request.id

    logger.info(
        "[dispatch_alerts_task] START task_id=%s retries=%s",
        task_id,
        self.request.retries,
    )

    try:
        run_async(_dispatch_alerts())

        logger.info("[dispatch_alerts_task] COMPLETED task_id=%s", task_id)

    except Exception as exc:
        logger.exception(
            "[dispatch_alerts_task] FAILED task_id=%s error=%s", task_id, exc
        )
        raise self.retry(exc=exc, countdown=60 * 2)


# ───────────────────────────────────────────────────────────
# Async implementations
# ───────────────────────────────────────────────────────────


async def _sync_matches():
    logger.debug("[_sync_matches] Opening DB session")

    from app.db.session import AsyncSessionLocal
    from app.services.match_service import (
        sync_all_leagues,
        cleanup_past_match_subscriptions,
    )

    async with AsyncSessionLocal() as db:
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
    logger.debug("[_dispatch_alerts] Opening DB session")

    from app.db.session import AsyncSessionLocal
    from app.models.models import AlertType
    from app.services.match_service import (
        get_matches_due_for_alerts,
        get_subscribed_user_ids_for_match,
        has_alert_been_sent,
        record_alert_sent,
    )
    from app.services.user_service import get_user_by_id
    from app.services.email_service import send_match_alert

    async with AsyncSessionLocal() as db:
        logger.debug("[_dispatch_alerts] DB session opened")

        for alert_type in AlertType:
            logger.debug("[_dispatch_alerts] Checking alert type: %s", alert_type.value)

            matches = await get_matches_due_for_alerts(db, alert_type)

            logger.debug(
                "[_dispatch_alerts] Found %s matches for alert type %s",
                len(matches),
                alert_type.value,
            )

            for match in matches:
                logger.debug(
                    "[_dispatch_alerts] Processing match id=%s kickoff=%s",
                    match.id,
                    match.kickoff_utc,
                )

                user_ids = await get_subscribed_user_ids_for_match(db, match)

                logger.debug(
                    "[_dispatch_alerts] %s subscribed users for match %s",
                    len(user_ids),
                    match.id,
                )

                for user_id in user_ids:
                    logger.debug(
                        "[_dispatch_alerts] Checking alert history user=%s match=%s",
                        user_id,
                        match.id,
                    )

                    already_sent = await has_alert_been_sent(
                        db, user_id, match.id, alert_type
                    )

                    if already_sent:
                        logger.debug(
                            "[_dispatch_alerts] Alert already sent user=%s match=%s",
                            user_id,
                            match.id,
                        )
                        continue

                    user = await get_user_by_id(db, user_id)

                    if not user:
                        logger.warning(
                            "[_dispatch_alerts] User not found user_id=%s", user_id
                        )
                        continue

                    if not user.is_active:
                        logger.debug(
                            "[_dispatch_alerts] User inactive user_id=%s", user_id
                        )
                        continue

                    logger.debug(
                        "[_dispatch_alerts] Sending email to %s for match %s",
                        user.email,
                        match.id,
                    )

                    success = await send_match_alert(user, match, alert_type)

                    if success:
                        logger.debug(
                            "[_dispatch_alerts] Email sent successfully user=%s match=%s",
                            user.email,
                            match.id,
                        )

                        await record_alert_sent(db, user_id, match.id, alert_type)

                        logger.info(
                            "[alerts] Sent %s alert → %s for match %s",
                            alert_type.value,
                            user.email,
                            match.id,
                        )

                    else:
                        logger.error(
                            "[_dispatch_alerts] Email sending FAILED user=%s match=%s",
                            user.email,
                            match.id,
                        )

        logger.debug("[_dispatch_alerts] Committing DB changes")
        await db.commit()

    logger.debug("[_dispatch_alerts] DB session closed")
