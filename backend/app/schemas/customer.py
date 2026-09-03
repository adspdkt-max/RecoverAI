"""
Customer Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.payment import PaymentResponse, AuditLogBrief
from app.schemas.recovery import RecoveryAttemptResponse


class CustomerSummary(BaseModel):
    customer_id: str
    payment_count: int
    failed_payments: int
    recovered_revenue: float
    revenue_at_risk: float
    last_payment_date: Optional[datetime] = None
    recovery_status: str = "HEALTHY"
    currency: str = "INR"


class CustomerDetailResponse(CustomerSummary):
    payments: List[PaymentResponse] = Field(default_factory=list)
    recovery_attempts: List[RecoveryAttemptResponse] = Field(default_factory=list)
    audit_timeline: List[AuditLogBrief] = Field(default_factory=list)


class PaginatedCustomerResponse(BaseModel):
    items: List[CustomerSummary]
    total: int
    page: int
    limit: int
    total_pages: int
