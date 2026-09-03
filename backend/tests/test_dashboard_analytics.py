"""
Dashboard, Analytics, Customers, and Audit Integrity Tests
"""
def test_empty_database_zero_fake_data_integrity(client):
    """
    CRITICAL REQUIREMENT: Empty database must return genuine empty/zero states, never hard-coded fake numbers.
    """
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["revenue_at_risk"] == 0.0
    assert data["recovered_revenue"] == 0.0
    assert data["recovery_rate"] == 0.0
    assert data["active_attempts"] == 0
    assert data["total_payments"] == 0
    assert data["failed_payments"] == 0
    assert data["successful_payments"] == 0
    assert data["human_escalations"] == 0
    assert data["recent_payments"] == []
    assert data["recent_recovery_attempts"] == []


def test_seed_and_metrics_calculation(client):
    # Trigger demo seed
    seed_res = client.post("/api/seed")
    assert seed_res.status_code == 201
    assert seed_res.json()["seeded"] is True

    # Check dashboard has real calculated non-zero values
    dash_res = client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_payments"] > 0
    assert dash_data["revenue_at_risk"] > 0.0
    assert dash_data["recovered_revenue"] > 0.0
    assert len(dash_data["recent_payments"]) > 0

    # Check analytics endpoint
    analytics_res = client.get("/api/analytics/summary")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert len(analytics_data["revenue_at_risk_over_time"]) > 0
    assert len(analytics_data["recovered_revenue_over_time"]) > 0

    # Check customers list
    cus_res = client.get("/api/customers")
    assert cus_res.status_code == 200
    assert cus_res.json()["total"] > 0

    # Check audit log
    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    assert audit_res.json()["total"] > 0

    # Test clear endpoint returns back to clean state
    clear_res = client.post("/api/seed/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["cleared"] is True

    # Verify zero again
    dash_zero = client.get("/api/dashboard/summary")
    assert dash_zero.json()["total_payments"] == 0
