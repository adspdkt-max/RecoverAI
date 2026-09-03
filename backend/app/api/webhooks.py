"""
Webhooks API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.webhook import WebhookEvent
from app.schemas.webhook import WebhookPaymentRequest, WebhookProcessResponse
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/payment", response_model=WebhookProcessResponse)
def handle_payment_webhook(
    payload: WebhookPaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Receives and processes incoming payment provider webhooks (e.g. payment.captured, payment.failed).
    Enforces idempotency to prevent duplicate revenue recovery.
    """
    response = WebhookService.process_payment_webhook(db, payload)
    return response


@router.get("/events")
def list_webhook_events(
    limit: int = Query(20, ge=1, le=100),
    payment_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns recent raw webhook events logged by the system for developer inspection.
    """
    query = db.query(WebhookEvent)
    if payment_id:
        query = query.filter(WebhookEvent.payment_id == payment_id)

    events = query.order_by(WebhookEvent.created_at.desc()).limit(limit).all()

    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "payment_id": e.payment_id,
            "event_type": e.event_type,
            "status": e.status,
            "amount": e.amount,
            "currency": e.currency,
            "processed": e.processed,
            "payload_json": e.payload_json,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
