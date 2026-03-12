from datetime import date
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Incident, Operator, ReliabilityMetric, Route, RouteStop, Stop


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add(Operator(id=1, noc="LDS1", name="Leeds City Buses", region="Leeds"))
    db.add(
        Route(
            id=1,
            operator_id=1,
            route_code="1",
            route_name="City Centre to Headingley",
            origin="Leeds City Centre",
            destination="Headingley",
        )
    )
    db.add(Stop(id=1, stop_code="STOP100", stop_name="Leeds Station", locality="Leeds", latitude=53.794, longitude=-1.548))
    db.add(Stop(id=2, stop_code="STOP200", stop_name="Headingley Arndale", locality="Headingley", latitude=53.819, longitude=-1.579))
    db.add(RouteStop(route_id=1, stop_id=1, stop_sequence=1))
    db.add(RouteStop(route_id=1, stop_id=2, stop_sequence=2))
    db.add(
        ReliabilityMetric(
            id=1,
            route_id=1,
            metric_date=date(2026, 3, 1),
            time_band="morning_peak",
            avg_delay_minutes=4.0,
            on_time_rate=0.8,
            cancellation_rate=0.05,
            observation_count=20,
        )
    )
    db.add(
        Incident(
            id=1,
            title="Test incident",
            description="Demo record",
            incident_type="delay",
            severity="medium",
            status="open",
            route_id=1,
            stop_id=1,
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
