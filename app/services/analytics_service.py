from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.reliability_metric import ReliabilityMetric
from app.models.route import Route
from app.schemas.analytics import ReliabilitySummary


def get_route_reliability(
    db: Session,
    route_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    time_band: Optional[str] = None,
) -> ReliabilitySummary:
    if db.get(Route, route_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found.")

    query = db.query(
        func.avg(ReliabilityMetric.avg_delay_minutes),
        func.avg(ReliabilityMetric.on_time_rate),
        func.avg(ReliabilityMetric.cancellation_rate),
        func.sum(ReliabilityMetric.observation_count),
    ).filter(ReliabilityMetric.route_id == route_id)

    if start_date is not None:
        query = query.filter(ReliabilityMetric.metric_date >= start_date)
    if end_date is not None:
        query = query.filter(ReliabilityMetric.metric_date <= end_date)
    if time_band is not None:
        query = query.filter(ReliabilityMetric.time_band == time_band)

    avg_delay, on_time_rate, cancellation_rate, observation_count = query.one()
    if observation_count is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reliability metrics found.")

    return ReliabilitySummary(
        route_id=route_id,
        start_date=start_date,
        end_date=end_date,
        time_band=time_band,
        avg_delay_minutes=round(float(avg_delay or 0.0), 2),
        on_time_rate=round(float(on_time_rate or 0.0), 4),
        cancellation_rate=round(float(cancellation_rate or 0.0), 4),
        observation_count=int(observation_count or 0),
    )
