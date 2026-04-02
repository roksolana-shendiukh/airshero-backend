import random
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from app.models.booking_model import Booking, BookingItem, BookingStatus
from app.models.baggage_model import BaggageOptionInFlight


def get_booking_status_id(db: Session, name: str) -> int:
    row = (
        db.query(BookingStatus.booking_status_id)
        .filter(BookingStatus.booking_status_name == name)
        .scalar()
    )
    if row is None:
        raise ValueError(f"BookingStatus '{name}' not found")
    return row


def generate_unique_booking_number(db: Session, max_attempts: int = 5) -> str:
    for _ in range(max_attempts):
        number = f"BK{random.randint(10_000_000, 99_999_999)}"
        exists = (
            db.query(Booking.booking_id)
            .filter(Booking.booking_number == number)
            .scalar()
        )
        if not exists:
            return number
    raise ValueError("Failed to generate unique booking number")


from datetime import datetime

def insert_booking(
    db: Session,
    booking_status_id: int,
    total_amount: float,
    booking_number: str,
) -> Booking:
    booking = Booking(
        booking_status_id=booking_status_id,
        booking_total_amount=total_amount,
        booking_number=booking_number,
        booking_date_time=datetime.now(),
    )
    db.add(booking)
    db.flush()
    return booking


def insert_booking_item(
    db: Session,
    booking_id: int,
    passenger_document_id: int,
    flight_price_id: int,
) -> BookingItem:
    item = BookingItem(
        booking_id=booking_id,
        passenger_document_id=passenger_document_id,
        flight_price_id=flight_price_id,
    )
    db.add(item)
    db.flush()
    return item


def insert_baggage_option(
    db: Session,
    booking_item_id: int,
    baggage_pricing_in_flight_id: int,
    baggage_quantity: int,
) -> None:
    option = BaggageOptionInFlight(
        booking_item_id=booking_item_id,
        baggage_pricing_in_flight_id=baggage_pricing_in_flight_id,
        baggage_quantity=baggage_quantity,
    )
    db.add(option)


def update_booking_status(db: Session, booking_id: int, booking_status_id: int) -> None:
    db.query(Booking).filter(Booking.booking_id == booking_id).update(
        {"booking_status_id": booking_status_id}
    )


def get_booking_by_id(db: Session, booking_id: int) -> Booking | None:
    return (
        db.query(Booking)
        .options(joinedload(Booking.status))
        .filter(Booking.booking_id == booking_id)
        .first()
    )


def check_passenger_in_booking(db: Session, booking_id: int, passenger_id: int) -> bool:
    return (
        db.query(BookingItem)
        .join(BookingItem.passenger_document)
        .filter(
            BookingItem.booking_id == booking_id,
            text("PassengerDocument.passenger_id = :pid"),
        )
        .params(pid=passenger_id)
        .first()
    ) is not None


def update_passenger_email(db: Session, passenger_id: int, email: str) -> None:
    db.execute(
        text("UPDATE Passenger SET passenger_email = :email WHERE passenger_id = :id"),
        {"email": email, "id": passenger_id},
    )


def get_adult_passengers(db: Session, booking_id: int) -> list:
    return db.execute(text("""
        SELECT DISTINCT
            p.passenger_id,
            p.passenger_first_name,
            p.passenger_last_name,
            p.passenger_email,
            p.passenger_date_of_birth
        FROM BookingItem bi
        JOIN PassengerDocument pd ON bi.passenger_document_id = pd.passenger_document_id
        JOIN Passenger p          ON pd.passenger_id = p.passenger_id
        WHERE bi.booking_id = :booking_id
    """), {"booking_id": booking_id}).fetchall()


def get_booking_flight_info_rows(db: Session, booking_id: int) -> list:
    return db.execute(text("""
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
        JOIN FlightPrice fp          ON bi.flight_price_id = fp.flight_price_id
        JOIN FlightClass fc          ON fp.flight_class_id = fc.flight_class_id
        JOIN Class c                 ON fc.class_id = c.class_id
        JOIN Flight f                ON fc.flight_id = f.flight_id
        JOIN FlightSchedule fs       ON f.flight_schedule_id = fs.flight_schedule_id
        JOIN Route r                 ON fs.route_id = r.route_id
        JOIN Airport dep_airport     ON r.departs_airport_id = dep_airport.airport_id
        JOIN City dep_city           ON dep_airport.city_id = dep_city.city_id
        JOIN Airport arr_airport     ON r.arrives_airport_id = arr_airport.airport_id
        JOIN City arr_city           ON arr_airport.city_id = arr_city.city_id
        JOIN PassengerDocument pd    ON bi.passenger_document_id = pd.passenger_document_id
        JOIN Passenger p             ON pd.passenger_id = p.passenger_id
        LEFT JOIN BaggageOptionInFlight bof  ON bof.booking_item_id = bi.booking_item_id
        LEFT JOIN BaggagePricingInFlight bpf ON bof.baggage_pricing_in_flight_id = bpf.baggage_pricing_in_flight_id
        WHERE bi.booking_id = :booking_id
    """), {"booking_id": booking_id}).fetchall()