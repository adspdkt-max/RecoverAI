"""
Master API Router
"""
from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.payments import router as payments_router
from app.api.risk import router as risk_router
from app.api.recovery import router as recovery_router
from app.api.webhooks import router as webhooks_router
from app.api.dashboard import router as dashboard_router
from app.api.analytics import router as analytics_router
from app.api.customers import router as customers_router
from app.api.audit import router as audit_router
from app.api.seed import router as seed_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(payments_router)
api_router.include_router(risk_router)
api_router.include_router(recovery_router)
api_router.include_router(webhooks_router)
api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(customers_router)
api_router.include_router(audit_router)
api_router.include_router(seed_router)
