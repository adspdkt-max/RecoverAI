"""
Payment Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PaymentBase(BaseModel):
    payment_id: str = Field(..., description="Unique payment identifier, e.g. pay_xxx")
    customer_id: str = Field(..., description="Customer identifier, e.g. cus_xxx")
    merchant_id: str = Field(default="mch_recoverai_prod", description="Merchant account ID")
    amount: float = Field(..., gt=0, description="Payment transaction amount")
    currency: str = Field(default="INR", description="Three-letter ISO currency code")
    payment_method: str = Field(default="card", description="Payment method used")


class PaymentEventRequest(PaymentBase):
    status: str = Field(default="FAILED", description="Payment status: PENDING, FAILED, CAPTURED, CANCELLED, REFUNDED")
    failure_code: Optional[str] = Field(default=None, description="Standard decline/failure code")
    failure_reason: Optional[str] = Field(default=None, description="Human-readable failure reason")
    attempt_count: int = Field(default=1, ge=1, description="Number of attempts made")


class PaymentCreate(PaymentEventRequest):
    pass


class PaymentResponse(PaymentBase):
    id: int
    status: str
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    attempt_count: int
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    cause_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryAttemptBrief(BaseModel):
    attempt_id: str
    intervention: str
    amount: float
    currency: str
    status: str
    recovered_amount: float
    recovery_probability: float
    requires_human_approval: bool
    is_human_approved: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogBrief(BaseModel):
    id: int
    timestamp: datetime
    action: str
    status: Optional[str] = None
    actor: str
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailResponse(PaymentResponse):
    recovery_attempts: List[RecoveryAttemptBrief] = []
    audit_logs: List[AuditLogBrief] = []


class PaginatedPaymentResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    limit: int
    total_pages: int
