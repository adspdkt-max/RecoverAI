"""
Webhook Ingestion and Idempotency Tests
"""
def test_successful_webhook_flow(client):
    # 1. Create failed payment
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_hook_001",
            "customer_id": "cus_hook_100",
            "amount": 320.0,
            "status": "FAILED",
            "failure_code": "network_error",
        },
    )

    # 2. Execute recovery attempt
    exec_res = client.post(
        "/api/recovery/execute",
        json={
            "payment_id": "pay_hook_001",
            "intervention": "RETRY_PAYMENT",
            "amount": 320.0,
        },
    )
    attempt_id = exec_res.json()["attempt_id"]

    # 3. Simulate payment.captured webhook
    webhook_payload = {
        "event_id": "evt_test_capture_999",
        "payment_id": "pay_hook_001",
        "status": "captured",
        "amount": 320.0,
        "currency": "USD",
    }
    hook_res = client.post("/api/webhooks/payment", json=webhook_payload)
    assert hook_res.status_code == 200
    hook_data = hook_res.json()
    assert hook_data["success"] is True
    assert hook_data["status"] == "captured"
    assert hook_data["recovered_amount"] == 320.0
    assert hook_data["duplicate"] is False

    # 4. Check payment status is now CAPTURED
    pay_res = client.get("/api/payments/pay_hook_001")
    assert pay_res.json()["status"] == "CAPTURED"

    # 5. Check recovery attempt is now SUCCEEDED
    attempts_res = client.get("/api/recovery/attempts?status=SUCCEEDED")
    assert any(a["attempt_id"] == attempt_id for a in attempts_res.json()["items"])


def test_webhook_idempotency_duplicate_handling(client):
    webhook_payload = {
        "event_id": "evt_idempotency_test_001",
        "payment_id": "pay_some_payment",
        "status": "captured",
        "amount": 100.0,
    }

    # First delivery
    res1 = client.post("/api/webhooks/payment", json=webhook_payload)
    assert res1.status_code == 200
    assert res1.json()["duplicate"] is False

    # Second identical delivery
    res2 = client.post("/api/webhooks/payment", json=webhook_payload)
    assert res2.status_code == 200
    assert res2.json()["duplicate"] is True
    assert "already processed" in res2.json()["message"]
