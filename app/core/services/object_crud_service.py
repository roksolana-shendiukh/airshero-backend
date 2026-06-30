from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.infrastructure.database.repositories import object_crud_repository as repo


def get_all_airports(db: Session) -> list:
    return [
        {
            "airport_id":      a.airport_id,
            "airport_name":    a.airport_name,
            "airport_code":    a.airport_code,
            "airport_address": a.airport_address,
            "latitude":        a.latitude,
            "longitude":       a.longitude,
            "city_id":         a.city_id,
            "city_name":       a.city.city_name if a.city else None,
            "country_id":      a.city.country_id if a.city else None,
            "terminal_types":  list({
                t.terminal_type.terminal_type_name
                for t in a.terminals if t.terminal_type
            }),
            "terminal_count":  len(a.terminals),
            "gate_count":      sum(len(t.gates) for t in a.terminals),
        }
        for a in repo.get_all_airports(db)
    ]


def create_airport(
    db: Session,
    city_id:         int,
    airport_name:    str,
    airport_address: str,
    airport_code:    str,
    latitude:        float,
    longitude:       float,
) -> dict:
    obj = repo.create_airport(
        db, city_id, airport_name, airport_address, airport_code, latitude, longitude
    )
    return {"airport_id": obj.airport_id, "airport_code": obj.airport_code}


def update_airport(
    db: Session,
    airport_id:      int,
    city_id:         int,
    airport_name:    str,
    airport_address: str,
    airport_code:    str,
    latitude:        float,
    longitude:       float,
) -> dict:
    obj = repo.update_airport(
        db, airport_id, city_id, airport_name,
        airport_address, airport_code, latitude, longitude,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Airport not found")
    return {"airport_id": obj.airport_id, "airport_code": obj.airport_code}


def delete_airport(db: Session, airport_id: int) -> dict:
    if not repo.delete_airport(db, airport_id):
        raise HTTPException(status_code=404, detail="Airport not found")
    return {"deleted": True}


def get_terminals_for_airport(db: Session, airport_id: int) -> list:
    return [
        {
            "terminal_id":        t.terminal_id,
            "terminal_code":      t.terminal_code,
            "terminal_size":      float(t.terminal_size) if t.terminal_size else None,
            "terminal_type_id":   t.terminal_type_id,
            "terminal_type_name": t.terminal_type.terminal_type_name if t.terminal_type else None,
            "airport_id":         t.airport_id,
        }
        for t in repo.get_terminals_for_airport(db, airport_id)
    ]


def create_terminal(
    db: Session,
    airport_id:       int,
    terminal_type_id: int,
    terminal_code:    str,
    terminal_size:    float | None,
) -> dict:
    existing = repo.get_terminal_by_airport_and_code(db, airport_id, terminal_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Terminal '{terminal_code}' already exists in this airport",
        )
    obj = repo.create_terminal(db, airport_id, terminal_type_id, terminal_code, terminal_size)
    return {"terminal_id": obj.terminal_id, "terminal_code": obj.terminal_code}


def update_terminal(
    db: Session,
    terminal_id:      int,
    terminal_type_id: int,
    terminal_code:    str,
    terminal_size:    float | None,
) -> dict:
    obj = repo.get_terminal(db, terminal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal not found")

    duplicate = repo.get_terminal_by_airport_and_code(db, obj.airport_id, terminal_code)
    if duplicate and duplicate.terminal_id != terminal_id:
        raise HTTPException(
            status_code=400,
            detail=f"Code '{terminal_code}' is already assigned to another terminal",
        )

    updated = repo.update_terminal(db, terminal_id, terminal_type_id, terminal_code, terminal_size)
    return {"terminal_id": updated.terminal_id, "terminal_code": updated.terminal_code}


def delete_terminal(db: Session, terminal_id: int) -> dict:
    if not repo.delete_terminal(db, terminal_id):
        raise HTTPException(status_code=404, detail="Terminal not found")
    return {"deleted": True}


def get_all_terminal_types(db: Session) -> list:
    return [
        {
            "terminal_type_id":   t.terminal_type_id,
            "terminal_type_name": t.terminal_type_name,
        }
        for t in repo.get_all_terminal_types(db)
    ]


def get_gates_for_terminal(db: Session, terminal_id: int) -> list:
    return [
        {
            "gate_id":     g.gate_id,
            "gate_code":   g.gate_code,
            "terminal_id": g.terminal_id,
        }
        for g in repo.get_gates_for_terminal(db, terminal_id)
    ]


def create_gate(db: Session, terminal_id: int, gate_code: str) -> dict:
    existing = repo.get_gate_by_terminal_and_code(db, terminal_id, gate_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Gate '{gate_code}' already exists in this terminal",
        )
    obj = repo.create_gate(db, terminal_id, gate_code)
    return {"gate_id": obj.gate_id, "gate_code": obj.gate_code}


def update_gate(db: Session, gate_id: int, gate_code: str) -> dict:
    current_gate = repo.get_gate(db, gate_id)
    if not current_gate:
        raise HTTPException(status_code=404, detail="Gate not found")

    duplicate = repo.get_gate_by_terminal_and_code(db, current_gate.terminal_id, gate_code)
    if duplicate and duplicate.gate_id != gate_id:
        raise HTTPException(
            status_code=400,
            detail=f"Gate '{gate_code}' is already used by another gate in this terminal",
        )

    obj = repo.update_gate(db, gate_id, gate_code)
    return {"gate_id": obj.gate_id, "gate_code": obj.gate_code}


def delete_gate(db: Session, gate_id: int) -> dict:
    try:
        if not repo.delete_gate(db, gate_id):
            raise HTTPException(status_code=404, detail="Gate not found")
        return {"deleted": True}
    except IntegrityError as e:
        db.rollback()
        if "FKFlightOperation_Gate" in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete this gate because it is currently assigned to one or more flight operations. Please unassign it first.",
            )
        raise HTTPException(status_code=400, detail="Cannot delete gate due to database constraints.")


def get_all_airlines(db: Session) -> list:
    return [
        {
            "airline_id":   a.airline_id,
            "airline_name": a.airline_name,
            "iata_code":    a.iata_code,
            "country_id":   a.country_id,
            "airline_url":  a.airline_url,
        }
        for a in repo.get_all_airlines(db)
    ]


def create_airline(
    db: Session,
    country_id:   int,
    airline_name: str,
    iata_code:    str,
    airline_url:  str | None,
) -> dict:
    obj = repo.create_airline(db, country_id, airline_name, iata_code, airline_url)
    return {"airline_id": obj.airline_id, "airline_name": obj.airline_name}


def update_airline(
    db: Session,
    airline_id:   int,
    country_id:   int,
    airline_name: str,
    iata_code:    str,
    airline_url:  str | None,
) -> dict:
    obj = repo.update_airline(db, airline_id, country_id, airline_name, iata_code, airline_url)
    if not obj:
        raise HTTPException(status_code=404, detail="Airline not found")
    return {"airline_id": obj.airline_id, "airline_name": obj.airline_name}


def delete_airline(db: Session, airline_id: int) -> dict:
    if not repo.delete_airline(db, airline_id):
        raise HTTPException(status_code=404, detail="Airline not found")
    return {"deleted": True}


def get_all_airfleets(db: Session) -> list:
    return [
        {
            "airfleet_id":               a.airfleet_id,
            "aircraft_model":            a.aircraft_model,
            "aircraft_range_km":         float(a.aircraft_range_km) if a.aircraft_range_km else None,
            "aircraft_speed":            float(a.aircraft_speed) if a.aircraft_speed else None,
            "seat_capacity":             a.seat_capacity,
            "baggage_capacity":          float(a.baggage_capacity) if a.baggage_capacity else None,
            "aircraft_fuel_consumption": float(a.aircraft_fuel_consumption) if a.aircraft_fuel_consumption else None,
            "aircraft_url":              a.aircraft_url,
            "manufacturer_id":           a.airfleet_manufacturer_id,
            "manufacturer_name":         a.manufacturer.airfleet_manufacturer_name if a.manufacturer else None,
        }
        for a in repo.get_all_airfleets(db)
    ]


def create_airfleet(
    db: Session,
    airfleet_manufacturer_id:  int,
    aircraft_model:            str,
    aircraft_range_km:         float,
    aircraft_speed:            float,
    seat_capacity:             int,
    baggage_capacity:          float,
    aircraft_fuel_consumption: float | None,
    aircraft_url:              str | None,
) -> dict:
    obj = repo.create_airfleet(
        db, airfleet_manufacturer_id, aircraft_model, aircraft_range_km,
        aircraft_speed, seat_capacity, baggage_capacity,
        aircraft_fuel_consumption, aircraft_url,
    )
    return {"airfleet_id": obj.airfleet_id, "aircraft_model": obj.aircraft_model}


def update_airfleet(
    db: Session,
    airfleet_id:               int,
    airfleet_manufacturer_id:  int,
    aircraft_model:            str,
    aircraft_range_km:         float,
    aircraft_speed:            float,
    seat_capacity:             int,
    baggage_capacity:          float,
    aircraft_fuel_consumption: float | None,
    aircraft_url:              str | None,
) -> dict:
    obj = repo.update_airfleet(
        db, airfleet_id, airfleet_manufacturer_id, aircraft_model,
        aircraft_range_km, aircraft_speed, seat_capacity, baggage_capacity,
        aircraft_fuel_consumption, aircraft_url,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"airfleet_id": obj.airfleet_id, "aircraft_model": obj.aircraft_model}


def delete_airfleet(db: Session, airfleet_id: int) -> dict:
    if not repo.delete_airfleet(db, airfleet_id):
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"deleted": True}


def get_all_manufacturers(db: Session) -> list:
    return [
        {
            "manufacturer_id":   m.airfleet_manufacturer_id,
            "manufacturer_name": m.airfleet_manufacturer_name,
        }
        for m in repo.get_all_manufacturers(db)
    ]


def create_manufacturer(db: Session, name: str) -> dict:
    obj = repo.create_manufacturer(db, name.strip())
    return {
        "manufacturer_id":   obj.airfleet_manufacturer_id,
        "manufacturer_name": obj.airfleet_manufacturer_name,
    }


def update_manufacturer(db: Session, manufacturer_id: int, name: str) -> dict:
    obj = repo.update_manufacturer(db, manufacturer_id, name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {
        "manufacturer_id":   obj.airfleet_manufacturer_id,
        "manufacturer_name": obj.airfleet_manufacturer_name,
    }


def delete_manufacturer(db: Session, manufacturer_id: int) -> dict:
    if not repo.delete_manufacturer(db, manufacturer_id):
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"deleted": True}


def get_all_routes(db: Session) -> list:
    return [
        {
            "route_id":           r.route_id,
            "flight_number":      r.flight_number,
            "airline_id":         r.airline_id,
            "airline_name":       r.airline.airline_name if r.airline else None,
            "airfleet_id":        r.airfleet_id,
            "aircraft_model":     r.airfleet.aircraft_model if r.airfleet else None,
            "departs_airport_id": r.departs_airport_id,
            "departs_code":       r.departs_airport.airport_code if r.departs_airport else None,
            "arrives_airport_id": r.arrives_airport_id,
            "arrives_code":       r.arrives_airport.airport_code if r.arrives_airport else None,
            "flight_range":       float(r.flight_range) if r.flight_range else None,
            "flight_duration":    str(r.flight_duration) if r.flight_duration else None,
        }
        for r in repo.get_all_routes(db)
    ]


def delete_route(db: Session, route_id: int) -> dict:
    if not repo.delete_route(db, route_id):
        raise HTTPException(status_code=404, detail="Route not found")
    return {"deleted": True}


def get_all_countries(db: Session) -> list:
    return [
        {"country_id": c.country_id, "country_name": c.country_name}
        for c in repo.get_all_countries(db)
    ]


def get_all_cities(db: Session) -> list:
    return [
        {
            "city_id":    city.city_id,
            "city_name":  city.city_name,
            "country_id": city.country_id,
        }
        for city in repo.get_all_cities(db)
    ]