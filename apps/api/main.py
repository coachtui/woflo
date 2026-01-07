from fastapi import FastAPI

from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.routers.me import router as me_router
from app.routers.tasks import router as tasks_router
from app.routers.technicians import router as technicians_router
from app.routers.units import router as units_router
from app.routers.work_orders import router as work_orders_router


configure_logging()

app = FastAPI(title="Woflo API", version="0.1.0")

app.include_router(health_router, tags=["health"])
app.include_router(me_router, tags=["auth"])
app.include_router(work_orders_router, tags=["work_orders"])
app.include_router(tasks_router, tags=["tasks"])
app.include_router(units_router, tags=["units"])
app.include_router(technicians_router, tags=["technicians"])
