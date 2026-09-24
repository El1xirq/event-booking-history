from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime


class VenueCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)
    description: str | None = None


class VenueUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=255)


class VenueResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    address: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    
    model_config = ConfigDict(from_attributes=True)


