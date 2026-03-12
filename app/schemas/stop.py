from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class StopRead(BaseModel):
    id: int
    stop_code: str
    stop_name: str
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
