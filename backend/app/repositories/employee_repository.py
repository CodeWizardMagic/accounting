from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, search: str | None = None) -> list[Employee]:
        stmt = select(Employee).order_by(Employee.id)
        if search:
            stmt = stmt.where(Employee.full_name.ilike(f"%{search}%"))
        return list(self.db.scalars(stmt))

    def get(self, employee_id: int) -> Employee | None:
        return self.db.get(Employee, employee_id)

    def find_by_name(self, name: str) -> Employee | None:
        return self.db.scalar(select(Employee).where(Employee.full_name.ilike(f"%{name}%")).limit(1))

    def create(self, data: EmployeeCreate) -> Employee:
        employee = Employee(**data.model_dump())
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update(self, employee: Employee, data: EmployeeUpdate) -> Employee:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(employee, field, value)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete(self, employee: Employee) -> None:
        self.db.delete(employee)
        self.db.commit()
