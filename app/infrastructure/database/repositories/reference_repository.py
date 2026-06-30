from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.database.models.passenger_model import Citizenship
from app.infrastructure.database.models.passenger_model import DocumentType

from app.infrastructure.database.models.payment_model import PaymentMethod, PaymentStatus
from app.infrastructure.database.models.baggage_model import BaggageType


def get_citizenships(db: Session, query: str | None = None) -> list:
    rows = db.query(Citizenship)
    if query:
        rows = rows.filter(Citizenship.citizenship_name.ilike(f"%{query}%"))
    return rows.order_by(Citizenship.citizenship_name).all()


def get_document_types(db: Session, flight_id: int | None = None) -> list:
    is_international = False

    if flight_id is not None:
        row = db.execute(text("""
            SELECT
                dep_country.country_id AS dep_country_id,
                arr_country.country_id AS arr_country_id
            FROM Flight f
            JOIN FlightSchedule fs   ON f.flight_schedule_id = fs.flight_schedule_id
            JOIN Route r             ON fs.route_id = r.route_id
            JOIN Airport dep_air     ON r.departs_airport_id = dep_air.airport_id
            JOIN City dep_city       ON dep_air.city_id = dep_city.city_id
            JOIN Airport arr_air     ON r.arrives_airport_id = arr_air.airport_id
            JOIN City arr_city       ON arr_air.city_id = arr_city.city_id
            JOIN Country dep_country ON dep_city.country_id = dep_country.country_id
            JOIN Country arr_country ON arr_city.country_id = arr_country.country_id
            WHERE f.flight_id = :flight_id
        """), {"flight_id": flight_id}).fetchone()

        if row:
            is_international = row.dep_country_id != row.arr_country_id

    allowed_codes = {"INT", "OFF"} if is_international else {"ID", "PAS"}
    rows = db.query(DocumentType).all()
    return [r for r in rows if r.document_type_code in allowed_codes]


def get_payment_methods(db: Session) -> list:
    return db.query(PaymentMethod).all()


def get_payment_statuses(db: Session) -> list:
    return db.query(PaymentStatus).all()


def get_baggage_types(db: Session) -> list:
    return db.query(BaggageType).all()