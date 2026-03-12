from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.route import Route
from app.models.stop import Stop
from app.schemas.incident import IncidentCreate, IncidentUpdate


def _validate_route_and_stop(db: Session, route_id: int, stop_id: Optional[int]) -> None:
    route = db.get(Route, route_id)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found.")

    if stop_id is not None and db.get(Stop, stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found.")


def list_incidents(
    db: Session,
    route_id: Optional[int] = None,
    severity: Optional[str] = None,
    status_value: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Incident]:
    query = db.query(Incident).order_by(Incident.reported_at.desc())
    if route_id is not None:
        query = query.filter(Incident.route_id == route_id)
    if severity is not None:
        query = query.filter(Incident.severity == severity)
    if status_value is not None:
        query = query.filter(Incident.status == status_value)
    return query.offset(offset).limit(limit).all()


def get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")
    return incident


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    _validate_route_and_stop(db, payload.route_id, payload.stop_id)
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, incident: Incident, payload: IncidentUpdate) -> Incident:
    updates = payload.model_dump(exclude_unset=True)
    route_id = updates.get("route_id", incident.route_id)
    stop_id = updates.get("stop_id", incident.stop_id)
    _validate_route_and_stop(db, route_id, stop_id)

    for field, value in updates.items():
        setattr(incident, field, value)

    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident: Incident) -> None:
    db.delete(incident)
    db.commit()
