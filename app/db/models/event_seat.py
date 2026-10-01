from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Uuid,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventSeatORM(Base):
    __tablename__ = "event_seats"

    __table_args__ = (
        UniqueConstraint("event_id", "seat_id", name="uq_event_seat"),
        Index(
            "uq_event_seat_active_reservation",
            "event_id",
            "seat_id",
            unique=True,
            postgresql_where=text("reservation_id IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    seat_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("seats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reservation_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reservations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    event: Mapped["EventORM"] = relationship(
        "EventORM",
        back_populates="event_seats",
    )

    seat: Mapped["SeatORM"] = relationship(
        "SeatORM",
        back_populates="event_seats",
    )

    reservation: Mapped["ReservationORM | None"] = relationship(
        "ReservationORM",
        back_populates="held_seats",
        foreign_keys=[reservation_id],
    )

    from datetime import datetime, timezone

    @property
    def status(self) -> str:
        if self.reservation_id is None:
            return "available"
        if self.hold_expires_at is None:
            return "sold"
        if self.hold_expires_at < datetime.now(timezone.utc):
            return "available"
        return "held"