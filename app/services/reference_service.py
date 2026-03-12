from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document_model import DocumentType
from app.models.citizenship_model import Citizenship
from app.models.payment_model import PaymentMethod, PaymentStatus


def get_citizenships(db: Session) -> list[dict]:
    rows = db.query(Citizenship).all()
    return [
        {"citizenshipId": r.citizenship_id, "citizenshipName": r.citizenship_name}
        for r in rows
    ]


def get_document_types(db: Session, flight_id: int | None = None) -> list[dict]:
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
    return [
        {
            "documentTypeId":   r.document_type_id,
            "documentTypeName": r.document_type_name,
            "documentTypeCode": r.document_type_code,
        }
        for r in rows
        if r.document_type_code in allowed_codes
    ]


def get_payment_methods(db: Session) -> list[dict]:
    rows = db.query(PaymentMethod).all()
    return [
        {"paymentMethodId": r.payment_method_id, "paymentMethodName": r.payment_method_name}
        for r in rows
    ]


def get_payment_statuses(db: Session) -> list[dict]:
    rows = db.query(PaymentStatus).all()
    return [
        {"paymentStatusId": r.payment_status_id, "paymentStatusName": r.payment_status_name}
        for r in rows
    ]


def get_sexes() -> list[dict]:
    return [{"id": 0, "name": "Female"}, {"id": 1, "name": "Male"}]