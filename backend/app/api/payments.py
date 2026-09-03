"""
Payments API Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.payment import (
    PaymentEventRequest,
    PaymentResponse,
    PaymentDetailResponse,
    PaginatedPaymentResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/events", response_model=PaymentResponse, status_code=201)
def create_or_update_payment_event(
    event: PaymentEventRequest,
    db: Session = Depends(get_db),
):
    """
    Ingests a raw payment lifecycle event (e.g. payment received, failed, captured).
    """
    payment = PaymentService.process_payment_event(db, event)
    return payment


@router.get("", response_model=PaginatedPaymentResponse)
def list_payments(
    search: Optional[str] = Query(None, description="Search by ID, customer, or reason"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, FAILED, CAPTURED, etc.)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Returns a paginated, filterable, and sortable list of payment records.
    """
    items, total = PaymentService.get_payments(
        db=db,
        search=search,
        status=status,
        risk_level=risk_level,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedPaymentResponse(
        items=[PaymentResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
def get_payment_detail(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves full payment record including associated recovery history and audit timeline.
    """
    payment = PaymentService.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")

    return PaymentDetailResponse(
        id=payment.id,
        payment_id=payment.payment_id,
        customer_id=payment.customer_id,
        merchant_id=payment.merchant_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        failure_code=payment.failure_code,
        failure_reason=payment.failure_reason,
        payment_method=payment.payment_method,
        attempt_count=payment.attempt_count,
        risk_score=payment.risk_score,
        risk_level=payment.risk_level,
        cause_category=payment.cause_category,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        recovery_attempts=[
            {
                "attempt_id": a.attempt_id,
                "intervention": a.intervention,
                "amount": a.amount,
                "currency": a.currency,
                "status": a.status,
                "recovered_amount": a.recovered_amount,
                "recovery_probability": a.recovery_probability,
                "requires_human_approval": a.requires_human_approval,
                "is_human_approved": a.is_human_approved,
                "created_at": a.created_at,
                "completed_at": a.completed_at,
            }
            for a in payment.recovery_attempts
        ],
        audit_logs=[
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "action": log.action,
                "status": log.status,
                "actor": log.actor,
                "details": log.details,
            }
            for log in payment.audit_logs
        ],
    )
