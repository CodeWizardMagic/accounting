from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError


class NotFoundError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Database error", "error": str(exc)})
