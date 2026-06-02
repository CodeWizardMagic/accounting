from datetime import date

from pydantic import ValidationError

from app.schemas.ai import ParsedTimesheetSchema
from app.services.ai_provider import get_ai_provider


SYSTEM_PROMPT = """
You convert Russian/Kazakh work-time messages into JSON.
Return only JSON matching this schema:
{"entries":[{"employee_name":"string","date":"YYYY-MM-DD","hours":number}]}
Rules:
- If date is absent, use the provided current date.
- If an employee appears several times for the same date, combine hours into one entry.
- Do not invent employees.
- Use numeric hours only.
"""


async def parse_work_message(text: str, current_date: date | None = None) -> ParsedTimesheetSchema:
    provider = get_ai_provider()
    today = current_date or date.today()
    user_prompt = f"Current date: {today.isoformat()}\nMessage: {text}"
    last_error: Exception | None = None

    for _ in range(2):
        try:
            data = await provider.generate_json(SYSTEM_PROMPT, user_prompt)
            parsed = ParsedTimesheetSchema.model_validate(data)
            return _merge_duplicates(parsed)
        except (ValidationError, ValueError, KeyError) as exc:
            last_error = exc
            user_prompt += "\nPrevious response was invalid. Return valid JSON only."

    raise ValueError(f"Could not parse model response: {last_error}")


def _merge_duplicates(parsed: ParsedTimesheetSchema) -> ParsedTimesheetSchema:
    merged: dict[tuple[str, date], object] = {}
    for entry in parsed.entries:
        key = (entry.employee_name.strip(), entry.date)
        if key in merged:
            merged[key].hours += entry.hours
        else:
            merged[key] = entry.model_copy(update={"employee_name": entry.employee_name.strip()})
    return ParsedTimesheetSchema(entries=list(merged.values()))
