from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.stop import Stop
from app.schemas.stop import StopRead

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=list[StopRead])
def list_stops(
    q: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Stop]:
    query = db.query(Stop).order_by(Stop.stop_name.asc())
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter((Stop.stop_name.ilike(pattern)) | (Stop.locality.ilike(pattern)))
    return query.offset(offset).limit(limit).all()
