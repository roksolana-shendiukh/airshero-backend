from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.dependencies.auth import require_role
from app.models.booking import CreateBookingDTO, BookingResponseDTO, PaymentDTO
from app.repositories import booking_repository
from sqlalchemy import text

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/payment-methods")
def get_payment_methods(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = booking_repository.get_payment_methods(db)
    return [
        {
            "paymentMethodId": row.payment_method_id,
            "paymentMethodName": row.payment_method_name,
        }
        for row in rows
    ]

@router.post("", response_model=BookingResponseDTO, status_code=201)
def create_booking(
    data: CreateBookingDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    try:
        result = booking_repository.create_booking(db, data)
        
        background_tasks.add_task(
            booking_repository.cancel_booking_if_not_paid, 
            result["bookingId"]
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

@router.post("/{booking_id}/payment")
def process_payment(
    booking_id: int,
    data: PaymentDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    row = db.execute(
        text("""
            SELECT b.booking_status_id, bs.booking_status_name
            FROM Booking b
            JOIN BookingStatus bs ON b.booking_status_id = bs.booking_status_id
            WHERE b.booking_id = :id
        """),
        {"id": booking_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    if row.booking_status_name == "Cancelled":
        raise HTTPException(
            status_code=409,
            detail="Booking has been cancelled — payment window expired"
        )

    if row.booking_status_name not in ("Pending",):
        raise HTTPException(
            status_code=409,
            detail=f"Booking cannot be paid — current status: {row.booking_status_name}"
        )

    try:
        booking_repository.process_payment(db, booking_id, data)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
  
@router.get("/{booking_id}/adult-passengers")
def get_adult_passengers(
    booking_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    return booking_repository.get_adult_passengers_for_booking(db, booking_id)

@router.put("/passengers/{passenger_id}/email")
def update_passenger_email(
    passenger_id: int,
    email: str,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    db.execute(text("""
        UPDATE Passenger
        SET email = :email
        WHERE passenger_id = :id
    """), {"email": email, "id": passenger_id})

    db.commit()
    return {"success": True}
