"""
Dashboard Pydantic Schemas
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.payment import PaymentResponse
from app.schemas.recovery import RecoveryAttemptResponse


class DashboardSummaryResponse(BaseModel):
    revenue_at_risk: float = Field(..., description="Total unrecovered revenue currently in failed state")
    recovered_revenue: float = Field(..., description="Total revenue successfully recovered through interventions")
    recovery_rate: float = Field(..., description="Percentage of failed revenue recovered")
    active_attempts: int = Field(..., description="Number of currently pending/in-flight recovery attempts")
    total_payments: int = Field(..., description="Total lifetime payment transactions recorded")
    failed_payments: int = Field(..., description="Total failed payment transactions")
    successful_payments: int = Field(..., description="Total captured/successful payments")
    human_escalations: int = Field(..., description="Total cases escalated for human manual intervention")
    currency: str = Field(default="INR", description="Primary reporting currency")
    
    risk_distribution: Dict[str, int] = Field(default_factory=dict, description="Counts by risk tier")
    payment_status_distribution: Dict[str, int] = Field(default_factory=dict, description="Counts by payment status")
    intervention_distribution: Dict[str, int] = Field(default_factory=dict, description="Counts by recovery intervention")
    
    recent_payments: List[PaymentResponse] = Field(default_factory=list)
    recent_recovery_attempts: List[RecoveryAttemptResponse] = Field(default_factory=list)
