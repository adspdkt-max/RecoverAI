"""
Webhook Processing Service

Provides idempotent ingestion of payment provider webhooks, records events,
and completes recovery attempt lifecycles.
"""
from datetime import datetime
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.models.webhook import WebhookEvent
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.schemas.webhook import WebhookPaymentRequest, WebhookProcessResponse
from app.services.audit_service import AuditService


class WebhookService:
    @staticmethod
    def process_payment_webhook(db: Session, payload: WebhookPaymentRequest) -> WebhookProcessResponse:
        """
        Processes an incoming webhook event idempotently.
        """
        # Check for idempotency / duplicate webhook
        existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == payload.event_id).first()
        if existing_event:
            return WebhookProcessResponse(
                success=True,
                event_id=payload.event_id,
                payment_id=payload.payment_id,
                status=existing_event.status,
                duplicate=True,
                message="Webhook event already processed (idempotent duplicate response).",
            )

        # Store incoming event
        webhook_record = WebhookEvent(
            event_id=payload.event_id,
            payment_id=payload.payment_id,
            event_type=f"payment.{payload.status.lower()}",
            status=payload.status.lower(),
            amount=payload.amount,
            currency=payload.currency.upper(),
            processed=True,
            payload_json=json.dumps(payload.model_dump()),
            created_at=datetime.utcnow(),
        )
        db.add(webhook_record)

        # Retrieve payment
        payment = db.query(Payment).filter(Payment.payment_id == payload.payment_id).first()
        attempt_id: Optional[str] = None
        recovered_amount: Optional[float] = None

        if payment:
            # Find the most recent active or pending recovery attempt for this payment
            active_attempt = (
                db.query(RecoveryAttempt)
                .filter(
                    RecoveryAttempt.payment_id == payment.payment_id,
                    RecoveryAttempt.status.in_(["PENDING", "ESCALATED"]),
                )
                .order_by(RecoveryAttempt.created_at.desc())
                .first()
            )

            if payload.status.lower() == "captured":
                payment.status = "CAPTURED"
                payment.updated_at = datetime.utcnow()
                recovered_amount = payload.amount

                if active_attempt:
                    active_attempt.status = "SUCCEEDED"
                    active_attempt.recovered_amount = payload.amount
                    active_attempt.webhook_event_id = payload.event_id
                    active_attempt.completed_at = datetime.utcnow()
                    attempt_id = active_attempt.attempt_id

                AuditService.log_event(
                    db=db,
                    action="WEBHOOK_RECEIVED",
                    payment_id=payment.payment_id,
                    attempt_id=attempt_id,
                    status="CAPTURED",
                    details=f"Provider webhook {payload.event_id} confirmed payment capture of {payload.currency} {payload.amount:,.2f}.",
                    actor="WEBHOOK_GATEWAY",
                )

                if active_attempt:
                    AuditService.log_event(
                        db=db,
                        action="RECOVERY_SUCCEEDED",
                        payment_id=payment.payment_id,
                        attempt_id=active_attempt.attempt_id,
                        customer_id=payment.customer_id,
                        status="SUCCEEDED",
                        details=f"Revenue recovery confirmed! Strategy '{active_attempt.intervention}' successfully recovered {payload.currency} {payload.amount:,.2f}.",
                        actor="RECOVERY_ENGINE",
                    )

            elif payload.status.lower() == "failed":
                payment.status = "FAILED"
                payment.failure_reason = payload.failure_reason or payment.failure_reason
                payment.updated_at = datetime.utcnow()

                if active_attempt:
                    active_attempt.status = "FAILED"
                    active_attempt.failure_reason = payload.failure_reason or "Downstream attempt failed"
                    active_attempt.webhook_event_id = payload.event_id
                    active_attempt.completed_at = datetime.utcnow()
                    attempt_id = active_attempt.attempt_id

                AuditService.log_event(
                    db=db,
                    action="WEBHOOK_RECEIVED",
                    payment_id=payment.payment_id,
                    attempt_id=attempt_id,
                    status="FAILED",
                    details=f"Provider webhook {payload.event_id} reported payment failure: {payload.failure_reason or 'No reason provided'}.",
                    actor="WEBHOOK_GATEWAY",
                )

        db.commit()

        return WebhookProcessResponse(
            success=True,
            event_id=payload.event_id,
            payment_id=payload.payment_id,
            status=payload.status.lower(),
            duplicate=False,
            message="Webhook event processed successfully and database synchronized.",
            recovered_amount=recovered_amount,
            attempt_id=attempt_id,
        )
