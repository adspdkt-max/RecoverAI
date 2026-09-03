"""
Analytics Service

Computes real-time, zero-hardcoding aggregation metrics directly from the database.
"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.analytics import AnalyticsSummaryResponse, TimeSeriesPoint
from app.schemas.payment import PaymentResponse
from app.schemas.recovery import RecoveryAttemptResponse


class AnalyticsService:
    @staticmethod
    def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
        """
        Calculates real-time dashboard KPIs from database tables.
        """
        total_payments = db.query(func.count(Payment.id)).scalar() or 0
        failed_payments = db.query(func.count(Payment.id)).filter(Payment.status == "FAILED").scalar() or 0
        successful_payments = db.query(func.count(Payment.id)).filter(Payment.status == "CAPTURED").scalar() or 0

        # Revenue at risk: sum of amounts for all current FAILED payments
        revenue_at_risk = (
            db.query(func.sum(Payment.amount)).filter(Payment.status == "FAILED").scalar() or 0.0
        )

        # Recovered revenue: sum of recovered_amount for all SUCCEEDED recovery attempts
        recovered_revenue = (
            db.query(func.sum(RecoveryAttempt.recovered_amount))
            .filter(RecoveryAttempt.status == "SUCCEEDED")
            .scalar()
            or 0.0
        )

        # Active recovery attempts in flight
        active_attempts = (
            db.query(func.count(RecoveryAttempt.id))
            .filter(RecoveryAttempt.status == "PENDING")
            .scalar()
            or 0
        )

        # Human escalations count
        human_escalations = (
            db.query(func.count(RecoveryAttempt.id))
            .filter(
                (RecoveryAttempt.status == "ESCALATED")
                | (RecoveryAttempt.intervention == "HUMAN_ESCALATION")
            )
            .scalar()
            or 0
        )

        # Recovery rate calculation
        total_at_stake = revenue_at_risk + recovered_revenue
        recovery_rate = (recovered_revenue / total_at_stake * 100.0) if total_at_stake > 0 else 0.0

        # Risk distribution
        risk_rows = (
            db.query(Payment.risk_level, func.count(Payment.id))
            .filter(Payment.risk_level.isnot(None))
            .group_by(Payment.risk_level)
            .all()
        )
        risk_distribution: Dict[str, int] = {row[0]: row[1] for row in risk_rows if row[0]}

        # Payment status distribution
        status_rows = db.query(Payment.status, func.count(Payment.id)).group_by(Payment.status).all()
        status_distribution: Dict[str, int] = {row[0]: row[1] for row in status_rows if row[0]}

        # Intervention distribution
        int_rows = (
            db.query(RecoveryAttempt.intervention, func.count(RecoveryAttempt.id))
            .group_by(RecoveryAttempt.intervention)
            .all()
        )
        intervention_distribution: Dict[str, int] = {row[0]: row[1] for row in int_rows if row[0]}

        # Recent 5 payments and 5 attempts
        recent_payments = (
            db.query(Payment).order_by(Payment.created_at.desc()).limit(5).all()
        )
        recent_attempts = (
            db.query(RecoveryAttempt).order_by(RecoveryAttempt.created_at.desc()).limit(5).all()
        )

        return DashboardSummaryResponse(
            revenue_at_risk=round(revenue_at_risk, 2),
            recovered_revenue=round(recovered_revenue, 2),
            recovery_rate=round(recovery_rate, 1),
            active_attempts=active_attempts,
            total_payments=total_payments,
            failed_payments=failed_payments,
            successful_payments=successful_payments,
            human_escalations=human_escalations,
            currency="INR",
            risk_distribution=risk_distribution,
            payment_status_distribution=status_distribution,
            intervention_distribution=intervention_distribution,
            recent_payments=[PaymentResponse.model_validate(p) for p in recent_payments],
            recent_recovery_attempts=[RecoveryAttemptResponse.model_validate(a) for a in recent_attempts],
        )

    @staticmethod
    def get_analytics_summary(db: Session, days: int = 14) -> AnalyticsSummaryResponse:
        """
        Calculates deep historical metrics, time-series data, and intervention efficacy.
        """
        dashboard = AnalyticsService.get_dashboard_summary(db)
        total_attempts = db.query(func.count(RecoveryAttempt.id)).scalar() or 0
        succeeded_attempts = (
            db.query(func.count(RecoveryAttempt.id))
            .filter(RecoveryAttempt.status == "SUCCEEDED")
            .scalar()
            or 0
        )
        success_rate = (succeeded_attempts / total_attempts * 100.0) if total_attempts > 0 else 0.0

        total_volume = db.query(func.sum(Payment.amount)).scalar() or 0.0

        # Build Daily Time-Series Buckets for the last N days
        now = datetime.utcnow()
        start_date = now - timedelta(days=days - 1)

        # Query daily failed amounts
        failed_by_date = (
            db.query(
                func.strftime("%Y-%m-%d", Payment.created_at).label("day"),
                func.sum(Payment.amount).label("amt"),
                func.count(Payment.id).label("cnt"),
            )
            .filter(Payment.created_at >= start_date, Payment.status == "FAILED")
            .group_by("day")
            .all()
        )
        failed_map = {row[0]: (float(row[1] or 0.0), int(row[2] or 0)) for row in failed_by_date}

        # Query daily recovered amounts
        recovered_by_date = (
            db.query(
                func.strftime("%Y-%m-%d", RecoveryAttempt.completed_at).label("day"),
                func.sum(RecoveryAttempt.recovered_amount).label("amt"),
                func.count(RecoveryAttempt.id).label("cnt"),
            )
            .filter(
                RecoveryAttempt.completed_at.isnot(None),
                RecoveryAttempt.completed_at >= start_date,
                RecoveryAttempt.status == "SUCCEEDED",
            )
            .group_by("day")
            .all()
        )
        recovered_map = {row[0]: (float(row[1] or 0.0), int(row[2] or 0)) for row in recovered_by_date}

        risk_series: List[TimeSeriesPoint] = []
        recovered_series: List[TimeSeriesPoint] = []

        for i in range(days):
            d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            f_amt, f_cnt = failed_map.get(d, (0.0, 0))
            r_amt, r_cnt = recovered_map.get(d, (0.0, 0))

            risk_series.append(TimeSeriesPoint(date=d, amount=round(f_amt, 2), count=f_cnt))
            recovered_series.append(TimeSeriesPoint(date=d, amount=round(r_amt, 2), count=r_cnt))

        # Failure reasons breakdown
        reason_rows = (
            db.query(Payment.failure_code, func.count(Payment.id))
            .filter(Payment.failure_code.isnot(None), Payment.failure_code != "")
            .group_by(Payment.failure_code)
            .all()
        )
        failure_reasons = {row[0]: row[1] for row in reason_rows if row[0]}

        # Intervention Success Rates
        intervention_rates: Dict[str, float] = {}
        all_interventions = (
            db.query(RecoveryAttempt.intervention, func.count(RecoveryAttempt.id))
            .group_by(RecoveryAttempt.intervention)
            .all()
        )
        for intervention_name, count_total in all_interventions:
            if not intervention_name:
                continue
            succeeded_count = (
                db.query(func.count(RecoveryAttempt.id))
                .filter(
                    RecoveryAttempt.intervention == intervention_name,
                    RecoveryAttempt.status == "SUCCEEDED",
                )
                .scalar()
                or 0
            )
            rate = round((succeeded_count / count_total * 100.0), 1) if count_total > 0 else 0.0
            intervention_rates[intervention_name] = rate

        return AnalyticsSummaryResponse(
            revenue_at_risk=dashboard.revenue_at_risk,
            recovered_revenue=dashboard.recovered_revenue,
            recovery_rate=dashboard.recovery_rate,
            recovery_attempts=total_attempts,
            recovery_success_rate=round(success_rate, 1),
            failed_payments=dashboard.failed_payments,
            total_payments=dashboard.total_payments,
            total_volume=round(total_volume, 2),
            currency="INR",
            revenue_at_risk_over_time=risk_series,
            recovered_revenue_over_time=recovered_series,
            payment_status=dashboard.payment_status_distribution,
            risk_distribution=dashboard.risk_distribution,
            recovery_interventions=dashboard.intervention_distribution,
            failure_reasons=failure_reasons,
            intervention_success_rates=intervention_rates,
        )
