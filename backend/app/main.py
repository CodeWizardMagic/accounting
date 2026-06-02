import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import employees, health, reports, timesheet
from app.core.config import settings
from app.core.errors import register_exception_handlers

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Uchet Timesheet API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.backend_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(health.router)
app.include_router(employees.router)
app.include_router(timesheet.router)
app.include_router(reports.router)
