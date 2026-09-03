"""
Recovery Attempt Database Model
"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(String(64), ForeignKey("payments.payment_id"), index=True, nullable=False)
    
    intervention: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    webhook_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    recovery_probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_human_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    payment = relationship("Payment", back_populates="recovery_attempts")
