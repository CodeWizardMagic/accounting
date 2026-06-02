from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.repositories.timesheet_repository import TimesheetRepository
from app.schemas.timesheet import TimesheetCellUpsert, TimesheetEntryCreate, TimesheetEntryRead, TimesheetEntryUpdate, TimesheetSummaryRow
from app.services.timesheet_service import TimesheetService

router = APIRouter(prefix="/timesheet", tags=["timesheet"])


@router.get("", response_model=list[TimesheetEntryRead])
def list_timesheet(
    employee_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
):
    if year and month:
        date_from, date_to = TimesheetService(db).month_range(year, month)
    return TimesheetRepository(db).list(employee_id=employee_id, date_from=date_from, date_to=date_to)


@router.get("/summary", response_model=list[TimesheetSummaryRow])
def monthly_summary(year: int, month: int = Query(ge=1, le=12), db: Session = Depends(get_db)):
    return TimesheetService(db).monthly_summary(year, month)


@router.post("", response_model=TimesheetEntryRead, status_code=201)
def create_entry(payload: TimesheetEntryCreate, db: Session = Depends(get_db)):
    return TimesheetRepository(db).create(payload)


@router.post("/upsert", response_model=TimesheetEntryRead)
def upsert_entry(payload: TimesheetCellUpsert, db: Session = Depends(get_db)):
    return TimesheetService(db).upsert_cell(TimesheetEntryCreate(**payload.model_dump()))


@router.put("/{entry_id}", response_model=TimesheetEntryRead)
def update_entry(entry_id: int, payload: TimesheetEntryUpdate, db: Session = Depends(get_db)):
    repo = TimesheetRepository(db)
    entry = repo.get(entry_id)
    if not entry:
        raise NotFoundError("Timesheet entry not found")
    return repo.update(entry, payload)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    repo = TimesheetRepository(db)
    entry = repo.get(entry_id)
    if not entry:
        raise NotFoundError("Timesheet entry not found")
    repo.delete(entry)
