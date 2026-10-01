from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.db.models.enums import ReservationStatus

class ReservationCreateRequest(BaseModel):
    event_id: UUID
    event_seat_id: UUID


class ReservationResponse(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    status: ReservationStatus
    expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventSeatResponse(BaseModel):
    id: UUID
    event_id: UUID
    seat_id: UUID
    price: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)