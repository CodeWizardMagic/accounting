from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.timesheet_entry import TimesheetEntry
from app.schemas.timesheet import TimesheetEntryCreate, TimesheetEntryUpdate


class TimesheetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        employee_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[TimesheetEntry]:
        stmt = select(TimesheetEntry).options(joinedload(TimesheetEntry.employee)).order_by(TimesheetEntry.work_date, TimesheetEntry.employee_id)
        if employee_id:
            stmt = stmt.where(TimesheetEntry.employee_id == employee_id)
        if date_from:
            stmt = stmt.where(TimesheetEntry.work_date >= date_from)
        if date_to:
            stmt = stmt.where(TimesheetEntry.work_date <= date_to)
        return list(self.db.scalars(stmt))

    def get(self, entry_id: int) -> TimesheetEntry | None:
        return self.db.get(TimesheetEntry, entry_id)

    def get_by_employee_date(self, employee_id: int, work_date: date) -> TimesheetEntry | None:
        return self.db.scalar(select(TimesheetEntry).where(TimesheetEntry.employee_id == employee_id, TimesheetEntry.work_date == work_date))

    def create(self, data: TimesheetEntryCreate) -> TimesheetEntry:
        entry = TimesheetEntry(**data.model_dump())
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: TimesheetEntry, data: TimesheetEntryUpdate) -> TimesheetEntry:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def upsert(self, data: TimesheetEntryCreate) -> TimesheetEntry:
        entry = self.get_by_employee_date(data.employee_id, data.work_date)
        if entry:
            entry.hours_worked = data.hours_worked
            entry.comment = data.comment
            self.db.commit()
            self.db.refresh(entry)
            return entry
        return self.create(data)

    def delete(self, entry: TimesheetEntry) -> None:
        self.db.delete(entry)
        self.db.commit()
