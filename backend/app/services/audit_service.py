"""
Audit Service

Records immutable audit trails for every key action and transition in the revenue recovery lifecycle.
"""
from datetime import datetime
from typing import Optional, Any
import json
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        payment_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        details: Optional[Any] = None,
        actor: str = "SYSTEM",
    ) -> AuditLog:
        """
        Creates and persists an audit log record.
        """
        detail_str = details if isinstance(details, str) else json.dumps(details) if details is not None else None

        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            action=action,
            payment_id=payment_id,
            attempt_id=attempt_id,
            customer_id=customer_id,
            status=status,
            details=detail_str,
            actor=actor,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
