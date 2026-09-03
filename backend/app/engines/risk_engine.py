"""
Explainable Risk Engine

Provides deterministic, explainable financial and operational risk scoring for failed payments.
Structured cleanly so that a machine learning scoring pipeline can be dropped in seamlessly.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from app.models.payment import Payment
from app.schemas.risk import RiskAnalysisResponse


class ExplainableRiskEngine:
    """
    Explainable Rule-Based Risk Engine evaluating failure reason, transaction amount,
    attempt frequency, and failure aging.
    """

    # Failure code mappings to cause category, risk weight, and confidence
    FAILURE_CODE_MAP: Dict[str, Dict[str, Any]] = {
        "fraud_suspected": {
            "category": "FRAUD_OR_SECURITY",
            "weight": 55.0,
            "confidence": 0.95,
            "reason": "Payment blocked due to high-risk fraud or velocity rule trigger.",
        },
        "stolen_card": {
            "category": "FRAUD_OR_SECURITY",
            "weight": 60.0,
            "confidence": 0.98,
            "reason": "Card reported stolen or lost; irrecoverable via standard retry.",
        },
        "lost_card": {
            "category": "FRAUD_OR_SECURITY",
            "weight": 60.0,
            "confidence": 0.98,
            "reason": "Card reported lost; requires new payment instrument.",
        },
        "expired_card": {
            "category": "CUSTOMER_CREDENTIALS_INVALID",
            "weight": 35.0,
            "confidence": 0.92,
            "reason": "Card expiration date has lapsed. Requires card update or account updater.",
        },
        "invalid_card_number": {
            "category": "CUSTOMER_CREDENTIALS_INVALID",
            "weight": 40.0,
            "confidence": 0.90,
            "reason": "Card number or PAN failed Luhn checksum or does not exist.",
        },
        "incorrect_cvc": {
            "category": "CUSTOMER_CREDENTIALS_INVALID",
            "weight": 30.0,
            "confidence": 0.88,
            "reason": "Card verification code mismatch.",
        },
        "insufficient_funds": {
            "category": "ACCOUNT_INSUFFICIENT_FUNDS",
            "weight": 20.0,
            "confidence": 0.85,
            "reason": "Customer account currently has insufficient balance or credit line.",
        },
        "withdrawal_limit_exceeded": {
            "category": "ACCOUNT_INSUFFICIENT_FUNDS",
            "weight": 22.0,
            "confidence": 0.82,
            "reason": "Cardholder daily or monthly transaction limit exceeded.",
        },
        "authentication_required": {
            "category": "CUSTOMER_ACTION_REQUIRED",
            "weight": 25.0,
            "confidence": 0.90,
            "reason": "3D Secure (3DS) or Strong Customer Authentication (SCA) verification required.",
        },
        "3d_secure_failed": {
            "category": "CUSTOMER_ACTION_REQUIRED",
            "weight": 30.0,
            "confidence": 0.88,
            "reason": "Cardholder failed or abandoned the 3D Secure authentication challenge.",
        },
        "processing_error": {
            "category": "TEMPORARY_ISSUER_DECLINE",
            "weight": 12.0,
            "confidence": 0.80,
            "reason": "Transient processing error at acquiring or issuing bank network.",
        },
        "issuer_unavailable": {
            "category": "TEMPORARY_ISSUER_DECLINE",
            "weight": 10.0,
            "confidence": 0.85,
            "reason": "Card issuing bank host system was temporarily offline during authorization.",
        },
        "network_error": {
            "category": "TEMPORARY_ISSUER_DECLINE",
            "weight": 8.0,
            "confidence": 0.85,
            "reason": "Network latency or transient socket timeout between payment gateway and network.",
        },
        "gateway_timeout": {
            "category": "TEMPORARY_ISSUER_DECLINE",
            "weight": 10.0,
            "confidence": 0.82,
            "reason": "Payment processor response timed out.",
        },
        "do_not_honor": {
            "category": "GENERIC_DECLINE",
            "weight": 32.0,
            "confidence": 0.70,
            "reason": "Issuer returned generic 'Do Not Honor' code without specific decline reason.",
        },
        "generic_decline": {
            "category": "GENERIC_DECLINE",
            "weight": 30.0,
            "confidence": 0.70,
            "reason": "Generic decline response from card network.",
        },
    }

    DEFAULT_FAILURE_META = {
        "category": "UNCLASSIFIED_DECLINE",
        "weight": 25.0,
        "confidence": 0.50,
        "reason": "Unclassified decline code; baseline heuristic applied.",
    }

    @classmethod
    def analyze_payment(cls, payment: Payment) -> RiskAnalysisResponse:
        """
        Calculates an explainable risk score and detailed factor breakdown for a given payment.
        """
        reasons: List[str] = []
        factor_breakdown: Dict[str, Any] = {}

        # 1. Failure Code & Cause Category Analysis
        code_key = (payment.failure_code or "").lower().strip()
        code_meta = cls.FAILURE_CODE_MAP.get(code_key, cls.DEFAULT_FAILURE_META)
        
        failure_weight = code_meta["weight"]
        cause_category = code_meta["category"]
        cause_confidence = code_meta["confidence"]
        
        reasons.append(f"Decline Factor: {code_meta['reason']} (+{failure_weight:.1f} pts)")
        factor_breakdown["failure_code_impact"] = {
            "code": payment.failure_code or "unknown",
            "category": cause_category,
            "weight": failure_weight,
        }

        # 2. Amount Exposure Tier
        amount = payment.amount
        amount_weight = 0.0
        curr = payment.currency or "INR"
        curr_sym = "₹" if curr == "INR" else "$"
        
        if amount >= 50000:
            amount_weight = 25.0
            reasons.append(f"Exposure Tier: Critical high-value transaction ({curr_sym}{amount:,.2f} >= {curr_sym}50,000) (+25.0 pts)")
        elif amount >= 15000:
            amount_weight = 18.0
            reasons.append(f"Exposure Tier: High-value transaction ({curr_sym}{amount:,.2f} >= {curr_sym}15,000) (+18.0 pts)")
        elif amount >= 5000:
            amount_weight = 10.0
            reasons.append(f"Exposure Tier: Standard enterprise tier ({curr_sym}{amount:,.2f} >= {curr_sym}5,000) (+10.0 pts)")
        elif amount >= 1000:
            amount_weight = 5.0
            reasons.append(f"Exposure Tier: Standard mid-market tier ({curr_sym}{amount:,.2f}) (+5.0 pts)")
        else:
            amount_weight = 2.0
            reasons.append(f"Exposure Tier: Micro-transaction ({curr_sym}{amount:,.2f} < {curr_sym}1,000) (+2.0 pts)")
            
        factor_breakdown["amount_exposure_impact"] = {
            "amount": amount,
            "currency": payment.currency,
            "weight": amount_weight,
        }

        # 3. Attempt Frequency & Fatigue
        attempts = payment.attempt_count
        attempt_weight = 0.0
        if attempts >= 4:
            attempt_weight = 40.0
            reasons.append(f"Attempt Velocity: Severe retry fatigue ({attempts} failed attempts) (+40.0 pts)")
        elif attempts == 3:
            attempt_weight = 25.0
            reasons.append(f"Attempt Velocity: High retry count ({attempts} attempts) (+25.0 pts)")
        elif attempts == 2:
            attempt_weight = 12.0
            reasons.append(f"Attempt Velocity: Second attempt failure (+12.0 pts)")
        else:
            attempt_weight = 0.0
            reasons.append(f"Attempt Velocity: Initial failure event (0.0 pts)")
            
        factor_breakdown["attempt_velocity_impact"] = {
            "attempts": attempts,
            "weight": attempt_weight,
        }

        # 4. Failure Aging (Recency)
        now_dt = datetime.utcnow()
        created_dt = payment.created_at or now_dt
        age_hours = max(0.0, (now_dt - created_dt).total_seconds() / 3600.0)
        
        recency_weight = 0.0
        if age_hours > 168:  # > 7 days
            recency_weight = 20.0
            reasons.append(f"Recency: Stale failure event ({age_hours/24:.1f} days old) (+20.0 pts)")
        elif age_hours > 24:  # > 1 day
            recency_weight = 10.0
            reasons.append(f"Recency: Aged failure event ({age_hours:.1f} hours old) (+10.0 pts)")
        elif age_hours > 2:
            recency_weight = 4.0
            reasons.append(f"Recency: Recent failure event ({age_hours:.1f} hours old) (+4.0 pts)")
        else:
            recency_weight = 0.0
            reasons.append("Recency: Real-time immediate failure (< 2 hours old) (0.0 pts)")
            
        factor_breakdown["recency_impact"] = {
            "age_hours": round(age_hours, 2),
            "weight": recency_weight,
        }

        # Calculate Total Composite Risk Score (Clamped 0 - 100)
        total_score = min(100.0, max(0.0, failure_weight + amount_weight + attempt_weight + recency_weight))
        total_score = round(total_score, 1)

        # Map to Risk Level and Priority
        if total_score >= 80.0:
            risk_level = "CRITICAL"
            recovery_priority = "URGENT"
        elif total_score >= 60.0:
            risk_level = "HIGH"
            recovery_priority = "HIGH"
        elif total_score >= 30.0:
            risk_level = "MEDIUM"
            recovery_priority = "NORMAL"
        else:
            risk_level = "LOW"
            recovery_priority = "LOW"

        # Recommended Immediate Action Preview
        action_preview = "Execute automated recovery intervention"
        if risk_level == "CRITICAL" or cause_category == "FRAUD_OR_SECURITY":
            action_preview = "Require human review before further actions"
        elif cause_category == "CUSTOMER_ACTION_REQUIRED":
            action_preview = "Dispatch direct 3DS / Payment Link to customer"

        return RiskAnalysisResponse(
            payment_id=payment.payment_id,
            revenue_at_risk=payment.amount,
            currency=payment.currency,
            risk_score=total_score,
            risk_level=risk_level,
            recovery_priority=recovery_priority,
            cause_category=cause_category,
            cause_confidence=cause_confidence,
            reasons=reasons,
            factor_breakdown=factor_breakdown,
            recommended_immediate_action=action_preview,
        )
