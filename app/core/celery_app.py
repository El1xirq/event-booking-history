from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "event_booking",
    broker=settings.redis_url,
    include=[
        "app.tasks.email",
        "app.tasks.cleanup",
    ],
)

celery_app.conf.update(
    task_ignore_result=True,
    task_track_started=False,
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)


celery_app.conf.beat_schedule = {
    "cleanup-expired-refresh-tokens": {
        "task": "app.tasks.cleanup.cleanup_expired_refresh_tokens",
        "schedule": 3600.0,
    },
}