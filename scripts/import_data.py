from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Incident, Operator, ReliabilityMetric, Route, RouteStop, Stop


PROCESSED_DIR = Path("data/processed")


def read_csv(filename: str) -> list[dict]:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(Incident).delete()
        db.query(RouteStop).delete()
        db.query(ReliabilityMetric).delete()
        db.query(Route).delete()
        db.query(Stop).delete()
        db.query(Operator).delete()
        db.commit()

        for row in read_csv("operators.csv"):
            db.add(
                Operator(
                    id=int(row["id"]),
                    noc=row["noc"],
                    name=row["name"],
                    region=row.get("region") or "Leeds",
                )
            )

        for row in read_csv("routes.csv"):
            db.add(
                Route(
                    id=int(row["id"]),
                    operator_id=int(row["operator_id"]),
                    route_code=row["route_code"],
                    route_name=row["route_name"],
                    origin=row.get("origin") or None,
                    destination=row.get("destination") or None,
                )
            )

        for row in read_csv("stops.csv"):
            db.add(
                Stop(
                    id=int(row["id"]),
                    stop_code=row["stop_code"],
                    stop_name=row["stop_name"],
                    locality=row.get("locality") or None,
                    latitude=float(row["latitude"]) if row.get("latitude") else None,
                    longitude=float(row["longitude"]) if row.get("longitude") else None,
                )
            )

        db.flush()

        for row in read_csv("route_stops.csv"):
            db.add(
                RouteStop(
                    route_id=int(row["route_id"]),
                    stop_id=int(row["stop_id"]),
                    stop_sequence=int(row["stop_sequence"]),
                )
            )

        for row in read_csv("reliability_metrics.csv"):
            db.add(
                ReliabilityMetric(
                    id=int(row["id"]),
                    route_id=int(row["route_id"]),
                    metric_date=date.fromisoformat(row["metric_date"]),
                    time_band=row["time_band"],
                    avg_delay_minutes=float(row["avg_delay_minutes"]),
                    on_time_rate=float(row["on_time_rate"]),
                    cancellation_rate=float(row["cancellation_rate"]),
                    observation_count=int(row["observation_count"]),
                )
            )

        db.commit()
        print("Imported processed CSV files into SQLite.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
