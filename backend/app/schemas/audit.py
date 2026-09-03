"""
Audit Log Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    payment_id: Optional[str] = None
    attempt_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
    details: Optional[str] = None
    actor: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    limit: int
    total_pages: int
