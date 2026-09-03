"""
Customers Intelligence API Router
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from app.db.session import get_db
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.models.audit import AuditLog
from app.schemas.customer import (
    CustomerSummary,
    CustomerDetailResponse,
    PaginatedCustomerResponse,
)
from app.schemas.payment import PaymentResponse, AuditLogBrief
from app.schemas.recovery import RecoveryAttemptResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedCustomerResponse)
def list_customers(
    search: Optional[str] = Query(None, description="Search by Customer ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated customer risk profiles, failure counts, and recovery metrics.
    """
    # Group distinct customers
    customer_query = db.query(Payment.customer_id).distinct()
    if search:
        customer_query = customer_query.filter(Payment.customer_id.ilike(f"%{search.strip()}%"))

    total_customers = customer_query.count()
    offset = (page - 1) * limit
    customer_ids = [row[0] for row in customer_query.offset(offset).limit(limit).all()]

    summaries: List[CustomerSummary] = []
    for cid in customer_ids:
        payments = db.query(Payment).filter(Payment.customer_id == cid).all()
        payment_count = len(payments)
        failed_count = sum(1 for p in payments if p.status == "FAILED")
        risk_sum = sum(p.amount for p in payments if p.status == "FAILED")
        
        # Succeeded recoveries for this customer's payments
        payment_ids = [p.payment_id for p in payments]
        recovered_sum = (
            db.query(func.sum(RecoveryAttempt.recovered_amount))
            .filter(
                RecoveryAttempt.payment_id.in_(payment_ids),
                RecoveryAttempt.status == "SUCCEEDED",
            )
            .scalar()
            or 0.0
        )

        has_escalation = (
            db.query(RecoveryAttempt)
            .filter(
                RecoveryAttempt.payment_id.in_(payment_ids),
                (RecoveryAttempt.status == "ESCALATED") | (RecoveryAttempt.intervention == "HUMAN_ESCALATION"),
            )
            .first()
            is not None
        )

        # Determine recovery status badge
        if has_escalation:
            rec_status = "ESCALATED"
        elif risk_sum > 0:
            rec_status = "AT_RISK"
        elif recovered_sum > 0:
            rec_status = "RECOVERED"
        else:
            rec_status = "HEALTHY"

        last_date = max((p.created_at for p in payments), default=None)

        summaries.append(
            CustomerSummary(
                customer_id=cid,
                payment_count=payment_count,
                failed_payments=failed_count,
                recovered_revenue=round(recovered_sum, 2),
                revenue_at_risk=round(risk_sum, 2),
                last_payment_date=last_date,
                recovery_status=rec_status,
                currency="USD",
            )
        )

    total_pages = (total_customers + limit - 1) // limit if total_customers > 0 else 1

    return PaginatedCustomerResponse(
        items=summaries,
        total=total_customers,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer_detail(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns deep customer intelligence: payment history, recovery attempts, and audit timeline.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .order_by(desc(Payment.created_at))
        .all()
    )
    if not payments:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    payment_ids = [p.payment_id for p in payments]
    attempts = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.payment_id.in_(payment_ids))
        .order_by(desc(RecoveryAttempt.created_at))
        .all()
    )

    audits = (
        db.query(AuditLog)
        .filter(or_(AuditLog.customer_id == customer_id, AuditLog.payment_id.in_(payment_ids)))
        .order_by(desc(AuditLog.timestamp))
        .all()
    )

    failed_count = sum(1 for p in payments if p.status == "FAILED")
    risk_sum = sum(p.amount for p in payments if p.status == "FAILED")
    recovered_sum = sum(a.recovered_amount for a in attempts if a.status == "SUCCEEDED")
    has_escalation = any(a.status == "ESCALATED" or a.intervention == "HUMAN_ESCALATION" for a in attempts)

    if has_escalation:
        rec_status = "ESCALATED"
    elif risk_sum > 0:
        rec_status = "AT_RISK"
    elif recovered_sum > 0:
        rec_status = "RECOVERED"
    else:
        rec_status = "HEALTHY"

    return CustomerDetailResponse(
        customer_id=customer_id,
        payment_count=len(payments),
        failed_payments=failed_count,
        recovered_revenue=round(recovered_sum, 2),
        revenue_at_risk=round(risk_sum, 2),
        last_payment_date=payments[0].created_at if payments else None,
        recovery_status=rec_status,
        currency="USD",
        payments=[PaymentResponse.model_validate(p) for p in payments],
        recovery_attempts=[RecoveryAttemptResponse.model_validate(a) for a in attempts],
        audit_timeline=[
            AuditLogBrief(
                id=log.id,
                timestamp=log.timestamp,
                action=log.action,
                status=log.status,
                actor=log.actor,
                details=log.details,
            )
            for log in audits
        ],
    )
