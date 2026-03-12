from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReliabilityMetric(Base):
    __tablename__ = "reliability_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    time_band: Mapped[str] = mapped_column(String(32), index=True)
    avg_delay_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    on_time_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cancellation_rate: Mapped[float] = mapped_column(Float, default=0.0)
    observation_count: Mapped[int] = mapped_column(default=0)

    route: Mapped["Route"] = relationship(back_populates="reliability_metrics")
