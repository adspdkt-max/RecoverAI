"""
Payment Database Model
"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), default="mch_recoverai_prod", index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(32), default="card", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cause_category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    recovery_attempts = relationship("RecoveryAttempt", back_populates="payment", cascade="all, delete-orphan", order_by="desc(RecoveryAttempt.created_at)")
    audit_logs = relationship("AuditLog", back_populates="payment", cascade="all, delete-orphan", order_by="desc(AuditLog.timestamp)")
