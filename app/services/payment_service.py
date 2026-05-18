from sqlalchemy.orm import Session
from app.schemas.payment_schema import PaymentDTO
from app.repositories import booking_repository, payment_repository
from app.services.email_service import send_booking_confirmation_email
from app.services.booking_service import _build_flight_info
                    


def process_payment(db: Session, booking_id: int, data: PaymentDTO) -> bool:
    status_map = {"paid": "Paid", "pending": "Pending"}
    payment_status_name = status_map.get(data.status, "Failed")
    p_status_id = payment_repository.get_payment_status_id(db, payment_status_name)

    payment_repository.insert_payment(
        db,
        booking_id=booking_id,
        payment_status_id=p_status_id,
        payment_method_id=data.paymentMethodId,
        payment_amount=data.amount,
    )

    if data.status == "failed":
        cancelled_id = booking_repository.get_booking_status_id(db, "Cancelled")
        booking_repository.update_booking_status(db, booking_id, cancelled_id)
        db.commit()
        return True

    if data.status == "paid":
        paid_status_id = payment_repository.get_payment_status_id(db, "Paid")
        total_paid = payment_repository.get_total_paid(db, booking_id, paid_status_id)

        booking = booking_repository.get_booking_by_id(db, booking_id)
        if not booking:
            return False

        booking_total = float(booking.booking_total_amount)

        if total_paid >= booking_total - 0.01:
            confirmed_id = booking_repository.get_booking_status_id(db, "Confirmed")
            booking_repository.update_booking_status(db, booking_id, confirmed_id)
            db.commit()

            try:
                flight_info = _build_flight_info(db, booking_id)
                details = {"number": booking.booking_number, "amount": booking_total}

                flight_info_2 = None
                details_2 = None
                if data.booking_id_2:
                    booking_2 = booking_repository.get_booking_by_id(db, data.booking_id_2)
                    if booking_2:
                        flight_info_2 = _build_flight_info(db, data.booking_id_2)
                        details_2 = {
                            "number": booking_2.booking_number,
                            "amount": float(booking_2.booking_total_amount),
                        }

                passengers_with_email = booking_repository.get_passengers_with_email(db, booking_id)
                for passenger in passengers_with_email:
                    send_booking_confirmation_email(
                        passenger['email'],
                        booking_id,
                        details,
                        flight_info,
                        booking_id_2=data.booking_id_2,
                        flight_info_2=flight_info_2,
                        booking_details_2=details_2,
                    )
            except Exception as e:
                print(f"[email] Failed to send ticket: {e}")
        else:
            pending_id = booking_repository.get_booking_status_id(db, "Pending")
            booking_repository.update_booking_status(db, booking_id, pending_id)
            db.commit()

    return True


