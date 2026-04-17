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

    prepaid_qty          = (allowance.get("baggage_quantity") if allowance else 0) or 0
    prepaid_max_w        = float(allowance.get("baggage_max_weight") or 0.0) if allowance else 0.0
    prepaid_overweight_fee = float(allowance.get("overweight_fee_per_kg") or 0.0) if allowance else 0.0

    rules = checkin_repository.get_flight_class_baggage_rules(db, flight_info["flight_class_id"])
    if not rules:
        rules = [{
            "baggage_type_id":       0,
            "baggage_max_weight":    23.0,
            "baggage_price":         50.0,
            "overweight_fee_per_kg": 15.0,
            "baggage_type_name":     "Standard",
            "baggage_dimension":     "—",
        }]

    total_surcharge = 0.0
    bags_result     = []

    for i, w in enumerate(bag_weights):
        fitting_rule = next(
            (r for r in rules if w <= float(r["baggage_max_weight"])),
            None
        )

        surcharge_for_bag = 0.0
        msg               = ""

        if fitting_rule:
            applied_rule = fitting_rule
            base_price   = float(applied_rule["baggage_price"])

            if i < prepaid_qty:
                if w <= prepaid_max_w + 0.5:
                    surcharge_for_bag = 0.0
                    msg = "Included"
                else:
                    surcharge_for_bag = base_price
                    msg = f"Exceeded prepaid {prepaid_max_w}kg · full price of new tier applied"
            else:
                surcharge_for_bag = base_price
                msg = "Extra bag"

        else:
            applied_rule     = rules[-1]
            base_price       = float(applied_rule["baggage_price"])
            over             = w - float(applied_rule["baggage_max_weight"])
            overweight_fee   = over * float(applied_rule["overweight_fee_per_kg"])

            if i < prepaid_qty:
                if w <= prepaid_max_w + 0.5:
                    surcharge_for_bag = 0.0
                    msg = "Included"
                else:
                    surcharge_for_bag = base_price + overweight_fee
                    msg = f"Exceeds all tiers · {over:.1f}kg overweight · fee added"
            else:
                surcharge_for_bag = base_price + overweight_fee
                msg = f"Extra bag · exceeds all tiers · {over:.1f}kg overweight"

        total_surcharge += surcharge_for_bag
        bags_result.append({
            "weight":               w,
            "determinedTypeId":     applied_rule["baggage_type_id"],
            "determinedTypeName":   applied_rule["baggage_type_name"],
            "determinedDimensions": applied_rule["baggage_dimension"],
            "isPreBookedSlot":      i < prepaid_qty,
            "surcharge":            surcharge_for_bag,
            "message":              msg,
        })

    return {
        "totalSurcharge": total_surcharge,
        "bags":           bags_result,
    }


def check_already_checked_in(db: Session, booking_item_id: int) -> dict:
    result = checkin_repository.check_already_checked_in(db, booking_item_id)
    return {
        "alreadyCheckedIn": result is not None,
        "ticketNumber": result["boarding_pass_ticket_number"] if result else None,
    }


def get_seat_map(db: Session, flight_operation_id: int):
    return checkin_repository.get_seat_map(db, flight_operation_id)


def get_active_flights(db: Session, agent_id: int, airline_id: int | None = None):
    airport_id = checkin_repository.get_airport_id_by_agent(db, agent_id)
    if not airport_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return checkin_repository.get_active_flights_for_agent(db, airport_id, airline_id=airline_id)


def get_baggage_info(db: Session, booking_item_id: int):
    return checkin_repository.get_baggage_info(db, booking_item_id)


def get_baggage_types(db: Session):
    return checkin_repository.get_baggage_types(db)


def get_checked_baggage_weight(db: Session, flight_operation_id: int):
    return checkin_repository.get_checked_baggage_weight(db, flight_operation_id)


def check_already_checked_in(db: Session, booking_item_id: int, flight_operation_id: int):
    result = checkin_repository.check_already_checked_in(db, booking_item_id, flight_operation_id)
    return {
        "alreadyCheckedIn": result is not None,
        "ticketNumber": result["boarding_pass_ticket_number"] if result else None,
    }


def issue_with_baggage(db: Session, data, flight_operation_id: int, checkin_agent_id: int) -> dict:
    agent = checkin_repository.get_checkin_agent_by_user_id(db, checkin_agent_id)
    if not agent:
        raise ValueError("Check-in agent not found")

    return checkin_repository.issue_boarding_pass_with_baggage(
        db=db,
        booking_item_id=data.booking_item_id,
        seat_layout_id=data.seat_layout_id,
        flight_operation_id=flight_operation_id,
        checkin_agent_id=agent["checkin_agent_id"],
        bags=[b.dict() for b in data.bags],
        payment_method_id=data.payment_method_id,
        total_surcharge=data.total_surcharge,
        status=data.status,
    )


def get_boarding_stats(db: Session, flight_operation_id: int) -> dict:
    return checkin_repository.get_boarding_stats(db, flight_operation_id)


def get_recently_checked_in(db: Session, flight_operation_id: int) -> list:
    return checkin_repository.get_recently_checked_in(db, flight_operation_id)


def get_boarding_pass_details(db: Session, boarding_pass_id: int) -> dict | None:
    return checkin_repository.get_boarding_pass_details(db, boarding_pass_id)



