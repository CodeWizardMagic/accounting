import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.employee_repository import EmployeeRepository
from app.repositories.timesheet_repository import TimesheetRepository
from app.schemas.timesheet import TimesheetEntryCreate, TimesheetSummaryRow


class TimesheetService:
    def __init__(self, db: Session) -> None:
        self.employees = EmployeeRepository(db)
        self.timesheet = TimesheetRepository(db)

    def month_range(self, year: int, month: int) -> tuple[date, date]:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)

    def monthly_summary(self, year: int, month: int) -> list[TimesheetSummaryRow]:
        start, end = self.month_range(year, month)
        employees = self.employees.list()
        entries = self.timesheet.list(date_from=start, date_to=end)
        by_employee_day = {(entry.employee_id, entry.work_date.day): entry.hours_worked for entry in entries}
        days_count = calendar.monthrange(year, month)[1]

        result: list[TimesheetSummaryRow] = []
        for employee in employees:
            days = {str(day): Decimal(by_employee_day.get((employee.id, day), 0)) for day in range(1, days_count + 1)}
            total_hours = sum(days.values(), Decimal(0))
            working_days = sum(1 for hours in days.values() if hours > 0)
            estimated_salary = total_hours * employee.hourly_rate if employee.payment_type == "hourly" else Decimal(0)
            result.append(
                TimesheetSummaryRow(
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    payment_type=str(employee.payment_type),
                    hourly_rate=employee.hourly_rate,
                    days=days,
                    working_days=working_days,
                    total_hours=total_hours,
                    estimated_salary=estimated_salary,
                )
            )
        return result

    def upsert_cell(self, data: TimesheetEntryCreate):
        return self.timesheet.upsert(data)
