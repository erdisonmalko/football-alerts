from celery import Celery
from celery.schedules import crontab

from app.v1.core.config import settings

celery_app = Celery(
    "football_alerts",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.v1.tasks.alert_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Beat schedule — runs every hour to check all alert windows
    beat_schedule={
        # Sync fresh match data from football-data.org twice a day
        "sync-matches-morning": {
            "task": "app.v1.tasks.alert_tasks.sync_matches_task",
            "schedule": crontab(hour=7, minute=0),
        },
        "sync-matches-evening": {
            "task": "app.v1.tasks.alert_tasks.sync_matches_task",
            "schedule": crontab(hour=18, minute=0),
        },
        # Check and dispatch alert emails every hour
        "dispatch-alerts": {
            "task": "app.v1.tasks.alert_tasks.dispatch_alerts_task",
            "schedule": crontab(minute=0),  # top of every hour
        },
        # Update live match statuses and scores every 15 minutes
        "update-match-statuses": {
            "task": "app.v1.tasks.alert_tasks.update_match_statuses_task",
            "schedule": crontab(minute="*/15"),
        },
        "sync-calendars": {
            "task": "app.v1.tasks.alert_tasks.sync_calendar_task",
            "schedule": crontab(hour=7, minute=30),  # 30 min after morning match sync
        },
    },
)
