# Database

Основная схема БД управляется Alembic-миграциями в `backend/alembic/versions`.

PostgreSQL запускается сервисом `postgres` в Docker Compose и хранит данные в именованном volume `postgres_data`.
