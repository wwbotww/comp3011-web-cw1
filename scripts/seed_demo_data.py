from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Incident, Operator, ReliabilityMetric, Route, RouteStop, Stop


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Operator).count() == 0:
            operator = Operator(id=1, noc="LDS1", name="Leeds City Buses", region="Leeds")
            route = Route(
                id=1,
                operator_id=1,
                route_code="1",
                route_name="City Centre to Headingley",
                origin="Leeds City Centre",
                destination="Headingley",
            )
            stop_a = Stop(id=1, stop_code="STOP100", stop_name="Leeds Station", locality="Leeds", latitude=53.794, longitude=-1.548)
            stop_b = Stop(id=2, stop_code="STOP200", stop_name="Headingley Arndale", locality="Headingley", latitude=53.819, longitude=-1.579)
            db.add_all([operator, route, stop_a, stop_b])
            db.flush()
            db.add_all(
                [
                    RouteStop(route_id=1, stop_id=1, stop_sequence=1),
                    RouteStop(route_id=1, stop_id=2, stop_sequence=2),
                    ReliabilityMetric(
                        id=1,
                        route_id=1,
                        metric_date=date(2026, 3, 1),
                        time_band="morning_peak",
                        avg_delay_minutes=3.2,
                        on_time_rate=0.83,
                        cancellation_rate=0.02,
                        observation_count=24,
                    ),
                    ReliabilityMetric(
                        id=2,
                        route_id=1,
                        metric_date=date(2026, 3, 2),
                        time_band="evening_peak",
                        avg_delay_minutes=5.1,
                        on_time_rate=0.65,
                        cancellation_rate=0.08,
                        observation_count=18,
                    ),
                ]
            )

        if db.query(Incident).count() == 0:
            db.add(
                Incident(
                    title="Roadworks near stop",
                    description="Temporary congestion caused by roadworks close to Headingley.",
                    incident_type="delay",
                    severity="medium",
                    status="open",
                    route_id=1,
                    stop_id=2,
                )
            )

        db.commit()
        print("Seeded demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
