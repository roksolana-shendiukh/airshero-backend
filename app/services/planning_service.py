from sqlalchemy.orm import Session
from app.repositories import planning_repository


def get_overview_flights(
    db: Session,
    airline_id: int,
    mode: str = "day",
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    status: str | None = None,
) -> list[dict]:
    rows = planning_repository.get_overview_flights(
        db, airline_id, mode=mode, date=date, month=month, year=year, status=status
    )
    return [
        {
            "flightId":        r["flight_id"],
            "flightNumber":    r["flight_number"],
            "departsCode":     r["departs_code"],
            "arrivesCode":     r["arrives_code"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "flightStatus":    r["flight_status_name"],
            "aircraft":        r["aircraft_model"],
            "classes":         r["classes"] or "",
            "bookedSeats":     r["booked_seats"],
            "seatCapacity":    r["seat_capacity"],
            "loadPercent":     round(
                r["booked_seats"] / r["seat_capacity"] * 100, 1
            ) if r["seat_capacity"] else 0.0,
        }
        for r in rows
    ]

def get_overview_stats(db: Session, airline_id: int) -> dict:
    r = planning_repository.get_overview_stats(db, airline_id)
    return {
        "activeFlightsCount":   r["active_flights_count"],
        "routesCount":          r["routes_count"],
        "averageLoadPercent":   round(float(r["average_load_percent"]), 1),
        "monthlyRevenueEur":    float(r["monthly_revenue_eur"]),
    }

def get_available_dates(db: Session, airline_id: int) -> list[str]:
    return planning_repository.get_available_dates(db, airline_id)


def get_booked_dates_for_schedule(db: Session, flight_schedule_id: int) -> list[str]:
    return planning_repository.get_booked_dates_for_schedule(db, flight_schedule_id)


def get_available_months(db: Session, airline_id: int) -> list[str]:
    return planning_repository.get_available_months(db, airline_id)

def get_routes_for_airline(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_routes_for_airline(db, airline_id)
    return [
        {
            "routeId":        r["route_id"],
            "flightNumber":   r["flight_number"],
            "airfleetId":     r["airfleet_id"],
            "aircraftModel":  r["aircraft_model"],
            "seatCapacity":   r["seat_capacity"],
            "departsCode":    r["departs_code"],
            "departsAirport": r["departs_airport"],
            "arrivesCode":    r["arrives_code"],
            "arrivesAirport": r["arrives_airport"],
            "flightDuration": r["flight_duration"],
        }
        for r in rows
    ]


def get_route_schedules(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_route_schedules(db, route_id)
    return [
        {
            "flightScheduleId":    r["flight_schedule_id"],
            "flightStartDate":     str(r["flight_start_date"]),
            "flightEndDate":       str(r["flight_end_date"]),
            "dayId":               r["day_id"],
            "dayName":             r["day_name"],
            "departureTime":       str(r["schedule_departure_time"]),
            "arrivalTime":         str(r["schedule_arrival_time"]),
        }
        for r in rows
    ]


def get_seat_layout(db: Session, airfleet_id: int) -> list[dict]:
    rows = planning_repository.get_seat_layout_for_airfleet(db, airfleet_id)
    return [
        {
            "seatLayoutId": r["seat_layout_id"],
            "row":          r["seat_layout_rows"],
            "column":       r["seat_layout_columns"],
            "classId":      r["class_id"],
            "className":    r["class_name"],
            "seatType":     r["seat_type_name"],
        }
        for r in rows
    ]

def create_flight(
    db: Session,
    flight_schedule_id: int,
    departs_datetime: str,
    arrives_datetime: str,
    class_prices: list,
) -> dict:
    scheduled_status = planning_repository.get_status_id_by_name(db, "Scheduled")

    class_prices_dicts = [
        {"class_id": cp.class_id, "price": cp.price}
        for cp in class_prices
    ]

    flight_id = planning_repository.create_flight(
        db,
        flight_schedule_id=flight_schedule_id,
        flight_status_id=scheduled_status,
        departs_datetime=departs_datetime,
        arrives_datetime=arrives_datetime,
        class_prices=class_prices_dicts,
    )
    return {"flightId": flight_id}

def get_baggage_rules(db: Session) -> list[dict]:
    rows = planning_repository.get_all_baggage_rules(db)
    return [
        {
            "baggagePricingRuleId": r["baggage_pricing_rule_id"],
            "baggageTypeId":        r["baggage_type_id"],
            "baggageTypeName":      r["baggage_type_name"],
            "dimensions":           r["baggage_dimension"],
            "maxWeightKg":          float(r["baggage_max_weight"]) if r["baggage_max_weight"] else None,
            "overweightFeePerKg":   float(r["overweight_fee_per_kg"]) if r["overweight_fee_per_kg"] else None,
        }
        for r in rows
    ]

def add_baggage_to_flight(db: Session, flight_id: int, options: list[dict]) -> dict:
    planning_repository.add_baggage_to_flight(db, flight_id, options)
    return {"success": True, "flightId": flight_id}

