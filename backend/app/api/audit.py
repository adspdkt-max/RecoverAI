"""
Audit Log API Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.db.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, PaginatedAuditResponse

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("", response_model=PaginatedAuditResponse)
def list_audit_logs(
    search: Optional[str] = Query(None, description="Search by action, payment ID, customer ID, or actor"),
    action: Optional[str] = Query(None, description="Filter by exact action name"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns an immutable, paginated chronological log of all recovery and payment system events.
    """
    query = db.query(AuditLog)

    if search:
        search_clean = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(search_clean),
                AuditLog.payment_id.ilike(search_clean),
                AuditLog.customer_id.ilike(search_clean),
                AuditLog.actor.ilike(search_clean),
                AuditLog.details.ilike(search_clean),
            )
        )

    if action and action.upper() != "ALL":
        query = query.filter(AuditLog.action == action.upper())

    if actor and actor.upper() != "ALL":
        query = query.filter(AuditLog.actor == actor.upper())

    total = query.count()
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedAuditResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
