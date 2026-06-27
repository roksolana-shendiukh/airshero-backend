from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.infrastructure.database.repositories import planning_repository


def get_overview_flights(
    db: Session,
    airline_id:    int,
    mode:          str = "day",
    date:          str | None = None,
    month:         int | None = None,
    year:          int | None = None,
    status:        str | None = None,
    flight_number: str | None = None,
) -> list[dict]:
    rows = planning_repository.get_overview_flights(
        db, airline_id, mode=mode, date=date, month=month, year=year,
        status=status, flight_number=flight_number,
    )
    return [
        {
            "flight_id":       r["flight_id"],
            "flight_number":   r["flight_number"],
            "departs_code":    r["departs_code"],
            "arrives_code":    r["arrives_code"],
            "departs_datetime": r["departs_datetime"].isoformat(),
            "arrives_datetime": r["arrives_datetime"].isoformat(),
            "flight_duration": r["flight_duration"],
            "flight_status":   r["flight_status_name"],
            "aircraft":        r["aircraft_model"],
            "classes":         r["classes"] or "",
            "booked_seats":    r["booked_seats"],
            "seat_capacity":   r["seat_capacity"],
            "load_percent":    round(
                r["booked_seats"] / r["seat_capacity"] * 100, 1
            ) if r["seat_capacity"] else 0.0,
        }
        for r in rows
    ]


def get_overview_stats(db: Session, airline_id: int) -> dict:
    r = planning_repository.get_overview_stats(db, airline_id)
    return {
        "active_flights_count": r["active_flights_count"],
        "routes_count":         r["routes_count"],
        "average_load_percent": round(float(r["average_load_percent"]), 1),
        "monthly_revenue_eur":  float(r["monthly_revenue_eur"]),
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
            "route_id":       r["route_id"],
            "flight_number":  r["flight_number"],
            "airfleet_id":    r["airfleet_id"],
            "aircraft_model": r["aircraft_model"],
            "seat_capacity":  r["seat_capacity"],
            "departs_code":   r["departs_code"],
            "departs_airport": r["departs_airport"],
            "arrives_code":   r["arrives_code"],
            "arrives_airport": r["arrives_airport"],
            "flight_duration": r["flight_duration"],
        }
        for r in rows
    ]


def get_route_schedules(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_route_schedules(db, route_id)
    return [
        {
            "flight_schedule_id": r["flight_schedule_id"],
            "flight_start_date":  str(r["flight_start_date"]),
            "flight_end_date":    str(r["flight_end_date"]),
            "day_id":             r["day_id"],
            "day_name":           r["day_name"],
            "departure_time":     str(r["schedule_departure_time"]),
            "arrival_time":       str(r["schedule_arrival_time"]),
        }
        for r in rows
    ]


def get_seat_layout(db: Session, airfleet_id: int) -> list[dict]:
    rows = planning_repository.get_seat_layout_for_airfleet(db, airfleet_id)
    return [
        {
            "seat_layout_id": r["seat_layout_id"],
            "row":            r["seat_layout_rows"],
            "column":         r["seat_layout_columns"],
            "class_id":       r["class_id"],
            "class_name":     r["class_name"],
            "seat_type":      r["seat_type_name"],
        }
        for r in rows
    ]


def create_flight(
    db: Session,
    schedule_flight_id: int,
    departs_datetime:   str,
    arrives_datetime:   str,
    class_prices:       list,
) -> dict:
    scheduled_status  = planning_repository.get_status_id_by_name(db, "Scheduled")
    class_prices_dicts = [
        {"class_id": cp.class_id, "price": cp.price}
        for cp in class_prices
    ]
    flight_id = planning_repository.create_flight(
        db,
        flight_schedule_id=schedule_flight_id,
        flight_status_id=  scheduled_status,
        departs_datetime=  departs_datetime,
        arrives_datetime=  arrives_datetime,
        class_prices=      class_prices_dicts,
    )
    return {"flight_id": flight_id}


def get_baggage_rules(db: Session) -> list[dict]:
    rows = planning_repository.get_all_baggage_rules(db)
    return [
        {
            "baggage_pricing_rule_id": r["baggage_pricing_rule_id"],
            "baggage_type_id":         r["baggage_type_id"],
            "baggage_type_name":       r["baggage_type_name"],
            "dimensions":              r["baggage_dimension"],
            "max_weight_kg":           float(r["baggage_max_weight"]) if r["baggage_max_weight"] else None,
            "overweight_fee_per_kg":   float(r["overweight_fee_per_kg"]) if r["overweight_fee_per_kg"] else None,
        }
        for r in rows
    ]


def get_airfleets_for_airline(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_airfleets_for_airline(db, airline_id)
    return [
        {
            "airfleet_id":        r["airfleet_id"],
            "aircraft_model":     r["aircraft_model"],
            "seat_capacity":      r["seat_capacity"],
            "aircraft_range_km":  float(r["aircraft_range_km"]) if r["aircraft_range_km"] else None,
            "aircraft_speed":     float(r["aircraft_speed"]) if r["aircraft_speed"] else None,
            "baggage_capacity":   float(r["baggage_capacity"]) if r["baggage_capacity"] else None,
            "manufacturer_name":  r["airfleet_manufacturer_name"],
        }
        for r in rows
    ]


def get_airports_for_airline(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_airports_for_airline(db, airline_id)
    return [
        {
            "airport_id":   r["airport_id"],
            "airport_name": r["airport_name"],
            "airport_code": r["airport_code"],
            "city_name":    r["city_name"],
            "country_name": r["country_name"],
            "latitude":     float(r["latitude"]) if r["latitude"] else None,
            "longitude":    float(r["longitude"]) if r["longitude"] else None,
        }
        for r in rows
    ]


def create_route_with_schedule(
    db: Session,
    airline_id:         int,
    airfleet_id:        int,
    departs_airport_id: int,
    arrives_airport_id: int,
    flight_number:      str | None,
    flight_start_date:  str,
    flight_end_date:    str,
    schedule_groups:    list[dict],
) -> dict:
    all_new_days = []
    for group in schedule_groups:
        all_new_days.extend(group["day_ids"])
    if len(all_new_days) != len(set(all_new_days)):
        raise ValueError("Schedule groups contain overlapping days")

    existing_route_id = planning_repository.get_existing_route(
        db,
        airline_id=        airline_id,
        airfleet_id=       airfleet_id,
        departs_airport_id=departs_airport_id,
        arrives_airport_id=arrives_airport_id,
    )

    if existing_route_id:
        route_id    = existing_route_id
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
            flight_number = planning_repository.generate_flight_number(db, airline_id)
        elif planning_repository.check_flight_number_exists(db, flight_number):
            raise ValueError(f"Flight number '{flight_number}' already exists")

        calculated = planning_repository.calculate_route_range_and_duration(
            db,
            departs_airport_id=departs_airport_id,
            arrives_airport_id=arrives_airport_id,
            airfleet_id=       airfleet_id,
        )

        if not planning_repository.check_aircraft_range(db, airfleet_id, calculated["range_km"]):
            raise ValueError(
                f"Aircraft range is insufficient for this route "
                f"({calculated['range_km']} km required)"
            )

        route_id = planning_repository.create_route(
            db,
            airline_id=        airline_id,
            airfleet_id=       airfleet_id,
            departs_airport_id=departs_airport_id,
            arrives_airport_id=arrives_airport_id,
            flight_number=     flight_number,
            flight_range=      calculated["range_km"],
            flight_duration=   calculated["duration"],
        )

    flight_schedule_id, flights_count = _create_schedule_and_flights(
        db,
        route_id=         route_id,
        flight_start_date=flight_start_date,
        flight_end_date=  flight_end_date,
        schedule_groups=  schedule_groups,
    )
    db.commit()

    return {
        "route_id":           route_id,
        "flight_schedule_id": flight_schedule_id,
        "flights_generated":  flights_count,
    }


def add_schedule_to_route(
    db: Session,
    route_id:         int,
    flight_start_date: str,
    flight_end_date:   str,
    schedule_groups:   list[dict],
) -> dict:
    all_new_days = []
    for group in schedule_groups:
        all_new_days.extend(group["day_ids"])
    if len(all_new_days) != len(set(all_new_days)):
        raise ValueError("Schedule groups contain overlapping days")

    overlapping = planning_repository.check_schedule_overlap(
        db,
        route_id=         route_id,
        flight_start_date=flight_start_date,
        flight_end_date=  flight_end_date,
        schedule_groups=  schedule_groups,
    )
    if overlapping:
        raise ValueError(
            f"Schedule overlaps with existing schedule on days: "
            f"{', '.join(overlapping)}"
        )

    flight_schedule_id, flights_count = _create_schedule_and_flights(
        db,
        route_id=         route_id,
        flight_start_date=flight_start_date,
        flight_end_date=  flight_end_date,
        schedule_groups=  schedule_groups,
    )
    db.commit()

    return {
        "flight_schedule_id": flight_schedule_id,
        "flights_generated":  flights_count,
    }


def _create_schedule_and_flights(
    db: Session,
    route_id:         int,
    flight_start_date: str,
    flight_end_date:   str,
    schedule_groups:   list[dict],
) -> tuple[int, int]:
    flight_schedule_id  = planning_repository.create_schedule_for_route(
        db,
        route_id=         route_id,
        flight_start_date=flight_start_date,
        flight_end_date=  flight_end_date,
        schedule_groups=  schedule_groups,
    )
    scheduled_status_id = planning_repository.get_status_id_by_name(db, "Auto-scheduled")
    flights_count       = planning_repository.generate_flights_for_schedule(
        db,
        flight_schedule_id=flight_schedule_id,
        route_id=          route_id,
        flight_start_date= flight_start_date,
        flight_end_date=   flight_end_date,
        schedule_groups=   schedule_groups,
        flight_status_id=  scheduled_status_id,
    )
    return flight_schedule_id, flights_count


def generate_flight_number(db: Session, airline_id: int) -> dict:
    number = planning_repository.generate_flight_number(db, airline_id)
    return {"flight_number": number}


def get_all_flight_numbers(db: Session, airline_id: int) -> list[str]:
    return planning_repository.get_all_flight_numbers(db, airline_id)


def get_route_duration(
    db: Session,
    airfleet_id:        int,
    departs_airport_id: int,
    arrives_airport_id: int,
) -> dict:
    return planning_repository.calculate_route_range_and_duration(
        db,
        departs_airport_id=departs_airport_id,
        arrives_airport_id=arrives_airport_id,
        airfleet_id=       airfleet_id,
    )


def get_routes_with_planned_flights(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_routes_with_planned_flights(db, airline_id)
    return [
        {
            "route_id":      r["route_id"],
            "flight_number": r["flight_number"],
            "aircraft_model": r["aircraft_model"],
            "departs_code":  r["departs_code"],
            "arrives_code":  r["arrives_code"],
            "planned_count": r["planned_count"],
        }
        for r in rows
    ]


def _map_flight_with_prices(r: dict, prices: list) -> dict:
    return {
        "flight_id":        r["flight_id"],
        "flight_number":    r["flight_number"],
        "departs_datetime": r["departs_datetime"].isoformat(),
        "arrives_datetime": r["arrives_datetime"].isoformat(),
        "flight_duration":  r["flight_duration"],
        "departs_code":     r["departs_code"],
        "arrives_code":     r["arrives_code"],
        "prices": [
            {
                "class_id":   p["class_id"],
                "class_name": p["class_name"],
                "price":      float(p["ticket_price"]),
            }
            for p in prices
        ],
    }


def get_planned_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows = planning_repository.get_planned_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(db, r["flight_id"])
        entry  = _map_flight_with_prices(r, prices)
        entry.update({
            "aircraft_model": r["aircraft_model"],
            "airfleet_id":    r["airfleet_id"],
        })
        result.append(entry)
    return result


def configure_planned_flight(
    db: Session,
    flight_id:   int,
    class_prices: list[dict],
) -> dict:
    planning_repository.configure_planned_flight(db, flight_id, class_prices)
    return {"flight_id": flight_id, "status": "Scheduled"}


def get_scheduled_flights_for_pricing(db: Session, airline_id: int) -> list[dict]:
    rows   = planning_repository.get_scheduled_flights_for_pricing(db, airline_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(db, r["flight_id"])
        entry  = _map_flight_with_prices(r, prices)
        entry.update({
            "flight_status":  r["flight_status_name"],
            "aircraft_model": r["aircraft_model"],
            "prices": [
                {
                    "class_id":       p["class_id"],
                    "class_name":     p["class_name"],
                    "price":          float(p["ticket_price"]),
                    "published_date": str(p["flight_published_date"]),
                }
                for p in prices
            ],
        })
        result.append(entry)
    return result


def get_price_history_for_flight(db: Session, flight_id: int) -> list[dict]:
    rows    = planning_repository.get_price_history_for_flight(db, flight_id)
    history: dict[str, dict] = {}
    for r in rows:
        d = str(r["flight_published_date"])
        if d not in history:
            history[d] = {"date": d, "prices": []}
        history[d]["prices"].append({
            "class_name": r["class_name"],
            "price":      float(r["ticket_price"]),
        })
    return list(history.values())


def update_flight_prices(
    db: Session,
    flight_id:   int,
    class_prices: list[dict],
) -> dict:
    planning_repository.update_flight_prices(db, flight_id, class_prices)
    return {"flight_id": flight_id, "updated": len(class_prices)}


def get_routes_with_pricing_flights(db: Session, airline_id: int) -> list[dict]:
    rows = planning_repository.get_routes_with_pricing_flights(db, airline_id)
    return [
        {
            "route_id":        r["route_id"],
            "flight_number":   r["flight_number"],
            "aircraft_model":  r["aircraft_model"],
            "departs_code":    r["departs_code"],
            "arrives_code":    r["arrives_code"],
            "total_count":     r["total_count"],
            "auto_count":      r["auto_count"],
            "confirmed_count": r["confirmed_count"],
            "departs_time":    r["departs_time"],
            "arrives_time":    r["arrives_time"],
        }
        for r in rows
    ]


def get_pricing_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows   = planning_repository.get_pricing_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(db, r["flight_id"])
        entry  = _map_flight_with_prices(r, prices)
        entry.update({
            "flight_status": r["flight_status_name"],
            "prices": [
                {
                    "class_id":       p["class_id"],
                    "class_name":     p["class_name"],
                    "price":          float(p["ticket_price"]),
                    "published_date": str(p["flight_published_date"]),
                }
                for p in prices
            ],
        })
        result.append(entry)
    return result


def get_all_flights_for_route(db: Session, route_id: int) -> list[dict]:
    rows   = planning_repository.get_all_flights_for_route(db, route_id)
    result = []
    for r in rows:
        prices = planning_repository.get_current_prices_for_flight(db, r["flight_id"])
        entry  = _map_flight_with_prices(r, prices)
        entry.update({
            "aircraft_model": r["aircraft_model"],
            "airfleet_id":    r["airfleet_id"],
            "flight_status":  r["flight_status_name"],
        })
        result.append(entry)
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
    return {"flight_id": flight_id, "updated": True}


def update_flight_baggage(
    db: Session,
    flight_id:       int,
    baggage_options: list[dict],
) -> dict:
    planning_repository.update_flight_baggage(db, flight_id, baggage_options)
    return {"flight_id": flight_id, "updated": True}


def cancel_flight(db: Session, flight_id: int):
    return planning_repository.cancel_flight(db, flight_id)


def update_flight_times(
    db: Session,
    flight_id:   int,
    departs_iso: str,
    arrives_iso: str,
) -> dict:
    new_dep      = datetime.fromisoformat(departs_iso)
    new_arr      = datetime.fromisoformat(arrives_iso)
    new_duration = new_arr - new_dep

    if new_duration.total_seconds() <= 0:
        raise HTTPException(status_code=400, detail="Arrival must be after departure.")

    flight_info = planning_repository.get_flight_reschedule_data(db, flight_id)
    if not flight_info:
        raise HTTPException(status_code=404, detail="Flight not found.")

    min_dur      = flight_info['flight_duration']
    min_timedelta = timedelta(hours=min_dur.hour, minutes=min_dur.minute)

    if new_duration < min_timedelta:
        readable_dur = min_dur.strftime('%H:%M')
        raise HTTPException(
            status_code=400,
            detail=f"Impossible duration. Route requires at least {readable_dur}.",
        )

    conflict = planning_repository.find_aircraft_overlap(
        db,
        airfleet_id=flight_info['airfleet_id'],
        flight_id=  flight_id,
        start=      new_dep,
        end=        new_arr,
    )
    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"Aircraft conflict! Assigned to flight {conflict['flight_number']} at this time.",
        )

    planning_repository.update_flight_datetimes(db, flight_id, new_dep, new_arr)
    db.commit()
    return {"flight_id": flight_id, "updated": True}