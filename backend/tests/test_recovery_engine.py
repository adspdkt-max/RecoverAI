"""
Recovery Decision Engine Tests
"""
from app.engines.recovery_engine import RecoveryEngine


def test_temporary_decline_recovery_decision():
    decision = RecoveryEngine.decide(
        risk_level="LOW",
        cause_category="TEMPORARY_ISSUER_DECLINE",
        amount=150.0,
        payment_attempts=1,
    )
    assert decision.intervention == "RETRY_PAYMENT"
    assert decision.recovery_probability >= 0.70
    assert decision.cooldown_minutes == 15
    assert not decision.requires_human_approval


def test_retry_bound_exhaustion_escalates_to_human():
    decision = RecoveryEngine.decide(
        risk_level="MEDIUM",
        cause_category="TEMPORARY_ISSUER_DECLINE",
        amount=150.0,
        payment_attempts=3,  # Reached max 3 attempts
    )
    assert decision.intervention == "HUMAN_ESCALATION"
    assert decision.requires_human_approval is True
    assert any("Retry Bound Guardrail" in g for g in decision.safety_guardrails_applied)


def test_high_value_payment_requires_human_approval():
    decision = RecoveryEngine.decide(
        risk_level="LOW",
        cause_category="TEMPORARY_ISSUER_DECLINE",
        amount=35000.0,  # > ₹25,000 threshold
        payment_attempts=1,
    )
    assert decision.requires_human_approval is True
    assert any("High-Value Guardrail" in g for g in decision.safety_guardrails_applied)


def test_fraud_decision_escalates_to_human():
    decision = RecoveryEngine.decide(
        risk_level="CRITICAL",
        cause_category="FRAUD_OR_SECURITY",
        amount=500.0,
        payment_attempts=1,
    )
    assert decision.intervention == "HUMAN_ESCALATION"
    assert decision.requires_human_approval is True
