from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import require_role
from sqlalchemy import text
from app.models.document_type_model import DocumentType

router = APIRouter(tags=["References"])

@router.get("/citizenships")
def get_citizenships(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = db.execute(text("SELECT citizenship_id, citizenship_name FROM Citizenship")).fetchall()
    return [{"citizenshipId": row.citizenship_id, "citizenshipName": row.citizenship_name} for row in rows]

@router.get("/document-types")
def get_document_types(
    flight_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    is_international = False

    if flight_id is not None:
        row = db.execute(text("""
            SELECT
                dep_country.country_id AS dep_country_id,
                arr_country.country_id AS arr_country_id
            FROM Flight f
            JOIN FlightSchedule fs  ON f.flight_schedule_id = fs.flight_schedule_id
            JOIN Route r            ON fs.route_id = r.route_id
            JOIN Airport dep_air    ON r.departs_airport_id = dep_air.airport_id
            JOIN City dep_city      ON dep_air.city_id = dep_city.city_id
            JOIN Airport arr_air    ON r.arrives_airport_id = arr_air.airport_id
            JOIN City arr_city      ON arr_air.city_id = arr_city.city_id
            JOIN Country dep_country ON dep_city.country_id = dep_country.country_id
            JOIN Country arr_country ON arr_city.country_id = arr_country.country_id
            WHERE f.flight_id = :flight_id
        """), {"flight_id": flight_id}).fetchone()

        if row:
            is_international = row.dep_country_id != row.arr_country_id

    regional_codes      = {'ID', 'PAS'}
    international_codes = {'INT', 'OFF'}
    allowed_codes       = international_codes if is_international else regional_codes

    rows = db.query(DocumentType).all()
    return [
        {
            "documentTypeId":   row.document_type_id,
            "documentTypeName": row.document_type_name,
            "documentTypeCode": row.document_type_code,
        }
        for row in rows
        if row.document_type_code in allowed_codes
    ]

@router.get("/sexes")
def get_sexes():
    return [
        {"id": 0, "name": "Female"},
        {"id": 1, "name": "Male"},
    ]

@router.get("/payment-methods")
def get_payment_methods(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = db.execute(text("SELECT payment_method_id, payment_method_name FROM PaymentMethod")).fetchall()
    return [{"paymentMethodId": row.payment_method_id, "paymentMethodName": row.payment_method_name} for row in rows]


@router.get("/payment-statuses")
def get_payment_statuses(
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    rows = db.execute(text("SELECT payment_status_id, payment_status_name FROM PaymentStatus")).fetchall()
    return [{"paymentStatusId": row.payment_status_id, "paymentStatusName": row.payment_status_name} for row in rows]
