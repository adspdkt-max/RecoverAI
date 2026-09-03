"""
Webhook Pydantic Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class WebhookPaymentRequest(BaseModel):
    event_id: str = Field(..., description="Unique webhook event ID, e.g. evt_xxx")
    payment_id: str = Field(..., description="Referenced payment ID, e.g. pay_xxx")
    status: str = Field(..., description="Payment event status: captured, failed, pending")
    amount: float = Field(..., gt=0, description="Amount in event")
    currency: str = Field(default="INR", description="Currency code")
    failure_reason: Optional[str] = Field(default=None, description="Failure reason if status is failed")


class WebhookProcessResponse(BaseModel):
    success: bool
    event_id: str
    payment_id: str
    status: str
    duplicate: bool = False
    message: str
    recovered_amount: Optional[float] = None
    attempt_id: Optional[str] = None
