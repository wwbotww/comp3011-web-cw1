from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), index=True)
    route_code: Mapped[str] = mapped_column(String(64), index=True)
    route_name: Mapped[str] = mapped_column(String(255))
    origin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    operator: Mapped["Operator"] = relationship(back_populates="routes")
    route_stops: Mapped[list["RouteStop"]] = relationship(back_populates="route", cascade="all, delete-orphan")
    reliability_metrics: Mapped[list["ReliabilityMetric"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="route")
