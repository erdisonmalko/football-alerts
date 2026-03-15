import asyncio

from celery import Celery
from celery.signals import worker_process_init
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "football_alerts",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.alert_tasks"],
)


@worker_process_init.connect
def init_worker(**kwargs):
    """
    Ensures each Celery worker process creates its own
    SQLAlchemy connection pool instead of inheriting
    the parent process pool.
    """
    from app.db.session import engine

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(engine.dispose())
    loop.close()


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        # Sync fresh match data from football-data.org twice a day
        "sync-matches-morning": {
            "task": "app.tasks.alert_tasks.sync_matches_task",
            "schedule": crontab(hour=7, minute=0),
        },
        "sync-matches-evening": {
            "task": "app.tasks.alert_tasks.sync_matches_task",
            "schedule": crontab(hour=18, minute=0),
        },
        # Check and dispatch alert emails every hour
        "dispatch-alerts": {
            "task": "app.tasks.alert_tasks.dispatch_alerts_task",
            "schedule": crontab(minute=0),
        },
    },
)
