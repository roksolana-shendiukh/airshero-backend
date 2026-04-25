import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.booking_schema import CreateBookingDTO, CreateGroupBookingDTO, ReserveBookingDTO, ReserveGroupBookingDTO, UpdatePassengersDTO
from app.repositories import booking_repository
from app.services import passenger_service


def _insert_booking_item_with_baggage(
    db: Session,
    booking_id: int,
    document_id: int,
    flight_price_id: int,
    baggage_items: list,
) -> None:
    item = booking_repository.insert_booking_item(db, booking_id, document_id, flight_price_id)
    for baggage in baggage_items:
        booking_repository.insert_baggage_option(
            db,
            booking_item_id=item.booking_item_id,
            baggage_pricing_in_flight_id=baggage.baggage_pricing_in_flight_id,
            baggage_quantity=baggage.quantity,
        )


def _build_flight_info(db: Session, booking_id: int) -> dict:
    rows = booking_repository.get_booking_flight_info_rows(db, booking_id)
    if not rows:
        return {"outbound": None, "passengers": []}

    flights_seen: dict = {}
    passengers: dict = {}

    for row in rows:
        fid = row.flight_id
        if fid not in flights_seen:
            flights_seen[fid] = {
                "dep_time": row.departs_datetime.strftime("%H:%M"),
                "arr_time": row.arrives_datetime.strftime("%H:%M"),
                "dep_date": row.departs_datetime.strftime("%d %b %Y"),
                "arr_date": row.arrives_datetime.strftime("%d %b %Y"),
                "dep_code": row.dep_code,
                "dep_city": row.dep_city,
                "arr_code": row.arr_code,
                "arr_city": row.arr_city,
                "date":     row.departs_datetime,
            }

        pname = f"{row.passenger_first_name} {row.passenger_last_name}"
        if pname not in passengers:
            passengers[pname] = {
                "name":          pname,
                "class_name":    row.class_name,
                "ticket_prices": [],
                "baggage_items": [],
            }

        passengers[pname]["ticket_prices"].append(float(row.ticket_price))

        if row.baggage_quantity and row.baggage_price:
            already = any(
                b.get("_id") == row.baggage_pricing_in_flight_id
                for b in passengers[pname]["baggage_items"]
            )
            if not already:
                passengers[pname]["baggage_items"].append({
                    "_id":   row.baggage_pricing_in_flight_id,
                    "label": "Checked baggage",
                    "count": row.baggage_quantity,
                    "price": float(row.baggage_price) * row.baggage_quantity,
                })

    flight_list = sorted(flights_seen.values(), key=lambda x: x["date"])
    result = {"outbound": flight_list[0], "passengers": list(passengers.values())}
    if len(flight_list) > 1:
        result["return"] = flight_list[1]
    return result


def create_booking(db: Session, data: CreateBookingDTO, auto_commit: bool = True) -> dict:
    from collections import Counter
    flight_price_counts: Counter = Counter()
    for p_data in data.passengers:
        flight_price_counts[p_data.flight_price_id] += 1
        if p_data.return_flight_price_id:
            flight_price_counts[p_data.return_flight_price_id] += 1

    for flight_price_id, required in flight_price_counts.items():
        is_available, message = booking_repository.check_seat_availability(
            db, flight_price_id, required
        )
        if not is_available:
            raise ValueError(message)

    booking_number = booking_repository.generate_unique_booking_number(db)
    pending_status_id = booking_repository.get_booking_status_id(db, "Pending")

    booking = booking_repository.insert_booking(
        db, pending_status_id, data.total_amount, booking_number
    )

    for p_data in data.passengers:
        document_id = passenger_service.get_or_create_document_id(db, p_data)
        _insert_booking_item_with_baggage(
            db, booking.booking_id, document_id,
            p_data.flight_price_id, p_data.baggage_items,
        )
        if p_data.return_flight_price_id:
            _insert_booking_item_with_baggage(
                db, booking.booking_id, document_id,
                p_data.return_flight_price_id, [],
            )

    if auto_commit:
        db.commit()

    expires_at = datetime.now() + timedelta(minutes=30)
    return {
        "bookingId":     booking.booking_id,
        "bookingNumber": booking_number,
        "expiresAt":     expires_at.isoformat(),
    }

def create_group_booking(db: Session, data: CreateGroupBookingDTO) -> dict:
    try:
        b1 = create_booking(db, data.booking1, auto_commit=False)
        b2 = create_booking(db, data.booking2, auto_commit=False)
        db.commit()

        expires_at = datetime.now() + timedelta(minutes=30)

        return {
            "booking1":  b1,
            "booking2":  b2,
            "expiresAt": expires_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        raise ValueError(str(e))


def validate_booking_for_payment(db: Session, booking_id: int) -> None:
    booking = booking_repository.get_booking_by_id(db, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    status_name = booking.status.booking_status_name
    if status_name == "Cancelled":
        raise ValueError("Booking has been cancelled — payment window expired")
    if status_name != "Pending":
        raise ValueError(f"Booking cannot be paid — current status: {status_name}")


def get_adult_passengers_for_booking(db: Session, booking_id: int) -> list[dict]:
    rows = booking_repository.get_adult_passengers(db, booking_id)
    today = datetime.now().date()
    result = []
    for row in rows:
        dob = row.passenger_date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age >= 18:
            result.append({
                "passengerId": row.passenger_id,
                "firstName":   row.passenger_first_name,
                "lastName":    row.passenger_last_name,
                "email":       row.passenger_email,
            })
    return result


def cancel_booking_if_not_paid(booking_id: int) -> None:
    print(f"[cancel_booking_if_not_paid] Started for booking_id={booking_id}")
    time.sleep(1800)

    db = SessionLocal()
    try:
        booking = booking_repository.get_booking_by_id(db, booking_id)
        if not booking:
            return
        pending_status_id = booking_repository.get_booking_status_id(db, "Pending")
        if booking.booking_status_id == pending_status_id:
            cancelled_id = booking_repository.get_booking_status_id(db, "Cancelled")
            booking_repository.update_booking_status(db, booking_id, cancelled_id)
            db.commit()
            print(f"[cancel_booking_if_not_paid] Booking {booking_id} cancelled")
        else:
            print(f"[cancel_booking_if_not_paid] Booking {booking_id} already paid, skipping")
    finally:
        db.close()


def cancel_group_booking_if_not_paid(booking_id_1: int, booking_id_2: int) -> None:
    print(f"[cancel_group_booking_if_not_paid] Started for bookings {booking_id_1}, {booking_id_2}")
    time.sleep(1800)

    db = SessionLocal()
    try:
        pending_status_id = booking_repository.get_booking_status_id(db, "Pending")
        cancelled_id = booking_repository.get_booking_status_id(db, "Cancelled")

        for booking_id in [booking_id_1, booking_id_2]:
            booking = booking_repository.get_booking_by_id(db, booking_id)
            if not booking:
                continue
            if booking.booking_status_id == pending_status_id:
                booking_repository.update_booking_status(db, booking_id, cancelled_id)
                print(f"[cancel_group_booking_if_not_paid] Booking {booking_id} cancelled")
            else:
                print(f"[cancel_group_booking_if_not_paid] Booking {booking_id} already paid, skipping")

        db.commit()
    finally:
        db.close()


def reserve_booking(db: Session, data, auto_commit: bool = True) -> dict:
    from collections import Counter
    flight_price_counts: Counter = Counter()
    for p in data.passengers:
        flight_price_counts[p.flight_price_id] += 1
        if p.return_flight_price_id:
            flight_price_counts[p.return_flight_price_id] += 1

    for flight_price_id, required in flight_price_counts.items():
        is_available, message = booking_repository.check_seat_availability(
            db, flight_price_id, required
        )
        if not is_available:
            raise ValueError(message)

    booking_number = booking_repository.generate_unique_booking_number(db)
    pending_status_id = booking_repository.get_booking_status_id(db, "Pending")

    booking = booking_repository.insert_booking(
        db, pending_status_id, data.total_amount, booking_number
    )

    for p in data.passengers:
        booking_repository.insert_booking_item_no_passenger(
            db, booking.booking_id, p.flight_price_id
        )
        if p.return_flight_price_id:
            booking_repository.insert_booking_item_no_passenger(
                db, booking.booking_id, p.return_flight_price_id
            )

    if auto_commit:
        db.commit()

    expires_at = datetime.now() + timedelta(minutes=30)
    return {
        "bookingId": booking.booking_id,
        "bookingNumber": booking_number,
        "expiresAt": expires_at.isoformat(),
    }


def reserve_group_booking(db: Session, data) -> dict:
    try:
        b1 = reserve_booking(db, data.booking1, auto_commit=False)
        b2 = reserve_booking(db, data.booking2, auto_commit=False)
        db.commit()
        expires_at = datetime.now() + timedelta(minutes=30)
        return {
            "booking1": b1,
            "booking2": b2,
            "expiresAt": expires_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        raise ValueError(str(e))
    

def update_booking_passengers(db: Session, booking_id: int, data: UpdatePassengersDTO) -> None:
    booking = booking_repository.get_booking_by_id(db, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    booking_repository.delete_booking_items(db, booking_id)

    for p_data in data.passengers:
        document_id = passenger_service.get_or_create_document_id(db, p_data)
        _insert_booking_item_with_baggage(
            db, booking_id, document_id,
            p_data.flight_price_id, p_data.baggage_items,
        )
        if p_data.return_flight_price_id:
            _insert_booking_item_with_baggage(
                db, booking_id, document_id,
                p_data.return_flight_price_id, [],
            )

    if data.total_amount is not None:
        booking_repository.update_booking_amount(db, booking_id, data.total_amount)

    db.commit()


def get_bookings(db, skip=0, limit=50, status=None, airline_name=None, date_filter='this_month'):
    return booking_repository.get_bookings(
        db, skip=skip, limit=limit,
        status=status,
        airline_name=airline_name,
        date_filter=date_filter,
    )


def cancel_booking(db: Session, booking_id: int):
    booking = booking_repository.get_booking_by_id(db, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    cancellable_statuses = ["Confirmed", "Pending", "PartiallyPaid"]
    if booking.status.booking_status_name not in cancellable_statuses:
        raise ValueError("Booking cannot be cancelled")

    flight_date = booking_repository.get_earliest_flight_date(db, booking_id)
    if flight_date and flight_date <= datetime.now() + timedelta(hours=3):
        raise ValueError("Cannot cancel booking — less than 3 hours before departure")

    cancelled_id = booking_repository.get_booking_status_id(db, "Cancelled")
    booking_repository.update_booking_status(db, booking_id, cancelled_id)
    db.commit()

