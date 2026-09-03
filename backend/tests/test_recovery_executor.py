"""
Recovery Executor Guardrails and Approval Tests
"""
def test_execute_recovery_success(client):
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_exec_001",
            "customer_id": "cus_exec_100",
            "amount": 200.0,
            "status": "FAILED",
            "failure_code": "insufficient_funds",
        },
    )

    res = client.post(
        "/api/recovery/execute",
        json={
            "payment_id": "pay_exec_001",
            "intervention": "RETRY_PAYMENT",
            "amount": 200.0,
            "currency": "USD",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "PENDING"
    assert data["payment_id"] == "pay_exec_001"
    assert data["intervention"] == "RETRY_PAYMENT"


def test_reject_no_action_execution(client):
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_no_action_test",
            "customer_id": "cus_test",
            "amount": 100.0,
            "status": "FAILED",
        },
    )

    res = client.post(
        "/api/recovery/execute",
        json={
            "payment_id": "pay_no_action_test",
            "intervention": "NO_ACTION",
            "amount": 100.0,
            "currency": "USD",
        },
    )
    assert res.status_code == 400
    assert "NO_ACTION" in res.json()["detail"]


def test_high_value_escalation_workflow(client):
    client.post(
        "/api/payments/events",
        json={
            "payment_id": "pay_high_val",
            "customer_id": "cus_vip",
            "amount": 45000.0,  # High-value > ₹25,000
            "status": "FAILED",
            "failure_code": "insufficient_funds",
        },
    )

    # Attempt execution without explicit approval flag -> should be ESCALATED
    res = client.post(
        "/api/recovery/execute",
        json={
            "payment_id": "pay_high_val",
            "intervention": "RETRY_PAYMENT",
            "amount": 45000.0,
            "is_human_approved": False,
        },
    )
    assert res.status_code == 201
    attempt_data = res.json()
    assert attempt_data["status"] == "ESCALATED"
    assert attempt_data["requires_human_approval"] is True

    # Operator approves escalation
    attempt_id = attempt_data["attempt_id"]
    res_app = client.post(
        f"/api/recovery/attempts/{attempt_id}/approve",
        json={"attempt_id": attempt_id, "approved_by": "SUPERVISOR_ALICE"},
    )
    assert res_app.status_code == 200
    approved_data = res_app.json()
    assert approved_data["status"] == "PENDING"
    assert approved_data["is_human_approved"] is True
    assert approved_data["approved_by"] == "SUPERVISOR_ALICE"
