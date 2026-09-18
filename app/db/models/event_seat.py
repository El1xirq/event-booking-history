from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import EventSeatStatus


class EventSeatORM(Base):
    __tablename__ = "event_seats"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "seat_id",
            name="uq_event_seat",
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
        ForeignKey("seats.id"),
        nullable=False,
    )

    reservation_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reservations.id", ondelete="SET NULL"),
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    status: Mapped[EventSeatStatus] = mapped_column(
        SAEnum(EventSeatStatus, name="event_seat_status"),
        nullable=False,
        default=EventSeatStatus.AVAILABLE,
    )

    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    reservation_items: Mapped[list["ReservationItemORM"]] = relationship(
        "ReservationItemORM",
        back_populates="event_seat",
    )