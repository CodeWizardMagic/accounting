from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import ReportRequest, ReportResponse
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
def create_report(payload: ReportRequest, db: Session = Depends(get_db)):
    return ReportService(db).answer(payload.question)
