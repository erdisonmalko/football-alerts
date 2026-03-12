"""
Celery tasks for match syncing and alert dispatch.

Two tasks:
  1. sync_matches_task   — pulls upcoming matches from football-data.org into DB
  2. dispatch_alerts_task — checks all alert windows and sends emails
"""

import asyncio

from app.tasks.celery_app import celery_app

from app.core.logger import get_logger
logger = get_logger(__name__)

def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.tasks.alert_tasks.sync_matches_task", bind=True, max_retries=3)
def sync_matches_task(self):
    """Syncs upcoming matches from football-data.org for all supported leagues."""
    try:
        logger.info("Starting match sync task")
        run_async(_sync_matches())
    except Exception as exc:
        logger.error(f"Match sync failed with error: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # retry after 5 min


@celery_app.task(name="app.tasks.alert_tasks.dispatch_alerts_task", bind=True, max_retries=3)
def dispatch_alerts_task(self):
    """Checks all alert windows and dispatches emails to subscribed users."""
    try:
        logger.info("Starting alert dispatch task")
        run_async(_dispatch_alerts())
    except Exception as exc:
        logger.error(f"Alert dispatch failed with error: {exc}")
        raise self.retry(exc=exc, countdown=60 * 2)


# ── Async implementations ─────────────────────────────────────────────────────

async def _sync_matches():
    from app.db.session import AsyncSessionLocal
    from app.services.match_service import sync_all_leagues

    async with AsyncSessionLocal() as db:
        results = await sync_all_leagues(db)
        await db.commit()
        logger.info(f"Match sync complete: {results}")


async def _dispatch_alerts():
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
        for alert_type in AlertType:
            matches = await get_matches_due_for_alerts(db, alert_type)
            logger.info(f"{alert_type.value}: {len(matches)} matches in window")

            for match in matches:
                user_ids = await get_subscribed_user_ids_for_match(db, match)

                for user_id in user_ids:
                    already_sent = await has_alert_been_sent(db, user_id, match.id, alert_type)
                    if already_sent:
                        continue

                    user = await get_user_by_id(db, user_id)
                    if not user or not user.is_active:
                        continue

                    success = await send_match_alert(user, match, alert_type)
                    if success:
                        await record_alert_sent(db, user_id, match.id, alert_type)
                        logger.info(f"Sent {alert_type.value} alert → {user.email} for match {match.id}")

        await db.commit()
