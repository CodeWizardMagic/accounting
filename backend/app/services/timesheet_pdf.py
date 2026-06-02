import calendar
import os
from datetime import date
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.services.timesheet_service import TimesheetService


MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


class TimesheetPdfService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_monthly_pdf(self, year: int, month: int) -> bytes:
        font_name = self._register_font()
        rows = TimesheetService(self.db).monthly_summary(year, month)
        days_count = calendar.monthrange(year, month)[1]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=8 * mm,
            rightMargin=8 * mm,
            topMargin=8 * mm,
            bottomMargin=8 * mm,
        )
        title_style = ParagraphStyle("Title", fontName=font_name, fontSize=14, leading=18, alignment=1)
        subtitle_style = ParagraphStyle("Subtitle", fontName=font_name, fontSize=9, leading=12, alignment=1)

        data = [["Сотрудник", *[str(day) for day in range(1, days_count + 1)], "Дней", "Часов", "Зарплата, ₸"]]
        for row in rows:
            data.append(
                [
                    row.employee_name,
                    *[self._format_decimal(row.days[str(day)]) for day in range(1, days_count + 1)],
                    str(row.working_days),
                    self._format_decimal(row.total_hours),
                    self._format_decimal(row.estimated_salary),
                ]
            )

        day_width = 6.3 * mm
        col_widths = [48 * mm, *([day_width] * days_count), 11 * mm, 14 * mm, 24 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 5.7),
                    ("FONTSIZE", (0, 0), (-1, 0), 6.2),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172033")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9aa7b7")),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 1.4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 1.4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        story = [
            Paragraph("Табель учета рабочего времени", title_style),
            Paragraph(f"{MONTH_NAMES[month]} {year}", subtitle_style),
            Spacer(1, 5 * mm),
            table,
        ]
        doc.build(story)
        return buffer.getvalue()

    def filename(self, year: int, month: int) -> str:
        return f"timesheet_{year}_{month:02d}.pdf"

    def _register_font(self) -> str:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("UchetFont", path))
                return "UchetFont"
        return "Helvetica"

    def _format_decimal(self, value: Decimal) -> str:
        normalized = value.quantize(Decimal("1")) if value == value.to_integral() else value.normalize()
        return f"{normalized:,}".replace(",", " ")
