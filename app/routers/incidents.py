from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.api_key import require_write_api_key
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.services.incident_service import (
    create_incident,
    delete_incident,
    get_incident_or_404,
    list_incidents,
    update_incident,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident_endpoint(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    return create_incident(db, payload)


@router.get("", response_model=list[IncidentRead])
def list_incidents_endpoint(
    route_id: Optional[int] = None,
    severity: Optional[str] = Query(default=None, pattern="^(low|medium|high)$"),
    status_value: Optional[str] = Query(default=None, alias="status", pattern="^(open|monitoring|resolved)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_incidents(db, route_id=route_id, severity=severity, status_value=status_value, limit=limit, offset=offset)


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident_endpoint(incident_id: int, db: Session = Depends(get_db)):
    return get_incident_or_404(db, incident_id)


@router.put("/{incident_id}", response_model=IncidentRead)
def update_incident_endpoint(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
):
    incident = get_incident_or_404(db, incident_id)
    return update_incident(db, incident, payload)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_write_api_key),
) -> Response:
    incident = get_incident_or_404(db, incident_id)
    delete_incident(db, incident)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
