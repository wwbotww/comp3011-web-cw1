from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import ReliabilitySummary
from app.services.analytics_service import get_route_reliability

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/routes/{route_id}/reliability", response_model=ReliabilitySummary)
def get_route_reliability_endpoint(
    route_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    time_band: Optional[str] = Query(default=None, pattern="^(morning_peak|midday|evening_peak|off_peak)$"),
    db: Session = Depends(get_db),
) -> ReliabilitySummary:
    return get_route_reliability(
        db,
        route_id=route_id,
        start_date=start_date,
        end_date=end_date,
        time_band=time_band,
    )
