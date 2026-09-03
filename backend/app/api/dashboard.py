"""
Dashboard Summary API Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Computes and returns real-time dashboard KPIs directly from database tables.
    Returns clean zeros and empty collections if no data exists.
    """
    return AnalyticsService.get_dashboard_summary(db)
