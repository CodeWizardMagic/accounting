from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ParsedTimesheetEntrySchema(BaseModel):
    employee_name: str = Field(min_length=1)
    date: date
    hours: Decimal = Field(ge=0, le=24)


class ParsedTimesheetSchema(BaseModel):
    entries: list[ParsedTimesheetEntrySchema]
