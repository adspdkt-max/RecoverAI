"""
Audit Log Database Model
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    payment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("payments.payment_id"), index=True, nullable=True)
    attempt_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(64), default="SYSTEM", nullable=False)

    payment = relationship("Payment", back_populates="audit_logs")
