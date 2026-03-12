from fastapi import FastAPI

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Incident, Operator, ReliabilityMetric, Route, RouteStop, Stop  # noqa: F401
from app.routers.analytics import router as analytics_router
from app.routers.incidents import router as incidents_router
from app.routers.operators import router as operators_router
from app.routers.routes import router as routes_router
from app.routers.stops import router as stops_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Public read API for Leeds bus routes and reliability metrics, with API key protected incident writes.",
    )

    Base.metadata.create_all(bind=engine)

    app.include_router(operators_router)
    app.include_router(routes_router)
    app.include_router(stops_router)
    app.include_router(incidents_router)
    app.include_router(analytics_router)
    return app


app = create_app()
