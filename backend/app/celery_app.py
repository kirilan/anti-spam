from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "antispam",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.email_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_extended=True,

    # Retry configuration for failed tasks
    task_acks_late=True,  # Acknowledge tasks after completion, not before
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker crashes
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    'scan-responses-hourly': {
        'task': 'app.tasks.email_tasks.scan_all_users_for_responses',
        'schedule': crontab(minute=0),  # Run at the top of every hour (development)
    },
}
