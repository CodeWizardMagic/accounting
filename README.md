# Uchet

Uchet - система учета рабочего времени сотрудников. В проекте есть веб-интерфейс для ведения табеля, FastAPI backend, PostgreSQL, Telegram-бот, AI-парсер свободного текста и PDF-отчеты.

## Возможности

- Ведение сотрудников: ФИО, тип оплаты, ставка в тенге за час, примечания.
- Табель учета рабочего времени по месяцам.
- Редактирование часов в таблице прямо в веб-интерфейсе.
- Расчет рабочих дней, общего количества часов и зарплаты в тенге.
- Telegram-бот для внесения часов, добавления сотрудников и получения отчетов.
- AI-команды для распознавания фраз вроде `Олжас сегодня 8 часов`.
- Изменение ставки через бота, например `Олжас изменил зарплату на 15 тысяч в час`.
- PDF-файл с таблицей `Табель учета рабочего времени`.

## Технологии

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic.
- Frontend: React, TypeScript, Vite, Ant Design.
- Database: PostgreSQL 17.
- Bot: Aiogram 3.
- AI provider: Groq.
- PDF: ReportLab.
- Runtime: Docker Compose.

## Быстрый запуск

1. Создайте `.env` в корне проекта:

```env
POSTGRES_DB=timesheet_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/timesheet_db
BACKEND_CORS_ORIGINS=http://localhost:5180,http://127.0.0.1:5180
BACKEND_CORS_ORIGIN_REGEX=http://.*:5180

TELEGRAM_BOT_TOKEN=
AI_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

2. Запустите сервисы:

```bash
docker compose up -d --build
```

Backend при старте дождется PostgreSQL и применит Alembic-миграции.

## Адреса

- Веб-интерфейс: http://localhost:5180
- Backend API: http://localhost:8010
- Swagger: http://localhost:8010/docs

## Docker-сервисы

- `timesheet_postgres` - PostgreSQL с volume `postgres_data`.
- `timesheet_backend` - FastAPI API и миграции.
- `timesheet_frontend` - React-приложение.
- `timesheet_telegram_bot` - Telegram-бот.

Полезные команды:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f telegram_bot
docker compose down
```

## Telegram-бот

Основные команды:

- `/start` - зарегистрировать пользователя.
- `/help` - показать список команд.
- `/employees` - список сотрудников со ставками.
- `/add_employee` - пошагово добавить сотрудника.
- `/add_employee Умаров Олжас; 15000` - добавить сотрудника сразу.
- `/hours` - пошагово внести часы.
- `/ai <текст>` - распознать свободный текст или изменить ставку.
- `/report <вопрос>` - получить текстовый отчет.
- `/timesheet_pdf июнь 2026` - получить PDF-табель за месяц.

Примеры AI-команд:

```text
/ai Олжас сегодня 8 часов
/ai Умаров Олжас 05.06.2026 отработал 7.5 часов
/ai Олжас изменил зарплату на 15 тысяч в час
```

Примеры отчетов:

```text
/report Сколько часов отработал Умаров Олжас за июнь 2026 года?
/report Сколько получит Умаров Олжас за июнь 2026 года?
/report сколько нужно заплатить всем сотрудникам за июнь?
/report сколько часов отработал Олжас за все время?
/report табель учета рабочего времени за июнь 2026 в pdf
```

## PDF-табель

PDF-отчет содержит:

- заголовок `Табель учета рабочего времени`;
- месяц и год;
- сотрудников по строкам;
- дни месяца по колонкам;
- итоговые колонки `Дней`, `Часов`, `Зарплата, ₸`.

PDF можно запросить отдельной командой:

```text
/timesheet_pdf июнь 2026
```

или через `/report`, если в вопросе есть `табель`, `pdf` или `пдф`.

## Форматы и валюта

- Дата в боте вводится в формате `ДД.ММ.ГГГГ` или словом `сегодня`.
- Ставки и зарплата отображаются в тенге: `₸`.
- Почасовая ставка отображается как `₸/час`.
- Внутренние значения API для типа оплаты остаются `hourly`, `shift`, `fixed`, но в интерфейсе показываются как `Почасово`, `Посменно`, `Фиксированно`.

## Локальная разработка

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend без Docker требует PostgreSQL и переменную `DATABASE_URL`:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Проверки:

```bash
cd frontend
npm run build
```

```bash
python -m compileall backend bot
```

## Структура проекта

```text
backend/   FastAPI, SQLAlchemy, Alembic, схемы, репозитории, сервисы
frontend/  React, TypeScript, Ant Design, Vite
bot/       Aiogram Telegram-бот
database/  SQL-материалы и заметки
docs/      документация проекта
```

## Примечания

- Если бот не отвечает, проверьте `TELEGRAM_BOT_TOKEN` и логи `timesheet_telegram_bot`.
- Если AI-команда не распознается, проверьте `GROQ_API_KEY`.
- После изменения backend или bot-кода пересоберите и перезапустите контейнеры:

```bash
docker compose build backend telegram_bot
docker compose up -d backend telegram_bot
```
