from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.operator import OperatorRead
from app.schemas.stop import StopRead


class RouteRead(BaseModel):
    id: int
    operator_id: int
    route_code: str
    route_name: str
    origin: Optional[str] = None
    destination: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RouteDetail(RouteRead):
    operator: OperatorRead
    stops: list[StopRead]
