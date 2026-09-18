from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ReportStatus


class ReportORM(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
    )

    requested_by_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"),
        nullable=False,
        default=ReportStatus.PENDING,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    event: Mapped["EventORM"] = relationship(
        "EventORM",
        back_populates="reports",
    )

    requested_by: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="reports",
        foreign_keys=[requested_by_id],
    )