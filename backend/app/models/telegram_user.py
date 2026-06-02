from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TelegramUserRole(StrEnum):
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[TelegramUserRole] = mapped_column(Enum(TelegramUserRole, name="telegram_user_role"), default=TelegramUserRole.manager)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
