from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ReservationStatus


class ReservationORM(Base):
    __tablename__ = "reservations"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id"),
        nullable=False,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        SAEnum(ReservationStatus, name="reservation_status"),
        nullable=False,
        default=ReservationStatus.PENDING,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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

    user: Mapped["UserORM"] = relationship(
        "UserORM",
        back_populates="reservations",
    )

    event: Mapped["EventORM"] = relationship(
        "EventORM",
        back_populates="reservations",
    )

    items: Mapped[list["ReservationItemORM"]] = relationship(
        "ReservationItemORM",
        back_populates="reservation",
        cascade="all, delete-orphan",
    )

    held_seats: Mapped[list["EventSeatORM"]] = relationship(
        "EventSeatORM",
        back_populates="reservation",
        foreign_keys="EventSeatORM.reservation_id",
    )

    notifications: Mapped[list["NotificationORM"]] = relationship(
        "NotificationORM",
        back_populates="reservation",
    )