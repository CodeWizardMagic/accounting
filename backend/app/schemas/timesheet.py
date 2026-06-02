from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee import EmployeeRead


class TimesheetEntryBase(BaseModel):
    employee_id: int
    work_date: date
    hours_worked: Decimal = Field(ge=0, le=24)
    comment: str | None = None


class TimesheetEntryCreate(TimesheetEntryBase):
    pass


class TimesheetEntryUpdate(BaseModel):
    employee_id: int | None = None
    work_date: date | None = None
    hours_worked: Decimal | None = Field(default=None, ge=0, le=24)
    comment: str | None = None


class TimesheetEntryRead(TimesheetEntryBase):
    id: int
    created_at: datetime
    employee: EmployeeRead | None = None

    model_config = ConfigDict(from_attributes=True)


class TimesheetCellUpsert(BaseModel):
    employee_id: int
    work_date: date
    hours_worked: Decimal = Field(ge=0, le=24)
    comment: str | None = None


class TimesheetSummaryRow(BaseModel):
    employee_id: int
    employee_name: str
    payment_type: str
    hourly_rate: Decimal
    days: dict[str, Decimal]
    working_days: int
    total_hours: Decimal
    estimated_salary: Decimal
