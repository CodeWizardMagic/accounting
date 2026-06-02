from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_timesheet_employee_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    hours_worked: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="timesheet_entries")
