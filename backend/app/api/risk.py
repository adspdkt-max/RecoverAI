"""
Risk Intelligence API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.payment import Payment
from app.schemas.risk import RiskAnalysisRequest, RiskAnalysisResponse
from app.engines.risk_engine import ExplainableRiskEngine
from app.services.audit_service import AuditService

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])


@router.post("/analyze", response_model=RiskAnalysisResponse)
def analyze_payment_risk(
    request: RiskAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Executes an explainable risk evaluation on a specified payment ID.
    Updates the payment record with computed risk metrics and records an audit log.
    """
    payment = db.query(Payment).filter(Payment.payment_id == request.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment '{request.payment_id}' not found.")

    analysis = ExplainableRiskEngine.analyze_payment(payment)

    # Persist updated risk metrics
    payment.risk_score = analysis.risk_score
    payment.risk_level = analysis.risk_level
    payment.cause_category = analysis.cause_category
    db.commit()

    # Log audit
    AuditService.log_event(
        db=db,
        action="RISK_ANALYZED",
        payment_id=payment.payment_id,
        customer_id=payment.customer_id,
        status=analysis.risk_level,
        details=f"Explainable Risk Engine calculated score of {analysis.risk_score:.1f}/100 ({analysis.risk_level}). Cause: {analysis.cause_category}. Reasons: {'; '.join(analysis.reasons[:2])}",
        actor="RISK_ENGINE",
    )

    return analysis


@router.get("/factors")
def get_risk_factors():
    """
    Returns the deterministic scoring matrix, factor categories, and risk rules used by the engine.
    """
    return {
        "engine": "Explainable Risk Engine v1.0",
        "methodology": "Rule-Based Deterministic Multi-Factor Scoring (ML-Interface Compatible)",
        "score_range": "0 (safest) to 100 (critical)",
        "tiers": {
            "LOW": "0 - 29 (Safe to automate immediate recovery)",
            "MEDIUM": "30 - 59 (Standard automated recovery with retry backoff)",
            "HIGH": "60 - 79 (Requires customer interaction or delayed dunning)",
            "CRITICAL": "80 - 100 (High fraud/exposure risk - human review required)",
        },
        "supported_decline_categories": list(
            set(v["category"] for v in ExplainableRiskEngine.FAILURE_CODE_MAP.values())
        ),
    }
