from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import route_service

router = APIRouter(tags=["Routes"])


@router.get("/routes")
def get_routes(
    db: Session = Depends(get_db),
    user=Depends(require_role("flightOperator")),
):
    airline_id = user.get("airlineId")
    if not airline_id:
        raise HTTPException(status_code=403, detail="No airline assigned to this user")
    return route_service.get_all_routes(db, airline_id=airline_id)