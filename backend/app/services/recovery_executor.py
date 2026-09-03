"""
Recovery Executor Service

Safely executes bounded recovery attempts, enforces safety guardrails,
and manages human approval workflows.
"""
from datetime import datetime
import uuid
from typing import Optional, List, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.schemas.recovery import RecoveryExecuteRequest, RecoveryDecisionResponse
from app.services.audit_service import AuditService
from app.engines.recovery_engine import RecoveryEngine
from app.engines.risk_engine import ExplainableRiskEngine


class RecoveryExecutorService:
    @staticmethod
    def execute_recovery(db: Session, request: RecoveryExecuteRequest) -> RecoveryAttempt:
        """
        Validates safety constraints and creates a bounded recovery attempt in PENDING state.
        Recovery is NOT confirmed until a successful webhook is processed.
        """
        payment = db.query(Payment).filter(Payment.payment_id == request.payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment '{request.payment_id}' not found.")

        if payment.status == "CAPTURED":
            raise HTTPException(
                status_code=400,
                detail=f"Payment '{request.payment_id}' is already captured and settled.",
            )

        intervention = request.intervention.strip().upper()

        # Guardrail: NEVER execute NO_ACTION
        if intervention == "NO_ACTION":
            raise HTTPException(
                status_code=400,
                detail="NO_ACTION cannot be executed as an active recovery intervention.",
            )

        # Check existing active attempts to avoid duplicate concurrent in-flight attempts
        active_attempt = (
            db.query(RecoveryAttempt)
            .filter(
                RecoveryAttempt.payment_id == payment.payment_id,
                RecoveryAttempt.status == "PENDING",
            )
            .first()
        )
        if active_attempt:
            raise HTTPException(
                status_code=400,
                detail=f"An active recovery attempt ({active_attempt.attempt_id}) is already in flight for this payment.",
            )

        # Calculate or load decision
        decision = RecoveryEngine.decide(
            risk_level=payment.risk_level or "MEDIUM",
            cause_category=payment.cause_category or "TEMPORARY_ISSUER_DECLINE",
            amount=request.amount,
            payment_attempts=payment.attempt_count,
            payment_id=payment.payment_id,
        )

        # Human Approval Enforcement for High Value or Critical Risk
        is_high_value = request.amount >= RecoveryEngine.HIGH_VALUE_THRESHOLD
        is_critical = (payment.risk_level or "").upper() == "CRITICAL"
        requires_approval = decision.requires_human_approval or is_high_value or is_critical

        initial_status = "PENDING"
        is_approved = request.is_human_approved

        if requires_approval and not is_approved and intervention != "HUMAN_ESCALATION":
            # If intervention is not escalation but requires approval and not given, escalate it
            intervention = "HUMAN_ESCALATION"
            initial_status = "ESCALATED"

        attempt_id = f"rec_{uuid.uuid4().hex[:12]}"

        attempt = RecoveryAttempt(
            attempt_id=attempt_id,
            payment_id=payment.payment_id,
            intervention=intervention,
            amount=request.amount,
            currency=request.currency.upper(),
            status=initial_status,
            recovered_amount=0.0,
            recovery_probability=decision.recovery_probability,
            requires_human_approval=requires_approval,
            is_human_approved=is_approved,
            approved_by="OPERATOR" if is_approved else None,
            created_at=datetime.utcnow(),
        )

        # Increment payment attempt count
        payment.attempt_count += 1
        payment.updated_at = datetime.utcnow()

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Audit log
        action_name = "HUMAN_ESCALATION" if initial_status == "ESCALATED" else "RECOVERY_ATTEMPT_CREATED"
        AuditService.log_event(
            db=db,
            action=action_name,
            payment_id=payment.payment_id,
            attempt_id=attempt.attempt_id,
            customer_id=payment.customer_id,
            status=attempt.status,
            details=f"Created recovery attempt {attempt.attempt_id} with strategy {attempt.intervention} for {attempt.currency} {attempt.amount:,.2f}. Status: {attempt.status}. Note: Recovery is pending until webhook confirmation.",
            actor="OPERATOR" if is_approved else "RECOVERY_EXECUTOR",
        )

        return attempt

    @staticmethod
    def approve_escalation(db: Session, attempt_id: str, approved_by: str = "OPERATOR", notes: Optional[str] = None) -> RecoveryAttempt:
        """
        Approves a human-escalated attempt to allow automated processing to proceed.
        """
        attempt = db.query(RecoveryAttempt).filter(RecoveryAttempt.attempt_id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail=f"Recovery attempt '{attempt_id}' not found.")

        attempt.is_human_approved = True
        attempt.approved_by = approved_by
        attempt.status = "PENDING"
        attempt.intervention = "RETRY_PAYMENT"  # Convert to executable retry once approved
        db.commit()
        db.refresh(attempt)

        AuditService.log_event(
            db=db,
            action="RECOVERY_ATTEMPT_APPROVED",
            payment_id=attempt.payment_id,
            attempt_id=attempt.attempt_id,
            status=attempt.status,
            details=f"Recovery attempt {attempt.attempt_id} approved by {approved_by}. {notes or ''}".strip(),
            actor=approved_by,
        )

        return attempt

    @staticmethod
    def get_recovery_attempts(
        db: Session,
        status: Optional[str] = None,
        intervention: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[RecoveryAttempt], int]:
        """
        Retrieves filtered and paginated recovery attempts.
        """
        query = db.query(RecoveryAttempt)

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    RecoveryAttempt.attempt_id.ilike(search_clean),
                    RecoveryAttempt.payment_id.ilike(search_clean),
                    RecoveryAttempt.intervention.ilike(search_clean),
                )
            )

        if status and status.upper() != "ALL":
            query = query.filter(RecoveryAttempt.status == status.upper())

        if intervention and intervention.upper() != "ALL":
            query = query.filter(RecoveryAttempt.intervention == intervention.upper())

        total = query.count()
        offset = (page - 1) * limit
        items = query.order_by(desc(RecoveryAttempt.created_at)).offset(offset).limit(limit).all()

        return items, total
