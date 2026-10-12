import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete

from app.core.celery_app import celery_app
from app.db.session import sync_session
from app.db.models.refresh_token import RefreshTokenORM


logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_refresh_tokens")
def cleanup_expired_refresh_tokens() -> int:
    """Delete refresh tokens that are expired or revoked long ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    with sync_session() as session:
        stmt = delete(RefreshTokenORM).where(
            RefreshTokenORM.revoked_at.is_not(None),
            RefreshTokenORM.revoked_at < cutoff,
        )
        result = session.execute(stmt)
        session.commit()
        deleted = result.rowcount

    logger.info(f"[CLEANUP] Deleted {deleted} expired/revoked refresh tokens")
    return deleted