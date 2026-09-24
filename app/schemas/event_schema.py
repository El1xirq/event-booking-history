from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from uuid import UUID
from datetime import datetime, timezone

from app.db.models.enums import EventStatus

class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    venue_id: UUID
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at")
    @classmethod
    def starts_at_must_be_future(cls, v: datetime) -> datetime:
        if v <= datetime.now(timezone.utc):
            raise ValueError("starts_at must be in the future")
        return v

    @model_validator(mode="after")
    def check_dates_order(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class EventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    venue_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class EventResponse(BaseModel):
    id: UUID
    organizer_id: UUID
    venue_id: UUID
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)