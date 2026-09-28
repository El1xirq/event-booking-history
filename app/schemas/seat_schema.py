from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

from app.db.models.enums import SeatType

class SeatCreateRequest(BaseModel):
    row_number: str = Field(min_length=1, max_length=20)
    seat_number: str = Field(min_length=1, max_length=20)
    seat_type: SeatType = SeatType.STANDARD


class SeatUpdateRequest(BaseModel):
    row_number: str | None = Field(min_length=1, max_length=20, default=None)
    seat_number: str | None = Field(min_length=1, max_length=20, default=None)
    seat_type: SeatType | None = None


class SeatResponse(BaseModel):
    id: UUID
    venue_id: UUID
    row_number: str
    seat_number: str
    seat_type: SeatType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)