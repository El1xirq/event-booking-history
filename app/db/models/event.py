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
from app.db.models.enums import EventStatus


class EventORM(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    organizer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    venue_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("venues.id"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus, name="event_status"),
        nullable=False,
        default=EventStatus.DRAFT,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organizer: Mapped["UserORM"] = relationship(
        "UserORM",
        foreign_keys=[organizer_id],
    )

    venue: Mapped["VenueORM"] = relationship(
        "VenueORM",
        back_populates="events",
    )

    event_seats: Mapped[list["EventSeatORM"]] = relationship(
        "EventSeatORM",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    reservations: Mapped[list["ReservationORM"]] = relationship(
        "ReservationORM",
        back_populates="event",
    )

    reports: Mapped[list["ReportORM"]] = relationship(
        "ReportORM",
        back_populates="event",
    )