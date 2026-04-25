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
    flight_number: str | None = None,
) -> list[dict]:
    rows = planning_repository.get_overview_flights(
        db, airline_id, mode=mode, date=date, month=month, year=year,
        status=status, flight_number=flight_number
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


def get_airfleets_for_airline(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_airfleets_for_airline(db, airline_id)
    return [
        {
            "airfleetId":           r["airfleet_id"],
            "aircraftModel":        r["aircraft_model"],
            "seatCapacity":         r["seat_capacity"],
            "aircraftRangeKm":      float(r["aircraft_range_km"]) if r["aircraft_range_km"] else None,
            "aircraftSpeed":        float(r["aircraft_speed"]) if r["aircraft_speed"] else None,
            "baggageCapacity":      float(r["baggage_capacity"]) if r["baggage_capacity"] else None,
            "manufacturerName":     r["airfleet_manufacturer_name"],
        }
        for r in rows
    ]


def get_airports_for_airline(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_airports_for_airline(db, airline_id)
    return [
        {
            "airportId":    r["airport_id"],
            "airportName":  r["airport_name"],
            "airportCode":  r["airport_code"],
            "cityName":     r["city_name"],
            "countryName":  r["country_name"],
            "latitude":     float(r["latitude"]) if r["latitude"] else None,
            "longitude":    float(r["longitude"]) if r["longitude"] else None,
        }
        for r in rows
    ]


def create_route_with_schedule(
    db: Session,
    airline_id: int,
    airfleet_id: int,
    departs_airport_id: int,
    arrives_airport_id: int,
    flight_number: str | None,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
) -> dict:
    all_new_days = []
    for group in schedule_groups:
        all_new_days.extend(group["day_ids"])
    if len(all_new_days) != len(set(all_new_days)):
        raise ValueError("Schedule groups contain overlapping days")

    existing_route_id = planning_repository.get_existing_route(
        db,
        airline_id=airline_id,
        airfleet_id=airfleet_id,
        departs_airport_id=departs_airport_id,
        arrives_airport_id=arrives_airport_id,
    )

    if existing_route_id:
        route_id = existing_route_id

        overlapping = planning_repository.check_schedule_overlap(
            db, route_id, flight_start_date, flight_end_date, schedule_groups
        )
        if overlapping:
            raise ValueError(
                f"Schedule overlaps with existing schedule on days: "
                f"{', '.join(overlapping)}"
            )
    else:
        if flight_number is None:
            flight_number = planning_repository.generate_flight_number(
                db, airline_id)
        elif planning_repository.check_flight_number_exists(db, flight_number):
            raise ValueError(
                f"Flight number '{flight_number}' already exists")

        calculated = planning_repository.calculate_route_range_and_duration(
            db,
            departs_airport_id=departs_airport_id,
            arrives_airport_id=arrives_airport_id,
            airfleet_id=airfleet_id,
        )

        if not planning_repository.check_aircraft_range(
            db, airfleet_id, calculated["range_km"]
        ):
            raise ValueError(
                f"Aircraft range is insufficient for this route "
                f"({calculated['range_km']} km required)"
            )

        route_id = planning_repository.create_route(
            db,
            airline_id=airline_id,
            airfleet_id=airfleet_id,
            departs_airport_id=departs_airport_id,
            arrives_airport_id=arrives_airport_id,
            flight_number=flight_number,
            flight_range=calculated["range_km"],
            flight_duration=calculated["duration"],
        )

    flight_schedule_id, flights_count = _create_schedule_and_flights(
        db,
        route_id=route_id,
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        schedule_groups=schedule_groups,
    )

    db.commit()

    return {
        "routeId":          route_id,
        "flightScheduleId": flight_schedule_id,
        "flightsGenerated": flights_count,
    }


def add_schedule_to_route(
    db: Session,
    route_id: int,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
) -> dict:
    all_new_days = []
    for group in schedule_groups:
        all_new_days.extend(group["day_ids"])
    if len(all_new_days) != len(set(all_new_days)):
        raise ValueError("Schedule groups contain overlapping days")

    overlapping = planning_repository.check_schedule_overlap(
        db,
        route_id=route_id,
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        schedule_groups=schedule_groups,
    )
    if overlapping:
        raise ValueError(
            f"Schedule overlaps with existing schedule on days: "
            f"{', '.join(overlapping)}"
        )

    flight_schedule_id, flights_count = _create_schedule_and_flights(
        db,
        route_id=route_id,
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        schedule_groups=schedule_groups,
    )

    db.commit()

    return {
        "flightScheduleId": flight_schedule_id,
        "flightsGenerated": flights_count,
    }


def _create_schedule_and_flights(
    db: Session,
    route_id: int,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
) -> tuple[int, int]:
    flight_schedule_id = planning_repository.create_schedule_for_route(
        db,
        route_id=route_id,
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        schedule_groups=schedule_groups,
    )

    scheduled_status_id = planning_repository.get_status_id_by_name(db, "Auto-scheduled")

    flights_count = planning_repository.generate_flights_for_schedule(
        db,
        flight_schedule_id=flight_schedule_id,
        route_id=route_id,
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        schedule_groups=schedule_groups,
        flight_status_id=scheduled_status_id,
    )

    return flight_schedule_id, flights_count


def generate_flight_number(db: Session, airline_id: int) -> dict:
    number = planning_repository.generate_flight_number(db, airline_id)
    return {"flightNumber": number}


def get_all_flight_numbers(db: Session, airline_id: int) -> list[str]:
    return planning_repository.get_all_flight_numbers(db, airline_id)


def get_route_duration(
    db: Session,
    airfleet_id: int,
    departs_airport_id: int,
    arrives_airport_id: int,
) -> dict:
    return planning_repository.calculate_route_range_and_duration(
        db,
        departs_airport_id=departs_airport_id,
        arrives_airport_id=arrives_airport_id,
        airfleet_id=airfleet_id,
    )



def get_routes_with_planned_flights(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_routes_with_planned_flights(db, airline_id)
    return [
        {
            "routeId":      r["route_id"],
            "flightNumber": r["flight_number"],
            "aircraftModel": r["aircraft_model"],
            "departsCode":  r["departs_code"],
            "arrivesCode":  r["arrives_code"],
            "plannedCount": r["planned_count"],
        }
        for r in rows
    ]


def get_planned_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_planned_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(
            db, r["flight_id"])
        result.append({
            "flightId":        r["flight_id"],
            "flightNumber":    r["flight_number"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "departsCode":     r["departs_code"],
            "arrivesCode":     r["arrives_code"],
            "aircraftModel":   r["aircraft_model"],
            "airfleetId":      r["airfleet_id"],
            "prices": [
                {
                    "classId":   p["class_id"],
                    "className": p["class_name"],
                    "price":     float(p["ticket_price"]),
                }
                for p in prices
            ],
        })
    return result

def configure_planned_flight(
    db: Session,
    flight_id: int,
    class_prices: list[dict],
) -> dict:
    planning_repository.configure_planned_flight(db, flight_id, class_prices)
    return {"flightId": flight_id, "status": "Scheduled"}


def get_scheduled_flights_for_pricing(
    db: Session, airline_id: int
) -> list[dict]:
    rows = planning_repository.get_scheduled_flights_for_pricing(
        db, airline_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(
            db, r["flight_id"])
        result.append({
            "flightId":        r["flight_id"],
            "flightNumber":    r["flight_number"],
            "flightStatus":    r["flight_status_name"],
            "departsCode":     r["departs_code"],
            "arrivesCode":     r["arrives_code"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "aircraftModel":   r["aircraft_model"],
            "prices": [
                {
                    "classId":       p["class_id"],
                    "className":     p["class_name"],
                    "price":         float(p["ticket_price"]),
                    "publishedDate": str(p["flight_published_date"]),
                }
                for p in prices
            ],
        })
    return result


def get_price_history_for_flight(
    db: Session, flight_id: int
) -> list[dict]:
    rows = planning_repository.get_price_history_for_flight(db, flight_id)
    history: dict[str, dict] = {}
    for r in rows:
        date = str(r["flight_published_date"])
        if date not in history:
            history[date] = {"date": date, "prices": []}
        history[date]["prices"].append({
            "className": r["class_name"],
            "price":     float(r["ticket_price"]),
        })
    return list(history.values())


def update_flight_prices(
    db: Session,
    flight_id: int,
    class_prices: list[dict],
) -> dict:
    planning_repository.update_flight_prices(db, flight_id, class_prices)
    return {"flightId": flight_id, "updated": len(class_prices)}


def get_routes_with_pricing_flights(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_routes_with_pricing_flights(db, airline_id)
    return [
        {
            "routeId":        r["route_id"],
            "flightNumber":   r["flight_number"],
            "aircraftModel":  r["aircraft_model"],
            "departsCode":    r["departs_code"],
            "arrivesCode":    r["arrives_code"],
            "totalCount":     r["total_count"],
            "autoCount":      r["auto_count"],
            "confirmedCount": r["confirmed_count"],
            "departsTime": r["departs_time"],
            "arrivesTime": r["arrives_time"],
        }
        for r in rows
    ]


def get_pricing_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_pricing_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(
            db, r["flight_id"])
        result.append({
            "flightId":        r["flight_id"],
            "flightNumber":    r["flight_number"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "departsCode":     r["departs_code"],
            "arrivesCode":     r["arrives_code"],
            "flightStatus":    r["flight_status_name"],
            "prices": [
                {
                    "classId":       p["class_id"],
                    "className":     p["class_name"],
                    "price":         float(p["ticket_price"]),
                    "publishedDate": str(p["flight_published_date"]),
                }
                for p in prices
            ],
        })
    return result


def get_all_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_all_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(
            db, r["flight_id"])
        result.append({
            "flightId":        r["flight_id"],
            "flightNumber":    r["flight_number"],
            "departsDatetime": r["departs_datetime"].isoformat(),
            "arrivesDatetime": r["arrives_datetime"].isoformat(),
            "flightDuration":  r["flight_duration"],
            "departsCode":     r["departs_code"],
            "arrivesCode":     r["arrives_code"],
            "aircraftModel":   r["aircraft_model"],
            "airfleetId":      r["airfleet_id"],
            "flightStatus":    r["flight_status_name"],
            "prices": [
                {
                    "classId":   p["class_id"],
                    "className": p["class_name"],
                    "price":     float(p["ticket_price"]),
                }
                for p in prices
            ],
        })
    return result


def confirm_flights(db: Session, flight_ids: list[int]) -> dict:
    count = planning_repository.confirm_flights(db, flight_ids)
    return {"confirmed": count}


def update_flight_classes(
    db: Session,
    flight_id: int,
    class_ids: list[int],
) -> dict:
    planning_repository.update_flight_classes(db, flight_id, class_ids)
    return {"flightId": flight_id, "updated": True}


def update_flight_baggage(
    db: Session,
    flight_id: int,
    baggage_options: list[dict],
) -> dict:
    planning_repository.update_flight_baggage(db, flight_id, baggage_options)
    return {"flightId": flight_id, "updated": True}



