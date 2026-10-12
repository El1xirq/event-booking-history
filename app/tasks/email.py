import logging
from celery import shared_task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.email.send_confirmation_email")
def send_confirmation_email(reservation_id: str) -> None:
    logger.info(f"[EMAIL] Confirmation for reservation {reservation_id}")