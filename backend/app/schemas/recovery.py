"""
Recovery Engine Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RecoveryDecisionRequest(BaseModel):
    payment_id: Optional[str] = Field(default=None, description="Optional payment ID to evaluate from DB")
    risk_level: Optional[str] = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    cause_category: Optional[str] = Field(default="TEMPORARY_ISSUER_DECLINE", description="Cause category")
    amount: Optional[float] = Field(default=100.0, gt=0, description="Amount to recover")
    payment_attempts: Optional[int] = Field(default=1, ge=1, description="Previous attempt count")
    customer_action_available: Optional[bool] = Field(default=True, description="Whether customer communication channel is available")


class RecoveryDecisionResponse(BaseModel):
    payment_id: Optional[str] = None
    intervention: str = Field(..., description="Recommended recovery intervention strategy")
    recovery_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated likelihood of successful recovery")
    reason: str = Field(..., description="Explainable rationale for the recommendation")
    requires_customer_action: bool = Field(default=False)
    requires_human_approval: bool = Field(default=False)
    max_attempts: int = Field(default=3, description="Bounded retry threshold")
    cooldown_minutes: int = Field(default=60, description="Recommended waiting period before attempt")
    safety_guardrails_applied: List[str] = Field(default_factory=list, description="List of safety checks enforced")


class RecoveryExecuteRequest(BaseModel):
    payment_id: str = Field(..., description="Target payment ID, e.g. pay_xxx")
    intervention: str = Field(..., description="Intervention strategy to execute")
    amount: float = Field(..., gt=0, description="Amount for recovery attempt")
    currency: str = Field(default="INR", description="Currency code")
    is_human_approved: bool = Field(default=False, description="Approval flag if high-value/critical")
    operator_notes: Optional[str] = None


class RecoveryApproveRequest(BaseModel):
    attempt_id: str = Field(..., description="Recovery attempt ID to approve")
    approved_by: str = Field(default="OPERATOR", description="Approver username or role")
    notes: Optional[str] = None


class RecoveryAttemptResponse(BaseModel):
    id: int
    attempt_id: str
    payment_id: str
    intervention: str
    amount: float
    currency: str
    status: str
    recovered_amount: float
    webhook_event_id: Optional[str] = None
    failure_reason: Optional[str] = None
    recovery_probability: float
    requires_human_approval: bool
    is_human_approved: bool
    approved_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedRecoveryResponse(BaseModel):
    items: List[RecoveryAttemptResponse]
    total: int
    page: int
    limit: int
    total_pages: int
