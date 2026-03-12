from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import airfleet_service

router = APIRouter(prefix="/airfleets", tags=["Airfleets"])


@router.get("")
def get_airfleets(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    return airfleet_service.get_all_airfleets(db)