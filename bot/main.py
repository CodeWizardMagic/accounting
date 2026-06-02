import asyncio
import logging
import re
from datetime import date, datetime
from decimal import Decimal

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.telegram_user_repository import TelegramUserRepository
from app.repositories.timesheet_repository import TimesheetRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.timesheet import TimesheetEntryCreate
from app.models.employee import Employee, PaymentType
from app.services.ai_parser import parse_work_message
from app.services.reports import ReportService
from app.services.timesheet_pdf import TimesheetPdfService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HoursState(StatesGroup):
    employee_id = State()
    work_date = State()
    hours = State()
    confirm = State()


class AIState(StatesGroup):
    confirm = State()


class AddEmployeeState(StatesGroup):
    full_name = State()
    hourly_rate = State()


PAYMENT_TYPE_LABELS = {
    "hourly": "Почасово",
    "shift": "Посменно",
    "fixed": "Фиксированно",
}


def db_session():
    return SessionLocal()


async def register_user(message: Message) -> None:
    if not message.from_user:
        return
    with db_session() as db:
        TelegramUserRepository(db).get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )


async def start(message: Message) -> None:
    await register_user(message)
    await message.answer("Вы зарегистрированы. Используйте /help для списка команд.")


async def help_command(message: Message) -> None:
    await message.answer(
        "/employees - список сотрудников\n"
        "/add_employee - добавить сотрудника\n"
        "/hours - пошагово внести часы\n"
        "/ai Олжас сегодня 8 часов - распознать текст\n"
        "/ai Олжас изменил зарплату на 15 тысяч в час - изменить ставку\n"
        "/timesheet_pdf июнь 2026 - табель в PDF\n"
        "/report Сколько получит Олжас за июнь 2026 года?\n"
        "/report табель учета рабочего времени за июнь 2026 в pdf\n"
        "/report Сколько часов отработал Олжас за июнь?"
    )


async def employees(message: Message) -> None:
    await register_user(message)
    with db_session() as db:
        rows = EmployeeRepository(db).list()
    if not rows:
        await message.answer("Сотрудники пока не созданы.")
        return
    await message.answer(
        "\n".join(
            f"{item.id}. {item.full_name} - {PAYMENT_TYPE_LABELS.get(str(item.payment_type), item.payment_type)}, "
            f"{format_decimal(item.hourly_rate)} ₸/час"
            for item in rows
        )
    )


async def hours_start(message: Message, state: FSMContext) -> None:
    await register_user(message)
    with db_session() as db:
        rows = EmployeeRepository(db).list()
    if not rows:
        await message.answer("Сначала создайте сотрудников в веб-интерфейсе.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=item.full_name, callback_data=f"emp:{item.id}")] for item in rows]
    )
    await state.set_state(HoursState.employee_id)
    await message.answer("Выберите сотрудника:", reply_markup=keyboard)


async def select_employee(callback: CallbackQuery, state: FSMContext) -> None:
    employee_id = int(callback.data.split(":")[1])
    await state.update_data(employee_id=employee_id)
    await state.set_state(HoursState.work_date)
    await callback.message.answer("Введите дату в формате ДД.ММ.ГГГГ или слово сегодня:")
    await callback.answer()


async def enter_date(message: Message, state: FSMContext) -> None:
    text = message.text.strip().lower()
    try:
        work_date = parse_user_date(text)
    except ValueError:
        await message.answer("Не понял дату. Введите ДД.ММ.ГГГГ или сегодня.")
        return
    await state.update_data(work_date=work_date.isoformat())
    await state.set_state(HoursState.hours)
    await message.answer("Введите количество часов:")


async def enter_hours(message: Message, state: FSMContext) -> None:
    try:
        hours = Decimal(message.text.replace(",", "."))
    except Exception:
        await message.answer("Введите число, например 8 или 7.5.")
        return
    data = await state.get_data()
    await state.update_data(hours=str(hours))
    await state.set_state(HoursState.confirm)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Подтвердить", callback_data="hours:confirm"), InlineKeyboardButton(text="Отмена", callback_data="hours:cancel")]]
    )
    await message.answer(f"Сохранить запись?\nСотрудник ID: {data['employee_id']}\nДата: {data['work_date']}\nЧасы: {hours}", reply_markup=keyboard)


async def confirm_hours(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "hours:cancel":
        await state.clear()
        await callback.message.answer("Отменено.")
        await callback.answer()
        return
    data = await state.get_data()
    with db_session() as db:
        TimesheetRepository(db).upsert(
            TimesheetEntryCreate(
                employee_id=int(data["employee_id"]),
                work_date=date.fromisoformat(data["work_date"]),
                hours_worked=Decimal(data["hours"]),
                comment="Telegram",
            )
        )
    await state.clear()
    await callback.message.answer("Запись сохранена.")
    await callback.answer()


async def ai_command(message: Message, state: FSMContext) -> None:
    await register_user(message)
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer("Напишите текст после команды, например: /ai Олжас сегодня 8 часов")
        return

    salary_answer = handle_salary_update(text)
    if salary_answer:
        await message.answer(salary_answer)
        return

    try:
        parsed = await parse_work_message(text)
    except Exception as exc:
        logger.exception("AI parse failed")
        await message.answer(f"Не удалось распознать сообщение: {exc}")
        return

    with db_session() as db:
        employee_repo = EmployeeRepository(db)
        prepared = []
        missing = []
        for entry in parsed.entries:
            employee = employee_repo.find_by_name(entry.employee_name)
            if not employee:
                missing.append(entry.employee_name)
            else:
                prepared.append({"employee_id": employee.id, "employee_name": employee.full_name, "date": entry.date.isoformat(), "hours": str(entry.hours)})

    if missing:
        await message.answer("Сотрудник не найден: " + ", ".join(missing))
        return
    if not prepared:
        await message.answer("Не найдено записей для сохранения.")
        return

    await state.update_data(entries=prepared)
    await state.set_state(AIState.confirm)
    lines = [f"✓ {item['employee_name']} - {item['hours']} часов" for item in prepared]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Подтвердить", callback_data="ai:confirm"), InlineKeyboardButton(text="Отмена", callback_data="ai:cancel")]]
    )
    await message.answer("Подтвердите внесение данных:\n\n" + "\n".join(lines) + f"\n\nДата: {prepared[0]['date']}", reply_markup=keyboard)


async def confirm_ai(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "ai:cancel":
        await state.clear()
        await callback.message.answer("Отменено.")
        await callback.answer()
        return
    data = await state.get_data()
    with db_session() as db:
        repo = TimesheetRepository(db)
        for item in data.get("entries", []):
            repo.upsert(
                TimesheetEntryCreate(
                    employee_id=int(item["employee_id"]),
                    work_date=date.fromisoformat(item["date"]),
                    hours_worked=Decimal(item["hours"]),
                    comment="AI Telegram",
                )
            )
    await state.clear()
    await callback.message.answer("Данные сохранены.")
    await callback.answer()


async def add_employee_start(message: Message, state: FSMContext) -> None:
    await register_user(message)
    text = message.text.partition(" ")[2].strip()
    if text:
        answer = create_employee_from_text(text)
        await message.answer(answer)
        return

    await state.set_state(AddEmployeeState.full_name)
    await message.answer("Введите ФИО сотрудника:")


async def add_employee_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer("Введите ФИО минимум из двух символов.")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(AddEmployeeState.hourly_rate)
    await message.answer("Введите ставку в тенге за час:")


async def add_employee_rate(message: Message, state: FSMContext) -> None:
    rate = parse_money(message.text)
    if rate is None:
        await message.answer("Введите ставку числом, например 15000 или 15 тысяч.")
        return
    data = await state.get_data()
    with db_session() as db:
        employee = EmployeeRepository(db).create(
            EmployeeCreate(full_name=data["full_name"], payment_type=PaymentType.hourly, hourly_rate=rate)
        )
    await state.clear()
    await message.answer(f"Сотрудник добавлен: {employee.full_name}, ставка {format_decimal(employee.hourly_rate)} ₸/час.")


async def report_command(message: Message) -> None:
    await register_user(message)
    question = message.text.partition(" ")[2].strip()
    if not question:
        await message.answer("Напишите вопрос после команды /report.")
        return
    if is_timesheet_pdf_request(question):
        await send_timesheet_pdf(message, question)
        return
    with db_session() as db:
        report = ReportService(db).answer(question)
    await message.answer(report.message)


async def timesheet_pdf_command(message: Message) -> None:
    await register_user(message)
    question = message.text.partition(" ")[2].strip()
    await send_timesheet_pdf(message, question)


async def send_timesheet_pdf(message: Message, question: str) -> None:
    with db_session() as db:
        year, month = ReportService(db)._extract_month(question.lower())
        service = TimesheetPdfService(db)
        pdf = service.build_monthly_pdf(year, month)
        file = BufferedInputFile(pdf, filename=service.filename(year, month))
    await message.answer_document(file, caption="Табель учета рабочего времени")


def is_timesheet_pdf_request(question: str) -> bool:
    lowered = question.lower()
    wants_pdf = any(token in lowered for token in ("pdf", "пдф", "файл"))
    wants_timesheet = any(token in lowered for token in ("табель", "учета рабочего времени", "учёта рабочего времени"))
    return wants_pdf or wants_timesheet


def create_employee_from_text(text: str) -> str:
    parts = [part.strip() for part in re.split(r"[;|,]", text, maxsplit=1)]
    if len(parts) < 2:
        return "Укажите ФИО и ставку, например: /add_employee Умаров Олжас; 15000"

    rate = parse_money(parts[1])
    if rate is None:
        return "Не понял ставку. Пример: /add_employee Умаров Олжас; 15000"

    with db_session() as db:
        employee = EmployeeRepository(db).create(EmployeeCreate(full_name=parts[0], payment_type=PaymentType.hourly, hourly_rate=rate))
    return f"Сотрудник добавлен: {employee.full_name}, ставка {format_decimal(employee.hourly_rate)} ₸/час."


def handle_salary_update(text: str) -> str | None:
    lowered = text.lower()
    if not any(token in lowered for token in ("зарплат", "ставк", "оплат")):
        return None
    if not any(token in lowered for token in ("измен", "помен", "постав", "сдел", "обнов")):
        return None

    rate = parse_money(text)
    if rate is None:
        return "Не понял ставку. Напишите, например: /ai Олжас изменил зарплату на 15 тысяч в час"

    with db_session() as db:
        employee = find_employee_in_text(EmployeeRepository(db).list(), text)
        if not employee:
            return "Сотрудник не найден. Укажите имя или фамилию как в списке сотрудников."
        EmployeeRepository(db).update(employee, EmployeeUpdate(payment_type=PaymentType.hourly, hourly_rate=rate))
        return f"Ставка обновлена: {employee.full_name} - {format_decimal(rate)} ₸/час."


def parse_user_date(text: str) -> date:
    if text == "сегодня":
        return date.today()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("Unsupported date format")


def parse_money(text: str) -> Decimal | None:
    lowered = text.lower().replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(тыс|тысяч|тысячи|k)?", lowered)
    if not match:
        return None
    value = Decimal(match.group(1))
    if match.group(2):
        value *= Decimal(1000)
    return value


def find_employee_in_text(employees: list[Employee], text: str) -> Employee | None:
    words = set(re.findall(r"[а-яa-zё]+", text.lower()))
    best_employee = None
    best_score = 0
    for employee in employees:
        name_words = set(re.findall(r"[а-яa-zё]+", employee.full_name.lower()))
        score = len(name_words & words)
        if employee.full_name.lower() in text.lower():
            score += 10
        if score > best_score:
            best_employee = employee
            best_score = score
    return best_employee if best_score > 0 else None


def format_decimal(value: Decimal) -> str:
    normalized = value.quantize(Decimal("1")) if value == value.to_integral() else value.normalize()
    return f"{normalized:,}".replace(",", " ")


async def main() -> None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is empty. Bot is waiting for configuration.")
        while True:
            await asyncio.sleep(3600)
    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(employees, Command("employees"))
    dp.message.register(add_employee_start, Command("add_employee"))
    dp.message.register(add_employee_name, AddEmployeeState.full_name)
    dp.message.register(add_employee_rate, AddEmployeeState.hourly_rate)
    dp.message.register(hours_start, Command("hours"))
    dp.callback_query.register(select_employee, F.data.startswith("emp:"), HoursState.employee_id)
    dp.message.register(enter_date, HoursState.work_date)
    dp.message.register(enter_hours, HoursState.hours)
    dp.callback_query.register(confirm_hours, F.data.startswith("hours:"), HoursState.confirm)
    dp.message.register(ai_command, Command("ai"))
    dp.callback_query.register(confirm_ai, F.data.startswith("ai:"), AIState.confirm)
    dp.message.register(timesheet_pdf_command, Command("timesheet_pdf"))
    dp.message.register(report_command, Command("report"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
