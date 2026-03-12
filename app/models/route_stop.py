from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RouteStop(Base):
    __tablename__ = "route_stops"

    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), primary_key=True, index=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("stops.id"), primary_key=True, index=True)
    stop_sequence: Mapped[int] = mapped_column(default=0)

    route: Mapped["Route"] = relationship(back_populates="route_stops")
    stop: Mapped["Stop"] = relationship(back_populates="route_stops")
