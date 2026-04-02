from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.dependencies.auth import require_role
from app.schemas.booking_schema import CreateBookingDTO, BookingResponseDTO, CreateGroupBookingDTO
from app.schemas.payment_schema import PaymentDTO
from app.services import booking_service, payment_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


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
            result["bookingId"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking creation failed: " + str(e.orig))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
            result["booking1"]["bookingId"],
            result["booking2"]["bookingId"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Group booking creation failed: " + str(e.orig))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        db.rollback()
        import traceback
        print(f"PAYMENT ERROR: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="payment_error")


@router.get("/{booking_id}/adult-passengers")
def get_adult_passengers(
    booking_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return booking_service.get_adult_passengers_for_booking(db, booking_id)

