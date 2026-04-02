from sqlalchemy.orm import Session
from app.repositories import checkin_repository
import time
from fastapi import HTTPException


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
            "passengerDateOfBirth": str(r["passenger_date_of_birth"]) if r["passenger_date_of_birth"] else None,
            "classId":                 r["class_id"],
            "className":              r["class_name"],
            "flightId":               r["flight_id"],
            "flightOperationId":      r["flight_operation_id"],
            "bookingItemId":           r["booking_item_id"],
            "baggageQuantity":        r["baggage_quantity"],
            "baggagePrice":           float(r["baggage_price"]) if r["baggage_price"] else None,
        }
        for r in rows
    ]


def get_suggestions_for_flight(
    db: Session, 
    q: str, 
    flight_number: str, 
    departs_date: str
):
    return checkin_repository.get_suggestions_for_flight(
        db, q, flight_number, departs_date
    )



def calculate_baggage_surcharge(db: Session, booking_item_id: int, bag_weights: list[float]) -> dict:
    flight_info = checkin_repository.get_flight_info_for_booking_item(db, booking_item_id)
    if not flight_info:
        raise HTTPException(status_code=404, detail="Flight info missing")

    allowance = checkin_repository.get_booking_baggage_allowance(db, booking_item_id)
    
    prepaid_qty = (allowance.get("baggage_quantity") if allowance else 0) or 0
    prepaid_max_w = float(allowance.get("baggage_max_weight") or 0.0) if allowance else 0.0
    prepaid_overweight_fee = float(allowance.get("overweight_fee_per_kg") or 0.0) if allowance else 0.0

    rules = checkin_repository.get_flight_class_baggage_rules(db, flight_info["flight_class_id"])
    if not rules:
        rules = [{"baggage_type_id": 0, "baggage_max_weight": 23.0, "baggage_price": 50.0, "overweight_fee_per_kg": 15.0, "baggage_type_name": "Standard"}]

    total_surcharge = 0.0
    bags_result = []

    for i, w in enumerate(bag_weights):
        applied_rule = next((r for r in rules if w <= float(r["baggage_max_weight"])), rules[-1])
        
        surcharge_for_bag = 0.0
        msg = ""

        if i < prepaid_qty:
            if w <= prepaid_max_w + 0.5:
                surcharge_for_bag = 0.0
                msg = "Included"
            else:
                surcharge_for_bag = float(applied_rule["baggage_price"])
                msg = f"Exceeded {prepaid_max_w}kg. Full price applied."
        else:
            surcharge_for_bag = float(applied_rule["baggage_price"])
            if w > float(applied_rule["baggage_max_weight"]):
                over = w - float(applied_rule["baggage_max_weight"])
                surcharge_for_bag += over * float(applied_rule["overweight_fee_per_kg"])
            msg = "Extra bag"

        total_surcharge += surcharge_for_bag
        bags_result.append({
            "weight": w,
            "determinedTypeId": applied_rule["baggage_type_id"],
            "determinedTypeName": applied_rule["baggage_type_name"],
            "determinedDimensions": applied_rule["baggage_dimension"],
            "isPreBookedSlot": i < prepaid_qty,
            "surcharge": surcharge_for_bag,
            "message": msg
        })

    return {
        "totalSurcharge": total_surcharge,
        "bags": bags_result
    }


