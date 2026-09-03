"""
Payment Service

Manages payment records, status transitions, search, and filtering.
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.schemas.payment import PaymentEventRequest
from app.services.audit_service import AuditService
from app.engines.risk_engine import ExplainableRiskEngine


class PaymentService:
    @staticmethod
    def process_payment_event(db: Session, event_data: PaymentEventRequest) -> Payment:
        """
        Ingests a payment event, creates/updates the payment record, computes baseline risk, and logs audit.
        """
        payment = db.query(Payment).filter(Payment.payment_id == event_data.payment_id).first()
        is_new = False

        if not payment:
            is_new = True
            payment = Payment(
                payment_id=event_data.payment_id,
                customer_id=event_data.customer_id,
                merchant_id=event_data.merchant_id,
                amount=event_data.amount,
                currency=event_data.currency.upper(),
                status=event_data.status.upper(),
                failure_code=event_data.failure_code,
                failure_reason=event_data.failure_reason,
                payment_method=event_data.payment_method,
                attempt_count=event_data.attempt_count,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(payment)
        else:
            payment.amount = event_data.amount
            payment.currency = event_data.currency.upper()
            payment.status = event_data.status.upper()
            payment.failure_code = event_data.failure_code
            payment.failure_reason = event_data.failure_reason
            payment.payment_method = event_data.payment_method
            payment.attempt_count = event_data.attempt_count
            payment.updated_at = datetime.utcnow()

        # If payment is failed, auto-run baseline risk evaluation
        if payment.status == "FAILED":
            risk_result = ExplainableRiskEngine.analyze_payment(payment)
            payment.risk_score = risk_result.risk_score
            payment.risk_level = risk_result.risk_level
            payment.cause_category = risk_result.cause_category

        db.commit()
        db.refresh(payment)

        # Audit Logging
        action_name = "PAYMENT_RECEIVED" if is_new else "PAYMENT_UPDATED"
        if payment.status == "FAILED":
            action_name = "PAYMENT_FAILED"
        elif payment.status == "CAPTURED":
            action_name = "PAYMENT_CAPTURED"

        AuditService.log_event(
            db=db,
            action=action_name,
            payment_id=payment.payment_id,
            customer_id=payment.customer_id,
            status=payment.status,
            details=f"Payment {payment.payment_id} processed for {payment.currency} {payment.amount:,.2f} with status {payment.status}. Failure code: {payment.failure_code or 'none'}",
            actor="PAYMENT_GATEWAY",
        )

        return payment

    @staticmethod
    def get_payments(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Payment], int]:
        """
        Retrieves paginated and filtered payments.
        """
        query = db.query(Payment)

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Payment.payment_id.ilike(search_clean),
                    Payment.customer_id.ilike(search_clean),
                    Payment.failure_code.ilike(search_clean),
                    Payment.failure_reason.ilike(search_clean),
                )
            )

        if status and status.upper() != "ALL":
            query = query.filter(Payment.status == status.upper())

        if risk_level and risk_level.upper() != "ALL":
            query = query.filter(Payment.risk_level == risk_level.upper())

        total = query.count()

        # Sorting
        sort_column = getattr(Payment, sort_by, Payment.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return items, total

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: str) -> Optional[Payment]:
        """
        Fetches payment by unique string ID.
        """
        return db.query(Payment).filter(Payment.payment_id == payment_id).first()
