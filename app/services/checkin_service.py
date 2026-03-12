from sqlalchemy.orm import Session
from app.repositories import checkin_repository


def get_passenger_booking(
    db: Session,
    document_number: str,
    flight_number: str,
    departs_date: str,
) -> list[dict]:
    rows = checkin_repository.get_passenger_booking(
        db, document_number, flight_number, departs_date
    )
    return [
        {
            "bookingId":              r["booking_id"],
            "bookingNumber":          r["booking_number"],
            "bookingStatus":          r["booking_status"],
            "passengerName":          r["passenger_name"],
            "passengerSurname":       r["passenger_surname"],
            "passengerDocumentNumber": r["passenger_document_number"],
            "className":              r["class_name"],
            "flightId":               r["flight_id"],
            "flightOperationId":      r["flight_operation_id"],
            "baggageQuantity":        r["baggage_quantity"],
            "baggagePrice":           float(r["baggage_price"]) if r["baggage_price"] else None,
        }
        for r in rows
    ]