from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    incident_type: str = Field(min_length=2, max_length=64)
    severity: str = Field(pattern="^(low|medium|high)$")
    status: str = Field(default="open", pattern="^(open|monitoring|resolved)$")
    route_id: int
    stop_id: Optional[int] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    incident_type: Optional[str] = Field(default=None, min_length=2, max_length=64)
    severity: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(default=None, pattern="^(open|monitoring|resolved)$")
    route_id: Optional[int] = None
    stop_id: Optional[int] = None


class IncidentRead(IncidentBase):
    id: int
    reported_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
