from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.me import router as me_router
from app.routers.schedules import router as schedules_router
from app.routers.tasks import router as tasks_router
from app.routers.technicians import router as technicians_router
from app.routers.units import router as units_router
from app.routers.work_orders import router as work_orders_router


configure_logging()

app = FastAPI(title="Woflo API", version="0.1.0")

# CORS middleware for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://*.up.railway.app",
        "https://*.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(me_router, tags=["auth"])
app.include_router(work_orders_router, tags=["work_orders"])
app.include_router(tasks_router, tags=["tasks"])
app.include_router(units_router, tags=["units"])
app.include_router(technicians_router, tags=["technicians"])
app.include_router(jobs_router, tags=["jobs"])
app.include_router(schedules_router, tags=["schedules"])
