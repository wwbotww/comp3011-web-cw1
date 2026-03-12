from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.route import Route
from app.models.route_stop import RouteStop
from app.schemas.route import RouteDetail, RouteRead

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteRead])
def list_routes(
    operator_id: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Route]:
    query = db.query(Route).order_by(Route.route_code.asc())
    if operator_id is not None:
        query = query.filter(Route.operator_id == operator_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter((Route.route_code.ilike(pattern)) | (Route.route_name.ilike(pattern)))
    return query.offset(offset).limit(limit).all()


@router.get("/{route_id}", response_model=RouteDetail)
def get_route(route_id: int, db: Session = Depends(get_db)) -> RouteDetail:
    route = (
        db.query(Route)
        .options(
            selectinload(Route.operator),
            selectinload(Route.route_stops).selectinload(RouteStop.stop),
        )
        .filter(Route.id == route_id)
        .first()
    )
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found.")

    ordered_stops = [link.stop for link in sorted(route.route_stops, key=lambda item: item.stop_sequence)]
    return RouteDetail(
        id=route.id,
        operator_id=route.operator_id,
        route_code=route.route_code,
        route_name=route.route_name,
        origin=route.origin,
        destination=route.destination,
        operator=route.operator,
        stops=ordered_stops,
    )
