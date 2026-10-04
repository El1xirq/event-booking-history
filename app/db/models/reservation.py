from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Uuid,
    func,
    String,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import ReservationStatus


class ReservationORM(Base):
    __tablename__ = "reservations"

    __table_args__ = (
    CheckConstraint(
        "status IN ('pending', 'confirmed', 'cancelled', 'expired')",
        name="ck_reservation_status",
    ),
)

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReservationStatus.PENDING.value,
        server_default=ReservationStatus.PENDING.value,
    )  

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
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

    held_seats: Mapped[list["EventSeatORM"]] = relationship(
        "EventSeatORM",
        back_populates="reservation",
        foreign_keys="EventSeatORM.reservation_id",
    )
    
    notifications: Mapped[list["NotificationORM"]] = relationship(
        "NotificationORM",
        back_populates="reservation",
    )