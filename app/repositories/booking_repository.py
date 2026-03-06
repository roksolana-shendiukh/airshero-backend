from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.repositories.queries.booking_queries import (
    GET_BOOKING_STATUS_ID,
    GET_PAYMENT_STATUS_ID,
    INSERT_BOOKING,
    INSERT_BOOKING_ITEM,
    INSERT_BAGGAGE_OPTION,
    INSERT_PAYMENT,
    UPDATE_BOOKING_STATUS,
    GET_PAYMENT_METHODS,
)
from app.models.booking import CreateBookingDTO, PaymentDTO
from app.repositories import passenger_repository
from sqlalchemy import text
import time
from app.database import SessionLocal
import random
from app.services.email_service import send_booking_confirmation_email


def _get_status_id(db: Session, table: str, name: str) -> int:
    if table == 'booking':
        row = db.execute(GET_BOOKING_STATUS_ID, {"name": name}).fetchone()
    else:
        row = db.execute(GET_PAYMENT_STATUS_ID, {"name": name}).fetchone()
    if not row:
        raise ValueError(f"Status '{name}' not found in {table}Status table")
    return row[0]

def get_payment_methods(db: Session):
    return db.execute(GET_PAYMENT_METHODS).fetchall()

def generate_unique_booking_number(db: Session, max_attempts: int = 5) -> str:
    for _ in range(max_attempts):
        number = f"BK{random.randint(10_000_000, 99_999_999)}"
        exists = db.execute(
            text("SELECT 1 FROM Booking WHERE booking_number = :num"),
            {"num": number}
        ).fetchone()
        if not exists:
            return number
    raise ValueError("Failed to generate unique booking number")

def _get_or_create_document_id(db: Session, p_data) -> int:
    existing_doc = passenger_repository.get_document_by_number(db, p_data.document_number)

    if existing_doc:
        from app.models.passenger import PassengerUpdateDTO
        update_dto = PassengerUpdateDTO(**p_data.model_dump())
        passenger_repository.update_passenger(db, existing_doc.passenger_id, update_dto)
        return existing_doc.passenger_document_id  # ← беремо одразу з existing_doc
    else:
        from app.models.passenger import PassengerCreateDTO
        create_dto = PassengerCreateDTO(**p_data.model_dump())
        passenger_repository.create_passenger(db, create_dto)
        
        new_doc = passenger_repository.get_document_by_number(db, p_data.document_number)
        if not new_doc:
            raise ValueError(f"Document not found after creation: {p_data.document_number}")
        return new_doc.passenger_document_id
    
def _insert_booking_item_with_baggage(
    db: Session,
    booking_id: int,
    document_id: int,
    flight_price_id: int,
    baggage_items: list,
) -> None:
    """Inserts one BookingItem and its baggage rows."""
    db.execute(INSERT_BOOKING_ITEM, {
        "passenger_document_id": document_id,
        "booking_id": booking_id,
        "flight_price_id": flight_price_id,
    })

    booking_item_id = db.execute(
        text(
            "SELECT TOP 1 booking_item_id FROM BookingItem "
            "WHERE booking_id = :booking_id AND passenger_document_id = :doc_id "
            "AND flight_price_id = :fp_id "
            "ORDER BY booking_item_id DESC"
        ),
        {"booking_id": booking_id, "doc_id": document_id, "fp_id": flight_price_id},
    ).scalar()

    for baggage in baggage_items:
        db.execute(INSERT_BAGGAGE_OPTION, {
            "baggage_pricing_in_flight_id": baggage.baggage_pricing_in_flight_id,
            "booking_item_id": booking_item_id,
            "baggage_quantity": baggage.quantity,
        })

def create_booking(db: Session, data: CreateBookingDTO) -> dict:
    booking_number = generate_unique_booking_number(db)
    pending_status_id = _get_status_id(db, 'booking', 'Pending')

    booking_row = db.execute(INSERT_BOOKING, {
        "booking_status_id": pending_status_id,
        "total_amount": data.total_amount,
        "booking_number": booking_number,
    }).fetchone()
    booking_id = booking_row[0]

    for p_data in data.passengers:
        document_id = _get_or_create_document_id(db, p_data)

        _insert_booking_item_with_baggage(
            db, booking_id, document_id,
            p_data.flight_price_id,
            p_data.baggage_items,
        )

        if p_data.return_flight_price_id:
            _insert_booking_item_with_baggage(
                db, booking_id, document_id,
                p_data.return_flight_price_id,
                [],  
            )

    db.commit()

    print(f"[create_booking] booking_id={booking_id}, number={booking_number}, total_amount={data.total_amount}")

    expires_at = datetime.utcnow() + timedelta(minutes=10)
    return {
        "bookingId": booking_id,
        "bookingNumber": booking_number,
        "expiresAt": expires_at.isoformat() + "Z",
    }

def _build_flight_info(db, booking_id: int) -> dict:
    rows = db.execute(text("""
        SELECT
            f.flight_id,
            f.departs_datetime,
            f.arrives_datetime,
            dep_airport.airport_code AS dep_code,
            dep_city.city_name       AS dep_city,
            arr_airport.airport_code AS arr_code,
            arr_city.city_name       AS arr_city,
            p.passenger_first_name,
            p.passenger_last_name,
            c.class_name,
            fp.ticket_price,
            bof.baggage_quantity,
            bpf.baggage_price,
            bpf.baggage_pricing_in_flight_id
        FROM BookingItem bi
        JOIN FlightPrice fp       ON bi.flight_price_id = fp.flight_price_id
        JOIN FlightClass fc       ON fp.flight_class_id = fc.flight_class_id
        JOIN Class c              ON fc.class_id = c.class_id
        JOIN Flight f             ON fc.flight_id = f.flight_id
        JOIN FlightSchedule fs    ON f.flight_schedule_id = fs.flight_schedule_id
        JOIN Route r              ON fs.route_id = r.route_id
        JOIN Airport dep_airport  ON r.departs_airport_id = dep_airport.airport_id
        JOIN City dep_city        ON dep_airport.city_id = dep_city.city_id
        JOIN Airport arr_airport  ON r.arrives_airport_id = arr_airport.airport_id
        JOIN City arr_city        ON arr_airport.city_id = arr_city.city_id
        JOIN PassengerDocument pd ON bi.passenger_document_id = pd.passenger_document_id
        JOIN Passenger p          ON pd.passenger_id = p.passenger_id
        LEFT JOIN BaggageOptionInFlight bof  ON bof.booking_item_id = bi.booking_item_id
        LEFT JOIN BaggagePricingInFlight bpf ON bof.baggage_pricing_in_flight_id = bpf.baggage_pricing_in_flight_id
        WHERE bi.booking_id = :booking_id
    """), {"booking_id": booking_id}).fetchall()

    if not rows:
        return {'outbound': None, 'passengers': []}

    flights_seen = {}
    passengers = {}

    for row in rows:
        fid = row.flight_id
        if fid not in flights_seen:
            flights_seen[fid] = {
                'dep_time': row.departs_datetime.strftime('%H:%M'),
                'arr_time': row.arrives_datetime.strftime('%H:%M'),
                'dep_date': row.departs_datetime.strftime('%d %b %Y'),
                'arr_date': row.arrives_datetime.strftime('%d %b %Y'),
                'dep_code': row.dep_code,
                'dep_city': row.dep_city,
                'arr_code': row.arr_code,
                'arr_city': row.arr_city,
                'date':     row.departs_datetime,
            }

        pname = f"{row.passenger_first_name} {row.passenger_last_name}"
        if pname not in passengers:
            passengers[pname] = {
                'name':          pname,
                'class_name':    row.class_name,
                'ticket_prices': [],  
                'baggage_items': [],
            }

        passengers[pname]['ticket_prices'].append(float(row.ticket_price))

        if row.baggage_quantity and row.baggage_price:
            already = any(
                b.get('_id') == row.baggage_pricing_in_flight_id
                for b in passengers[pname]['baggage_items']
            )
            if not already:
                passengers[pname]['baggage_items'].append({
                    '_id':   row.baggage_pricing_in_flight_id,
                    'label': 'Checked baggage',
                    'count': row.baggage_quantity,
                    'price': float(row.baggage_price) * row.baggage_quantity,
                })
    flight_list = sorted(flights_seen.values(), key=lambda x: x['date'])
    result = {
        'outbound':   flight_list[0],
        'passengers': list(passengers.values()),
    }
    if len(flight_list) > 1:
        result['return'] = flight_list[1]

    return result

def process_payment(db: Session, booking_id: int, data: PaymentDTO) -> bool:
    if data.status == "paid" and data.email and data.passengerId:
        check = db.execute(
            text("""
                SELECT 1 FROM BookingItem bi
                JOIN PassengerDocument pd ON bi.passenger_document_id = pd.passenger_document_id
                WHERE bi.booking_id = :booking_id AND pd.passenger_id = :passenger_id
            """),
            {"booking_id": booking_id, "passenger_id": data.passengerId}
        ).fetchone()
        if not check:
            raise ValueError("Passenger does not belong to this booking")
        db.execute(
            text("UPDATE Passenger SET passenger_email = :email WHERE passenger_id = :id"),
            {"email": data.email, "id": data.passengerId}
        )

    if data.status == "paid":
        p_status_id = _get_status_id(db, 'payment', 'Paid')
    elif data.status == "pending":
        p_status_id = _get_status_id(db, 'payment', 'Pending')
    else:
        p_status_id = _get_status_id(db, 'payment', 'Failed')

    db.execute(INSERT_PAYMENT, {
        "booking_id":        booking_id,
        "payment_status_id": p_status_id,
        "payment_method_id": data.paymentMethodId,
        "payment_amount":    data.amount,
    })

    if data.status == "failed":
        cancelled_id = _get_status_id(db, 'booking', 'Cancelled')
        db.execute(UPDATE_BOOKING_STATUS, {
            "booking_status_id": cancelled_id,
            "booking_id":        booking_id,
        })
        db.commit()
        return True

    if data.status == "paid":
        paid_status_id = _get_status_id(db, 'payment', 'Paid')
        total_paid_res = db.execute(
            text("""
                SELECT SUM(payment_amount) FROM Payment 
                WHERE booking_id = :bid AND payment_status_id = :sid
            """),
            {"bid": booking_id, "sid": paid_status_id}
        ).scalar() or 0
        total_paid = float(total_paid_res)

        booking_data = db.execute(
            text("SELECT booking_total_amount, booking_number FROM Booking WHERE booking_id = :id"),
            {"id": booking_id}
        ).fetchone()

        if booking_data:
            booking_total = float(booking_data.booking_total_amount)

            if total_paid >= booking_total - 0.01:
                confirmed_id = _get_status_id(db, 'booking', 'Confirmed')
                db.execute(UPDATE_BOOKING_STATUS, {
                    "booking_status_id": confirmed_id,
                    "booking_id":        booking_id,
                })
                db.commit()

                if data.email:
                    try:
                        flight_info = _build_flight_info(db, booking_id)
                        details = {
                            "number": booking_data.booking_number,
                            "amount": booking_total,
                        }
                        send_booking_confirmation_email(data.email, booking_id, details, flight_info)
                    except Exception as e:
                        print(f"[email] Failed to send ticket: {e}")
            else:
                pending_id = _get_status_id(db, 'booking', 'Pending')
                db.execute(UPDATE_BOOKING_STATUS, {
                    "booking_status_id": pending_id,
                    "booking_id":        booking_id,
                })
                db.commit()

    return True

def cancel_booking_if_not_paid(booking_id: int):
    print(f"[cancel_booking_if_not_paid] Started for booking_id={booking_id}")
    time.sleep(600)

    db = SessionLocal()
    try:
        booking = db.execute(
            text("SELECT booking_status_id FROM Booking WHERE booking_id = :id"),
            {"id": booking_id}
        ).fetchone()

        pending_status_id = _get_status_id(db, 'booking', 'Pending')

        if booking and booking[0] == pending_status_id:
            cancelled_status_id = _get_status_id(db, 'booking', 'Cancelled')
            db.execute(UPDATE_BOOKING_STATUS, {
                "booking_status_id": cancelled_status_id,
                "booking_id": booking_id,
            })
            db.commit()
            print(f"[cancel_booking_if_not_paid] Booking {booking_id} cancelled")
        else:
            print(f"[cancel_booking_if_not_paid] Booking {booking_id} already paid, skipping")
    finally:
        db.close()

def get_adult_passengers_for_booking(db: Session, booking_id: int):
    rows = db.execute(text("""
        SELECT DISTINCT
            p.passenger_id,
            p.passenger_first_name,
            p.passenger_last_name,
            p.passenger_email,
            p.passenger_date_of_birth
        FROM BookingItem bi
        JOIN PassengerDocument pd ON bi.passenger_document_id = pd.passenger_document_id
        JOIN Passenger p ON pd.passenger_id = p.passenger_id
        WHERE bi.booking_id = :booking_id
    """), {"booking_id": booking_id}).fetchall()

    adults = []
    today = datetime.utcnow().date()

    for row in rows:
        age = today.year - row.passenger_date_of_birth.year - (
            (today.month, today.day) < (row.passenger_date_of_birth.month, row.passenger_date_of_birth.day)
        )
        if age >= 18:
            adults.append({
                "passengerId": row.passenger_id,
                "firstName":   row.passenger_first_name,
                "lastName":    row.passenger_last_name,
                "email":       row.passenger_email,
            })

    return adults



