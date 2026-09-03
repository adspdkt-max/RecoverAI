"""
Health Check and Diagnostics API
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.config import APP_TITLE, APP_VERSION, ENVIRONMENT

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """
    Returns system health status and database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }
