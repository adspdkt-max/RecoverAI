"""
Analytics API Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    days: int = Query(14, ge=1, le=90, description="Historical range in days"),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated analytics, time-series data points, and recovery metrics.
    """
    return AnalyticsService.get_analytics_summary(db=db, days=days)


@router.get("/recovery")
def get_recovery_analytics(db: Session = Depends(get_db)):
    """
    Returns specific recovery efficiency and intervention success rates.
    """
    summary = AnalyticsService.get_analytics_summary(db=db, days=30)
    return {
        "recovered_revenue": summary.recovered_revenue,
        "revenue_at_risk": summary.revenue_at_risk,
        "recovery_rate": summary.recovery_rate,
        "recovery_attempts": summary.recovery_attempts,
        "recovery_success_rate": summary.recovery_success_rate,
        "interventions": summary.recovery_interventions,
        "intervention_success_rates": summary.intervention_success_rates,
    }


@router.get("/risk")
def get_risk_analytics(db: Session = Depends(get_db)):
    """
    Returns risk profile distribution across all payment events.
    """
    summary = AnalyticsService.get_analytics_summary(db=db, days=30)
    return {
        "risk_distribution": summary.risk_distribution,
        "failure_reasons": summary.failure_reasons,
        "failed_payments": summary.failed_payments,
    }
