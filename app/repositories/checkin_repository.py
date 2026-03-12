from sqlalchemy.orm import Session
from sqlalchemy import text


def get_passenger_booking(
    db: Session,
    document_number: str,
    flight_number: str,
    departs_date: str,
):
    result = db.execute(
        text("EXEC SP_GetPassengerBooking :document_number, :flight_number, :departs_date"),
        {
            "document_number": document_number,
            "flight_number":   flight_number,
            "departs_date":    departs_date,
        },
    )
    return result.mappings().all()