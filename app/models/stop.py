from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    stop_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    stop_name: Mapped[str] = mapped_column(String(255))
    locality: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    route_stops: Mapped[list["RouteStop"]] = relationship(back_populates="stop", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="stop")
