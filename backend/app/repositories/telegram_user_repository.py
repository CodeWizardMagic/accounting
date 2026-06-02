from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.telegram_user import TelegramUser, TelegramUserRole


class TelegramUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, telegram_id: int, username: str | None, full_name: str | None) -> TelegramUser:
        user = self.db.scalar(select(TelegramUser).where(TelegramUser.telegram_id == telegram_id))
        if user:
            user.username = username
            user.full_name = full_name
            self.db.commit()
            self.db.refresh(user)
            return user

        user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=TelegramUserRole.manager,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
