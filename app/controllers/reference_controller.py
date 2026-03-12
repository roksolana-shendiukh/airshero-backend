from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import reference_service

router = APIRouter(tags=["References"])


@router.get("/citizenships")
def get_citizenships(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return reference_service.get_citizenships(db)


@router.get("/document-types")
def get_document_types(
    flight_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return reference_service.get_document_types(db, flight_id)


@router.get("/sexes")
def get_sexes():
    return reference_service.get_sexes()


@router.get("/payment-methods")
def get_payment_methods(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return reference_service.get_payment_methods(db)


@router.get("/payment-statuses")
def get_payment_statuses(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return reference_service.get_payment_statuses(db)