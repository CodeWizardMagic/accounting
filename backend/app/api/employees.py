from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
def list_employees(search: str | None = Query(default=None), db: Session = Depends(get_db)):
    return EmployeeRepository(db).list(search)


@router.post("", response_model=EmployeeRead, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    return EmployeeRepository(db).create(payload)


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    repo = EmployeeRepository(db)
    employee = repo.get(employee_id)
    if not employee:
        raise NotFoundError("Employee not found")
    return repo.update(employee, payload)


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    repo = EmployeeRepository(db)
    employee = repo.get(employee_id)
    if not employee:
        raise NotFoundError("Employee not found")
    repo.delete(employee)
