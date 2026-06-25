from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.services import booking_service, payment_service
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.booking_schema import (
    CreateBookingDTO,
    BookingResponseDTO,
    CreateGroupBookingDTO,
    ReserveBookingDTO,
    ReserveGroupBookingDTO,
    UpdatePassengersDTO,
)
from app.interfaces.schemas.payment_schema import PaymentDTO

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", status_code=200)
def get_bookings(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    date_filter: str | None = "this_month",
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return booking_service.get_bookings(
        db, skip=skip, limit=limit,
        status=status,
        date_filter=date_filter,
    )


@router.post("", response_model=BookingResponseDTO, status_code=201)
def create_booking(
    data: CreateBookingDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = booking_service.create_booking(db, data)
        background_tasks.add_task(
            booking_service.cancel_booking_if_not_paid,
            result["booking_id"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking creation failed: " + str(e.orig))


@router.post("/group", status_code=201)
def create_group_booking(
    data: CreateGroupBookingDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = booking_service.create_group_booking(db, data)
        background_tasks.add_task(
            booking_service.cancel_group_booking_if_not_paid,
            result["booking1"]["booking_id"],
            result["booking2"]["booking_id"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Group booking creation failed: " + str(e.orig))


@router.post("/reserve", response_model=BookingResponseDTO, status_code=201)
def reserve_booking(
    data: ReserveBookingDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = booking_service.reserve_booking(db, data)
        background_tasks.add_task(
            booking_service.cancel_booking_if_not_paid,
            result["booking_id"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking reservation failed: " + str(e.orig))


@router.post("/reserve/group", status_code=201)
def reserve_group_booking(
    data: ReserveGroupBookingDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = booking_service.reserve_group_booking(db, data)
        background_tasks.add_task(
            booking_service.cancel_group_booking_if_not_paid,
            result["booking1"]["booking_id"],
            result["booking2"]["booking_id"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Group booking reservation failed: " + str(e.orig))


@router.post("/{booking_id}/payment")
def process_payment(
    booking_id: int,
    data: PaymentDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        booking_service.validate_booking_for_payment(db, booking_id)
        payment_service.process_payment(db, booking_id, data)
        return {"success": True}
    except ValueError as e:
        msg = str(e).lower()
        if "cancelled" in msg:
            raise HTTPException(status_code=409, detail="booking_expired")
        if "not found" in msg:
            raise HTTPException(status_code=404, detail="booking_not_found")
        raise HTTPException(status_code=409, detail="booking_unavailable")


@router.get("/{booking_id}/adult-passengers")
def get_adult_passengers(
    booking_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return booking_service.get_adult_passengers_for_booking(db, booking_id)


@router.patch("/{booking_id}/passengers", status_code=200)
def update_booking_passengers(
    booking_id: int,
    data: UpdatePassengersDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        booking_service.update_booking_passengers(db, booking_id, data)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.post("/{booking_id}/cancel", status_code=200)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        booking_service.cancel_booking(db, booking_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))