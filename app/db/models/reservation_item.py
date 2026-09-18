from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReservationItemORM(Base):
    __tablename__ = "reservation_items"

    __table_args__ = (
        UniqueConstraint(
            "reservation_id",
            "event_seat_id",
            name="uq_reservation_item",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    reservation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_seat_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event_seats.id"),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    reservation: Mapped["ReservationORM"] = relationship(
        "ReservationORM",
        back_populates="items",
    )

    event_seat: Mapped["EventSeatORM"] = relationship(
        "EventSeatORM",
        back_populates="reservation_items",
    )