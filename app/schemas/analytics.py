from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class ReliabilitySummary(BaseModel):
    route_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    time_band: Optional[str] = None
    avg_delay_minutes: float
    on_time_rate: float
    cancellation_rate: float
    observation_count: int
