from decimal import Decimal

from pydantic import BaseModel


class ReportRequest(BaseModel):
    question: str


class ReportResponse(BaseModel):
    title: str
    rows: list[dict[str, str | int | Decimal]]
    message: str
