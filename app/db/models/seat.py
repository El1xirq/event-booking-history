from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    CheckConstraint,
    ForeignKey,
    String,
    Uuid,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import SeatType


class SeatORM(Base):
    __tablename__ = "seats"

    __table_args__ = (
        UniqueConstraint("venue_id", "row_number", "seat_number", name="uq_seat_position_in_venue"),
        CheckConstraint(
            "seat_type IN ('standard', 'vip')",
            name="ck_seats_seat_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    venue_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
    )

    row_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    seat_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    seat_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SeatType.STANDARD.value,
        server_default=SeatType.STANDARD.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    venue: Mapped["VenueORM"] = relationship(
        "VenueORM",
        back_populates="seats",
    )

    event_seats: Mapped[list["EventSeatORM"]] = relationship(
        "EventSeatORM",
        back_populates="seat",
    )