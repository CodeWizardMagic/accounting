import calendar
import re
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.timesheet_entry import TimesheetEntry
from app.schemas.report import ReportResponse

MONTH_PATTERNS = [
    (r"\bянвар", 1),
    (r"\bфеврал", 2),
    (r"\bмарт", 3),
    (r"\bапрел", 4),
    (r"\bма[йя]\b", 5),
    (r"\bиюн", 6),
    (r"\bиюл", 7),
    (r"\bавгуст", 8),
    (r"\bсентябр", 9),
    (r"\bоктябр", 10),
    (r"\bноябр", 11),
    (r"\bдекабр", 12),
]


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def answer(self, question: str) -> ReportResponse:
        lowered = question.lower()
        start, end = self._extract_period(lowered)

        if "больше всех" in lowered:
            return self._top_employee(start, end)
        if "менее" in lowered:
            threshold = self._extract_number(lowered) or Decimal(80)
            return self._less_than(start, end, threshold)
        if any(token in lowered for token in ("получит", "зарплат", "оплат", "заплат", "начисл")):
            if any(token in lowered for token in ("всем", "все сотрудники", "всех сотрудников", "каждому")):
                return self._all_employees_salary(start, end)
            return self._employee_salary(lowered, start, end)
        return self._employee_hours(lowered, start, end)

    def _employee_hours(self, question: str, start: date | None, end: date | None) -> ReportResponse:
        employee = self._find_employee_in_question(question)
        if not employee:
            return ReportResponse(title="Отчет", rows=[], message="Сотрудник не найден в вопросе.")

        total = self._employee_total_hours(employee.id, start, end)
        return ReportResponse(
            title=f"Часы сотрудника: {employee.full_name}",
            rows=[{"employee": employee.full_name, "hours": Decimal(total)}],
            message=f"{employee.full_name}: {Decimal(total)} часов.",
        )

    def _employee_salary(self, question: str, start: date | None, end: date | None) -> ReportResponse:
        employee = self._find_employee_in_question(question)
        if not employee:
            return ReportResponse(title="Отчет", rows=[], message="Сотрудник не найден в вопросе.")

        total_hours = self._employee_total_hours(employee.id, start, end)
        salary = total_hours * employee.hourly_rate if employee.payment_type == "hourly" else Decimal(0)
        return ReportResponse(
            title=f"Зарплата сотрудника: {employee.full_name}",
            rows=[{"employee": employee.full_name, "hours": total_hours, "salary": salary}],
            message=(
                f"{employee.full_name}: {self._format_decimal(salary)} ₸ "
                f"({self._format_decimal(total_hours)} часов × {self._format_decimal(employee.hourly_rate)} ₸/час)."
            ),
        )

    def _all_employees_salary(self, start: date | None, end: date | None) -> ReportResponse:
        rows = []
        total_salary = Decimal(0)

        employees = list(self.db.scalars(select(Employee).order_by(Employee.full_name)))
        for employee in employees:
            total_hours = self._employee_total_hours(employee.id, start, end)
            salary = total_hours * employee.hourly_rate if employee.payment_type == "hourly" else Decimal(0)
            total_salary += salary
            if total_hours > 0 or salary > 0:
                rows.append({"employee": employee.full_name, "hours": total_hours, "salary": salary})

        details = "\n".join(
            f"{row['employee']}: {self._format_decimal(row['salary'])} ₸ "
            f"({self._format_decimal(row['hours'])} часов)"
            for row in rows
        )
        message = f"Всего к выплате: {self._format_decimal(total_salary)} ₸."
        if details:
            message += "\n\n" + details
        return ReportResponse(title="Зарплата всех сотрудников", rows=rows, message=message)

    def _top_employee(self, start: date | None, end: date | None) -> ReportResponse:
        conditions = self._timesheet_period_conditions(start, end)
        stmt = (
            select(Employee.full_name, func.coalesce(func.sum(TimesheetEntry.hours_worked), 0).label("hours"))
            .join(TimesheetEntry, TimesheetEntry.employee_id == Employee.id)
            .group_by(Employee.id)
            .order_by(func.sum(TimesheetEntry.hours_worked).desc())
            .limit(1)
        )
        if conditions:
            stmt = stmt.where(*conditions)
        row = self.db.execute(stmt).first()
        rows = [{"employee": row.full_name, "hours": Decimal(row.hours)}] if row else []
        message = f"Больше всех работал {row.full_name}: {Decimal(row.hours)} часов." if row else "Нет данных за период."
        return ReportResponse(title="Лидер по часам", rows=rows, message=message)

    def _less_than(self, start: date | None, end: date | None, threshold: Decimal) -> ReportResponse:
        join_condition = TimesheetEntry.employee_id == Employee.id
        if start:
            join_condition = join_condition & (TimesheetEntry.work_date >= start)
        if end:
            join_condition = join_condition & (TimesheetEntry.work_date <= end)
        stmt = (
            select(Employee.full_name, func.coalesce(func.sum(TimesheetEntry.hours_worked), 0).label("hours"))
            .outerjoin(TimesheetEntry, join_condition)
            .group_by(Employee.id)
            .having(func.coalesce(func.sum(TimesheetEntry.hours_worked), 0) < threshold)
            .order_by(Employee.full_name)
        )
        rows = [{"employee": name, "hours": Decimal(hours)} for name, hours in self.db.execute(stmt)]
        return ReportResponse(title=f"Сотрудники менее {threshold} часов", rows=rows, message=f"Найдено сотрудников: {len(rows)}.")

    def _extract_period(self, question: str) -> tuple[date | None, date | None]:
        if any(phrase in question for phrase in ("за все время", "за всё время", "все время", "всё время", "за весь период")):
            return None, None
        year, month = self._extract_month(question)
        return self._month_range(year, month)

    def _extract_month(self, question: str) -> tuple[int, int]:
        current = date.today()
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", question)
        year = int(year_match.group(1)) if year_match else current.year
        for pattern, month in MONTH_PATTERNS:
            if re.search(pattern, question):
                return year, month
        return year, current.month

    def _month_range(self, year: int, month: int) -> tuple[date, date]:
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])

    def _extract_number(self, question: str) -> Decimal | None:
        match = re.search(r"\d+(?:[.,]\d+)?", question)
        return Decimal(match.group(0).replace(",", ".")) if match else None

    def _employee_total_hours(self, employee_id: int, start: date | None, end: date | None) -> Decimal:
        conditions = [TimesheetEntry.employee_id == employee_id, *self._timesheet_period_conditions(start, end)]
        total = self.db.scalar(select(func.coalesce(func.sum(TimesheetEntry.hours_worked), 0)).where(*conditions))
        return Decimal(total)

    def _timesheet_period_conditions(self, start: date | None, end: date | None):
        conditions = []
        if start:
            conditions.append(TimesheetEntry.work_date >= start)
        if end:
            conditions.append(TimesheetEntry.work_date <= end)
        return conditions

    def _find_employee_in_question(self, question: str) -> Employee | None:
        employees = list(self.db.scalars(select(Employee).order_by(Employee.full_name)))
        words = set(re.findall(r"[а-яa-zё]+", question.lower()))
        best_employee = None
        best_score = 0

        for employee in employees:
            name_words = set(re.findall(r"[а-яa-zё]+", employee.full_name.lower()))
            score = len(name_words & words)
            if employee.full_name.lower() in question:
                score += 10
            if score > best_score:
                best_employee = employee
                best_score = score

        return best_employee if best_score > 0 else None

    def _format_decimal(self, value: Decimal) -> str:
        normalized = value.quantize(Decimal("1")) if value == value.to_integral() else value.normalize()
        return f"{normalized:,}".replace(",", " ")
