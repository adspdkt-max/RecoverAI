"""
Explainable Risk Engine Tests
"""
from app.models.payment import Payment
from app.engines.risk_engine import ExplainableRiskEngine


def test_risk_scoring_fraud():
    p = Payment(
        payment_id="pay_fraud",
        customer_id="cus_test",
        amount=60000.0,  # Critical High tier +25 pts
        currency="INR",
        status="FAILED",
        failure_code="fraud_suspected",  # +55 pts
        attempt_count=1,
    )
    result = ExplainableRiskEngine.analyze_payment(p)
    assert result.risk_score >= 80.0
    assert result.risk_level == "CRITICAL"
    assert result.recovery_priority == "URGENT"
    assert result.cause_category == "FRAUD_OR_SECURITY"
    assert len(result.reasons) >= 3


def test_risk_scoring_network_glitch():
    p = Payment(
        payment_id="pay_glitch",
        customer_id="cus_test",
        amount=499.0,  # Micro tier +2 pts
        currency="INR",
        status="FAILED",
        failure_code="network_error",  # +8 pts
        attempt_count=1,
    )
    result = ExplainableRiskEngine.analyze_payment(p)
    assert result.risk_score < 30.0
    assert result.risk_level == "LOW"
    assert result.cause_category == "TEMPORARY_ISSUER_DECLINE"


def test_risk_analyze_api_endpoint(client):
    # Ingest a payment first
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_risk_api_test",
            "customer_id": "cus_123",
            "amount": 3500.0,
            "currency": "INR",
            "status": "FAILED",
            "failure_code": "expired_card",
        },
    )

    res = client.post("/api/risk/analyze", json={"payment_id": "pay_risk_api_test"})
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "pay_risk_api_test"
    assert data["cause_category"] == "CUSTOMER_CREDENTIALS_INVALID"
    assert data["currency"] == "INR"
    assert "factor_breakdown" in data
