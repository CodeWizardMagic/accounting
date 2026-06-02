from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.employee import PaymentType


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    payment_type: PaymentType
    hourly_rate: Decimal = Field(default=0, ge=0)
    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    payment_type: PaymentType | None = None
    hourly_rate: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
