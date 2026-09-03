"""
Recovery Operations API Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.payment import Payment
from app.schemas.recovery import (
    RecoveryDecisionRequest,
    RecoveryDecisionResponse,
    RecoveryExecuteRequest,
    RecoveryAttemptResponse,
    RecoveryApproveRequest,
    PaginatedRecoveryResponse,
)
from app.engines.recovery_engine import RecoveryEngine
from app.services.recovery_executor import RecoveryExecutorService

router = APIRouter(prefix="/recovery", tags=["Recovery Operations"])


@router.post("/decide", response_model=RecoveryDecisionResponse)
def decide_recovery_strategy(
    request: RecoveryDecisionRequest,
    db: Session = Depends(get_db),
):
    """
    Evaluates payment parameters or an existing payment ID to recommend the safest recovery strategy.
    Enforces retry boundaries, human approval thresholds, and cooldowns.
    """
    risk_level = request.risk_level or "MEDIUM"
    cause_category = request.cause_category or "TEMPORARY_ISSUER_DECLINE"
    amount = request.amount or 100.0
    attempts = request.payment_attempts or 1

    # If payment_id is provided, pull real metadata from the database
    if request.payment_id:
        payment = db.query(Payment).filter(Payment.payment_id == request.payment_id).first()
        if payment:
            risk_level = payment.risk_level or risk_level
            cause_category = payment.cause_category or cause_category
            amount = payment.amount
            attempts = payment.attempt_count

    decision = RecoveryEngine.decide(
        risk_level=risk_level,
        cause_category=cause_category,
        amount=amount,
        payment_attempts=attempts,
        customer_action_available=request.customer_action_available if request.customer_action_available is not None else True,
        payment_id=request.payment_id,
    )

    return decision


@router.post("/execute", response_model=RecoveryAttemptResponse, status_code=201)
def execute_recovery_attempt(
    request: RecoveryExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Initializes a bounded recovery attempt in PENDING state.
    Note: Recovery is not confirmed until a successful webhook is received from the payment provider.
    """
    attempt = RecoveryExecutorService.execute_recovery(db, request)
    return RecoveryAttemptResponse.model_validate(attempt)


@router.post("/attempts/{attempt_id}/approve", response_model=RecoveryAttemptResponse)
def approve_escalated_attempt(
    attempt_id: str,
    request: RecoveryApproveRequest,
    db: Session = Depends(get_db),
):
    """
    Approves a human-escalated attempt so automated recovery processing can proceed.
    """
    approved = RecoveryExecutorService.approve_escalation(
        db=db,
        attempt_id=attempt_id,
        approved_by=request.approved_by,
        notes=request.notes,
    )
    return RecoveryAttemptResponse.model_validate(approved)


@router.get("/attempts", response_model=PaginatedRecoveryResponse)
def list_recovery_attempts(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, SUCCEEDED, FAILED, ESCALATED)"),
    intervention: Optional[str] = Query(None, description="Filter by intervention"),
    search: Optional[str] = Query(None, description="Search attempt ID or payment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Returns a paginated list of recovery attempts.
    """
    items, total = RecoveryExecutorService.get_recovery_attempts(
        db=db,
        status=status,
        intervention=intervention,
        search=search,
        page=page,
        limit=limit,
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedRecoveryResponse(
        items=[RecoveryAttemptResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
