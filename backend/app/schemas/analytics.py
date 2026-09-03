"""
Analytics Pydantic Schemas
"""
from typing import List, Dict
from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    date: str = Field(..., description="ISO Date string YYYY-MM-DD")
    amount: float = Field(..., description="Monetary total or count for that date")
    count: int = Field(default=0, description="Number of events on that date")


class AnalyticsSummaryResponse(BaseModel):
    revenue_at_risk: float
    recovered_revenue: float
    recovery_rate: float
    recovery_attempts: int
    recovery_success_rate: float
    failed_payments: int
    total_payments: int
    total_volume: float
    currency: str = "INR"
    
    revenue_at_risk_over_time: List[TimeSeriesPoint] = Field(default_factory=list)
    recovered_revenue_over_time: List[TimeSeriesPoint] = Field(default_factory=list)
    
    payment_status: Dict[str, int] = Field(default_factory=dict)
    risk_distribution: Dict[str, int] = Field(default_factory=dict)
    recovery_interventions: Dict[str, int] = Field(default_factory=dict)
    failure_reasons: Dict[str, int] = Field(default_factory=dict)
    intervention_success_rates: Dict[str, float] = Field(default_factory=dict)
