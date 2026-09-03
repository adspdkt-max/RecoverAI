"""
Recovery Decision Engine

Determines safe, bounded recovery strategies for failed payments while enforcing strict safety rules:
- Bounded retry limits (no infinite loops)
- Human approval triggers for high-value or critical risk payments
- Strict prohibition of direct money movement
- Intelligent cooldown periods
"""
from typing import List, Optional
from app.models.payment import Payment
from app.schemas.recovery import RecoveryDecisionResponse


class RecoveryEngine:
    """
    Deterministic Decision Engine evaluating risk profile, decline mechanics,
    attempt fatigue, and transaction value.
    """

    MAX_AUTOMATED_ATTEMPTS = 3
    HIGH_VALUE_THRESHOLD = 25000.0

    @classmethod
    def decide(
        cls,
        risk_level: str,
        cause_category: str,
        amount: float,
        payment_attempts: int,
        customer_action_available: bool = True,
        payment_id: Optional[str] = None,
    ) -> RecoveryDecisionResponse:
        """
        Determines the optimal recovery strategy along with safety constraints.
        """
        guardrails: List[str] = []
        requires_human_approval = False
        requires_customer_action = False

        # Guardrail 1: High-value payment threshold check
        if amount >= cls.HIGH_VALUE_THRESHOLD:
            requires_human_approval = True
            guardrails.append(f"High-Value Guardrail: Amount (₹{amount:,.2f}) >= ₹{cls.HIGH_VALUE_THRESHOLD:,.2f} requires human approval")

        # Guardrail 2: Critical risk level check
        if risk_level.upper() == "CRITICAL":
            requires_human_approval = True
            guardrails.append("Critical Risk Guardrail: Critical risk profile flagged for human supervisor review")

        # Guardrail 3: Max Retry Limit Exhaustion
        if payment_attempts >= cls.MAX_AUTOMATED_ATTEMPTS:
            guardrails.append(f"Retry Bound Guardrail: Attempt limit reached ({payment_attempts}/{cls.MAX_AUTOMATED_ATTEMPTS}). Escalating to human team")
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="HUMAN_ESCALATION",
                recovery_probability=0.25,
                reason=f"Maximum automated recovery attempts ({cls.MAX_AUTOMATED_ATTEMPTS}) reached. Escalating to account management to avoid customer fatigue.",
                requires_customer_action=False,
                requires_human_approval=True,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=0,
                safety_guardrails_applied=guardrails,
            )

        # Decision Matrix by Cause Category
        cat = (cause_category or "").upper()

        if cat == "FRAUD_OR_SECURITY":
            guardrails.append("Anti-Fraud Guardrail: Automated payment retry prohibited for security risk")
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="HUMAN_ESCALATION",
                recovery_probability=0.10,
                reason="High security or fraud risk detected. Automated retry is strictly prohibited to protect merchant credentials.",
                requires_customer_action=False,
                requires_human_approval=True,
                max_attempts=1,
                cooldown_minutes=0,
                safety_guardrails_applied=guardrails,
            )

        elif cat == "TEMPORARY_ISSUER_DECLINE":
            guardrails.append(f"Bounded Retry Guardrail: Automated retry scheduled with 15 min cooldown (Attempt {payment_attempts + 1}/{cls.MAX_AUTOMATED_ATTEMPTS})")
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="RETRY_PAYMENT",
                recovery_probability=0.82 if payment_attempts == 1 else 0.65,
                reason="Temporary network or issuing bank glitch detected. High likelihood of recovery via scheduled automated retry.",
                requires_customer_action=False,
                requires_human_approval=requires_human_approval,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=15,
                safety_guardrails_applied=guardrails,
            )

        elif cat == "ACCOUNT_INSUFFICIENT_FUNDS":
            guardrails.append("Smart Dunning Guardrail: Insufficient funds cooldown set to 720 minutes (12 hours)")
            intervention = "SUBSCRIPTION_RETRY" if amount < 200 else "RETRY_PAYMENT"
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention=intervention,
                recovery_probability=0.68 if payment_attempts == 1 else 0.45,
                reason="Soft decline due to balance limit. Scheduled retry aligned with banking settlement cycles.",
                requires_customer_action=False,
                requires_human_approval=requires_human_approval,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=720,
                safety_guardrails_applied=guardrails,
            )

        elif cat == "CUSTOMER_ACTION_REQUIRED":
            requires_customer_action = True
            guardrails.append("Interactive Flow Guardrail: Customer direct authentication challenge required")
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="SEND_PAYMENT_LINK",
                recovery_probability=0.74,
                reason="3D Secure / SCA verification or updated card authorization required from customer.",
                requires_customer_action=True,
                requires_human_approval=requires_human_approval,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=60,
                safety_guardrails_applied=guardrails,
            )

        elif cat == "CUSTOMER_CREDENTIALS_INVALID":
            requires_customer_action = True
            guardrails.append("Credential Invalidation Guardrail: Existing payment instrument expired or invalid")
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="ALTERNATE_PAYMENT_METHOD",
                recovery_probability=0.62,
                reason="Expired card or invalid credential. Requesting customer to add or select alternate payment method.",
                requires_customer_action=True,
                requires_human_approval=requires_human_approval,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=120,
                safety_guardrails_applied=guardrails,
            )

        elif cat == "GENERIC_DECLINE":
            if payment_attempts == 1:
                return RecoveryDecisionResponse(
                    payment_id=payment_id,
                    intervention="CUSTOMER_REMINDER",
                    recovery_probability=0.55,
                    reason="Generic card decline. Sending gentle customer reminder before second retry attempt.",
                    requires_customer_action=True,
                    requires_human_approval=requires_human_approval,
                    max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                    cooldown_minutes=180,
                    safety_guardrails_applied=guardrails,
                )
            else:
                return RecoveryDecisionResponse(
                    payment_id=payment_id,
                    intervention="ALTERNATE_PAYMENT_METHOD",
                    recovery_probability=0.48,
                    reason="Persistent generic decline. Recommending backup payment instrument.",
                    requires_customer_action=True,
                    requires_human_approval=requires_human_approval,
                    max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                    cooldown_minutes=240,
                    safety_guardrails_applied=guardrails,
                )

        else:
            # Fallback for unknown / unclassified
            return RecoveryDecisionResponse(
                payment_id=payment_id,
                intervention="CUSTOMER_REMINDER" if customer_action_available else "RETRY_PAYMENT",
                recovery_probability=0.50,
                reason="Standard recovery protocol applied for unclassified decline.",
                requires_customer_action=customer_action_available,
                requires_human_approval=requires_human_approval,
                max_attempts=cls.MAX_AUTOMATED_ATTEMPTS,
                cooldown_minutes=120,
                safety_guardrails_applied=guardrails,
            )
