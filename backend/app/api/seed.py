"""
Demo Seed & Database Management API Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.seed_service import SeedService

router = APIRouter(prefix="/seed", tags=["Demo Data & Sandbox"])


@router.post("", status_code=201)
def seed_demo_dataset(db: Session = Depends(get_db)):
    """
    Populates realistic multi-scenario payment, recovery, and audit records for demonstration.
    """
    result = SeedService.seed_demo_data(db)
    return result


@router.post("/clear")
def clear_demo_dataset(db: Session = Depends(get_db)):
    """
    Wipes all database records to return RecoverAI to a 100% clean empty state.
    """
    result = SeedService.clear_all_data(db)
    return result
