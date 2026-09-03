"""
Risk Engine Pydantic Schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskAnalysisRequest(BaseModel):
    payment_id: str = Field(..., description="ID of payment to analyze, e.g. pay_xxx")


class RiskFactorDetail(BaseModel):
    name: str
    impact: str  # POSITIVE, NEUTRAL, NEGATIVE, CRITICAL
    weight: float
    description: str


class RiskAnalysisResponse(BaseModel):
    payment_id: str
    revenue_at_risk: float
    currency: str
    risk_score: float = Field(..., ge=0, le=100, description="Explainable risk score from 0 (safest) to 100 (highest risk)")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    recovery_priority: str = Field(..., description="LOW, NORMAL, HIGH, URGENT")
    cause_category: str = Field(..., description="Root cause category of payment failure")
    cause_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in cause categorization")
    reasons: List[str] = Field(default_factory=list, description="Plain English factor justifications")
    factor_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Detailed numerical component weights")
    recommended_immediate_action: Optional[str] = None
