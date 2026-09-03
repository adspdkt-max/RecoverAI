"""
Demo Seed Service

Populates realistic, diverse mock payment intelligence data for demos and walkthroughs.
Does NOT hard-code fixed fake single values like ₹2,499.
Includes a clear_all_data method to return to a 100% clean empty state.
"""
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.recovery import RecoveryAttempt
from app.models.webhook import WebhookEvent
from app.models.audit import AuditLog
from app.engines.risk_engine import ExplainableRiskEngine
from app.services.audit_service import AuditService


class SeedService:
    @staticmethod
    def clear_all_data(db: Session) -> dict:
        """
        Wipes all records across all tables, returning database to true empty state.
        """
        deleted_attempts = db.query(RecoveryAttempt).delete()
        deleted_webhooks = db.query(WebhookEvent).delete()
        deleted_audits = db.query(AuditLog).delete()
        deleted_payments = db.query(Payment).delete()
        db.commit()

        return {
            "cleared": True,
            "deleted_payments": deleted_payments,
            "deleted_attempts": deleted_attempts,
            "deleted_webhooks": deleted_webhooks,
            "deleted_audits": deleted_audits,
            "message": "All database tables wiped successfully. System is in 100% clean empty state.",
        }

    @staticmethod
    def seed_demo_data(db: Session) -> dict:
        """
        Populates realistic payments, varied recovery states, and audit trails.
        """
        # First clear existing data
        SeedService.clear_all_data(db)

        now = datetime.utcnow()

        # Diverse seed scenarios in Indian Rupees (INR / ₹)
        scenarios = [
            # 1. High value fraud -> Escalated
            {
                "payment_id": "pay_sec_991823",
                "customer_id": "cus_vortex_772",
                "amount": 78500.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "fraud_suspected",
                "failure_reason": "High fraud probability score (0.96) on international BIN route.",
                "days_ago": 1,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_esc_441209",
                    "intervention": "HUMAN_ESCALATION",
                    "status": "ESCALATED",
                    "requires_approval": True,
                    "is_approved": False,
                },
            },
            # 2. Insufficient funds -> Recovered via retry
            {
                "payment_id": "pay_inf_330912",
                "customer_id": "cus_aurora_801",
                "amount": 3499.00,
                "currency": "INR",
                "status": "CAPTURED",
                "failure_code": "insufficient_funds",
                "failure_reason": "Card issuer reported insufficient credit/balance.",
                "days_ago": 4,
                "attempts": 2,
                "recovery": {
                    "attempt_id": "rec_ret_110943",
                    "intervention": "RETRY_PAYMENT",
                    "status": "SUCCEEDED",
                    "requires_approval": False,
                    "is_approved": True,
                    "recovered_amount": 3499.00,
                    "webhook_id": "evt_cap_992104",
                },
            },
            # 3. 3DS Authentication required -> In-Flight Payment Link
            {
                "payment_id": "pay_aut_558291",
                "customer_id": "cus_zenith_412",
                "amount": 14200.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "authentication_required",
                "failure_reason": "Strong Customer Authentication challenge not completed.",
                "days_ago": 0.2,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_lnk_773012",
                    "intervention": "SEND_PAYMENT_LINK",
                    "status": "PENDING",
                    "requires_approval": False,
                    "is_approved": False,
                },
            },
            # 4. Expired card -> In-Flight Alternate Payment Method
            {
                "payment_id": "pay_exp_771204",
                "customer_id": "cus_hyperion_109",
                "amount": 999.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "expired_card",
                "failure_reason": "Card expired on 07/26. Issuer declined auth.",
                "days_ago": 2,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_alt_884920",
                    "intervention": "ALTERNATE_PAYMENT_METHOD",
                    "status": "PENDING",
                    "requires_approval": False,
                    "is_approved": False,
                },
            },
            # 5. Network glitch -> Succeeded via immediate retry
            {
                "payment_id": "pay_net_882049",
                "customer_id": "cus_solaris_330",
                "amount": 18500.00,
                "currency": "INR",
                "status": "CAPTURED",
                "failure_code": "network_error",
                "failure_reason": "Issuer gateway connection timeout during processing.",
                "days_ago": 6,
                "attempts": 2,
                "recovery": {
                    "attempt_id": "rec_ret_339102",
                    "intervention": "RETRY_PAYMENT",
                    "status": "SUCCEEDED",
                    "requires_approval": False,
                    "is_approved": True,
                    "recovered_amount": 18500.00,
                    "webhook_id": "evt_cap_774921",
                },
            },
            # 6. High ticket enterprise renewal -> Succeeded via smart dunning
            {
                "payment_id": "pay_sub_109284",
                "customer_id": "cus_strata_504",
                "amount": 32000.00,
                "currency": "INR",
                "status": "CAPTURED",
                "failure_code": "insufficient_funds",
                "failure_reason": "Corporate account daily ACH limit reached on initial attempt.",
                "days_ago": 8,
                "attempts": 2,
                "recovery": {
                    "attempt_id": "rec_sub_664910",
                    "intervention": "SUBSCRIPTION_RETRY",
                    "status": "SUCCEEDED",
                    "requires_approval": False,
                    "is_approved": True,
                    "recovered_amount": 32000.00,
                    "webhook_id": "evt_cap_440192",
                },
            },
            # 7. Generic decline -> In-flight customer reminder
            {
                "payment_id": "pay_dnh_449102",
                "customer_id": "cus_novus_221",
                "amount": 7800.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "do_not_honor",
                "failure_reason": "Generic 'Do Not Honor' code returned from card network.",
                "days_ago": 3,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_rem_229104",
                    "intervention": "CUSTOMER_REMINDER",
                    "status": "PENDING",
                    "requires_approval": False,
                    "is_approved": False,
                },
            },
            # 8. Micro subscription -> Pending
            {
                "payment_id": "pay_mic_662019",
                "customer_id": "cus_lyra_619",
                "amount": 499.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "processing_error",
                "failure_reason": "Temporary processor switch outage.",
                "days_ago": 0.5,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_ret_550192",
                    "intervention": "RETRY_PAYMENT",
                    "status": "PENDING",
                    "requires_approval": False,
                    "is_approved": False,
                },
            },
            # 9. Direct successful payment (healthy customer baseline)
            {
                "payment_id": "pay_dir_774910",
                "customer_id": "cus_apex_844",
                "amount": 45000.00,
                "currency": "INR",
                "status": "CAPTURED",
                "failure_code": None,
                "failure_reason": None,
                "days_ago": 5,
                "attempts": 1,
                "recovery": None,
            },
            # 10. Direct successful payment
            {
                "payment_id": "pay_dir_993012",
                "customer_id": "cus_pulsar_921",
                "amount": 12000.00,
                "currency": "INR",
                "status": "CAPTURED",
                "failure_code": None,
                "failure_reason": None,
                "days_ago": 10,
                "attempts": 1,
                "recovery": None,
            },
            # 11. Stolen card -> Escalated
            {
                "payment_id": "pay_stl_220914",
                "customer_id": "cus_pulsar_921",
                "amount": 56000.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "stolen_card",
                "failure_reason": "Issuer confirmed stolen card alert.",
                "days_ago": 7,
                "attempts": 1,
                "recovery": {
                    "attempt_id": "rec_esc_993011",
                    "intervention": "HUMAN_ESCALATION",
                    "status": "ESCALATED",
                    "requires_approval": True,
                    "is_approved": False,
                },
            },
            # 12. Fresh failure unanalyzed
            {
                "payment_id": "pay_fresh_102938",
                "customer_id": "cus_aurora_801",
                "amount": 8900.00,
                "currency": "INR",
                "status": "FAILED",
                "failure_code": "insufficient_funds",
                "failure_reason": "Insufficient account balance at time of charge.",
                "days_ago": 0.1,
                "attempts": 1,
                "recovery": None,
            },
        ]

        created_payments = 0
        created_attempts = 0

        for sc in scenarios:
            created_at = now - timedelta(days=sc["days_ago"])
            payment = Payment(
                payment_id=sc["payment_id"],
                customer_id=sc["customer_id"],
                merchant_id="mch_recoverai_prod",
                amount=sc["amount"],
                currency=sc["currency"],
                status=sc["status"],
                failure_code=sc["failure_code"],
                failure_reason=sc["failure_reason"],
                payment_method="card",
                attempt_count=sc["attempts"],
                created_at=created_at,
                updated_at=created_at + timedelta(minutes=10),
            )

            # Analyze risk for failed payments
            if payment.status == "FAILED":
                risk_res = ExplainableRiskEngine.analyze_payment(payment)
                payment.risk_score = risk_res.risk_score
                payment.risk_level = risk_res.risk_level
                payment.cause_category = risk_res.cause_category

            db.add(payment)
            created_payments += 1

            # Log audit for payment creation
            AuditService.log_event(
                db=db,
                action="PAYMENT_RECEIVED",
                payment_id=payment.payment_id,
                customer_id=payment.customer_id,
                status=payment.status,
                details=f"Payment {payment.payment_id} recorded for {payment.currency} {payment.amount:,.2f}.",
                actor="GATEWAY_INGESTOR",
            )

            if sc.get("recovery"):
                rec_info = sc["recovery"]
                is_succ = rec_info["status"] == "SUCCEEDED"
                completed_at = created_at + timedelta(hours=2) if is_succ else None

                attempt = RecoveryAttempt(
                    attempt_id=rec_info["attempt_id"],
                    payment_id=payment.payment_id,
                    intervention=rec_info["intervention"],
                    amount=payment.amount,
                    currency=payment.currency,
                    status=rec_info["status"],
                    recovered_amount=rec_info.get("recovered_amount", 0.0),
                    webhook_event_id=rec_info.get("webhook_id"),
                    requires_human_approval=rec_info["requires_approval"],
                    is_human_approved=rec_info["is_approved"],
                    recovery_probability=0.75 if is_succ else 0.50,
                    created_at=created_at + timedelta(minutes=5),
                    completed_at=completed_at,
                )
                db.add(attempt)
                created_attempts += 1

                # If webhook was simulated
                if rec_info.get("webhook_id"):
                    webhook_rec = WebhookEvent(
                        event_id=rec_info["webhook_id"],
                        payment_id=payment.payment_id,
                        event_type="payment.captured",
                        status="captured",
                        amount=payment.amount,
                        currency=payment.currency,
                        processed=True,
                        payload_json='{"demo_seeded": true}',
                        created_at=completed_at or created_at,
                    )
                    db.add(webhook_rec)

                # Log audit for recovery attempt
                AuditService.log_event(
                    db=db,
                    action="RECOVERY_ATTEMPT_CREATED" if rec_info["status"] != "ESCALATED" else "HUMAN_ESCALATION",
                    payment_id=payment.payment_id,
                    attempt_id=attempt.attempt_id,
                    customer_id=payment.customer_id,
                    status=attempt.status,
                    details=f"Recovery strategy {attempt.intervention} initialized. Status: {attempt.status}.",
                    actor="RECOVERY_ENGINE",
                )

                if is_succ:
                    AuditService.log_event(
                        db=db,
                        action="RECOVERY_SUCCEEDED",
                        payment_id=payment.payment_id,
                        attempt_id=attempt.attempt_id,
                        customer_id=payment.customer_id,
                        status="SUCCEEDED",
                        details=f"Revenue recovery confirmed! {payment.currency} {payment.amount:,.2f} successfully captured.",
                        actor="WEBHOOK_GATEWAY",
                    )

        db.commit()

        return {
            "seeded": True,
            "created_payments": created_payments,
            "created_recovery_attempts": created_attempts,
            "message": f"Successfully seeded {created_payments} realistic payments and {created_attempts} recovery workflows.",
        }
