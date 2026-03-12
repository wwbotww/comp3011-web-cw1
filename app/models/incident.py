from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    stop_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stops.id"), nullable=True, index=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    route: Mapped["Route"] = relationship(back_populates="incidents")
    stop: Mapped["Stop"] = relationship(back_populates="incidents")
