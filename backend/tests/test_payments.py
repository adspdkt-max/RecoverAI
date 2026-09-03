"""
Payments API and Lifecycle Tests
"""
def test_create_failed_payment_event(client):
    payload = {
        "payment_id": "pay_test_001",
        "customer_id": "cus_test_100",
        "merchant_id": "mch_default",
        "amount": 250.0,
        "currency": "USD",
        "status": "FAILED",
        "failure_code": "insufficient_funds",
        "failure_reason": "Account has insufficient balance",
        "attempt_count": 1,
    }
    response = client.post("/api/payments/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["payment_id"] == "pay_test_001"
    assert data["status"] == "FAILED"
    assert data["risk_score"] is not None
    assert data["cause_category"] == "ACCOUNT_INSUFFICIENT_FUNDS"


def test_list_and_filter_payments(client):
    # Create two payments
    p1 = {
        "payment_id": "pay_alpha",
        "customer_id": "cus_alpha",
        "amount": 100.0,
        "status": "FAILED",
        "failure_code": "expired_card",
    }
    p2 = {
        "payment_id": "pay_beta",
        "customer_id": "cus_beta",
        "amount": 500.0,
        "status": "CAPTURED",
    }
    client.post("/api/payments/events", json=p1)
    client.post("/api/payments/events", json=p2)

    # Test all
    res = client.get("/api/payments")
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # Filter status=FAILED
    res_failed = client.get("/api/payments?status=FAILED")
    assert res_failed.json()["total"] == 1
    assert res_failed.json()["items"][0]["payment_id"] == "pay_alpha"

    # Search
    res_search = client.get("/api/payments?search=cus_beta")
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["payment_id"] == "pay_beta"


def test_get_payment_detail_and_not_found(client):
    res_404 = client.get("/api/payments/pay_non_existent")
    assert res_404.status_code == 404

    # Create payment
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_detail_test",
            "customer_id": "cus_detail_test",
            "amount": 75.0,
            "status": "FAILED",
            "failure_code": "network_error",
        },
    )

    res = client.get("/api/payments/pay_detail_test")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "pay_detail_test"
    assert "recovery_attempts" in data
    assert "audit_logs" in data


def test_invalid_payment_amount(client):
    payload = {
        "payment_id": "pay_invalid",
        "customer_id": "cus_invalid",
        "amount": -50.0,  # Invalid negative amount
        "status": "FAILED",
    }
    response = client.post("/api/payments/events", json=payload)
    assert response.status_code == 422
