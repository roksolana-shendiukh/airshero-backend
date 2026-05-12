from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories import object_crud_repository as repo
from app.models.airport_model import Airport

def get_all_airports(db: Session):
    airports = db.query(Airport).all()
    
    result = []
    for a in airports:
        term_types = set()
        for t in a.terminals:
            if t.terminal_type:
                term_types.add(t.terminal_type.terminal_type_name)
        
        result.append({
            "airportId": a.airport_id,
            "airportName": a.airport_name,
            "airportCode": a.airport_code,
            "airportAddress": a.airport_address,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "cityId": a.city_id,
            "cityName": a.city.city_name if a.city else None,
            "countryId": a.city.country_id if a.city else None,
            "terminalTypes": list(term_types),
            "terminalCount": len(a.terminals),                         
            "gateCount": sum(len(t.gates) for t in a.terminals), 
        })
    return result

def create_airport(
    db: Session,
    city_id: int,
    airport_name: str,
    airport_address: str,
    airport_code: str,
    latitude: float,
    longitude: float,
) -> dict:
    obj = repo.create_airport(
        db, city_id, airport_name, airport_address, airport_code, latitude, longitude)
    return {"airportId": obj.airport_id, "airportCode": obj.airport_code}

def update_airport(
    db: Session,
    airport_id: int,
    city_id: int,
    airport_name: str,
    airport_address: str,
    airport_code: str,
    latitude: float,
    longitude: float,
) -> dict:
    obj = repo.update_airport(
        db, airport_id, city_id, airport_name,
        airport_address, airport_code, latitude, longitude)
    if not obj:
        raise HTTPException(status_code=404, detail="Airport not found")
    return {"airportId": obj.airport_id, "airportCode": obj.airport_code}

def delete_airport(db: Session, airport_id: int) -> dict:
    if not repo.delete_airport(db, airport_id):
        raise HTTPException(status_code=404, detail="Airport not found")
    return {"deleted": True}


def get_terminals_for_airport(db: Session, airport_id: int) -> list:
    return [
        {
            "terminalId": t.terminal_id,
            "terminalCode": t.terminal_code,
            "terminalSize": float(t.terminal_size) if t.terminal_size else None,
            "terminalTypeId": t.terminal_type_id,
            "terminalTypeName": t.terminal_type.terminal_type_name if t.terminal_type else None,
            "airportId": t.airport_id,
        }
        for t in repo.get_terminals_for_airport(db, airport_id)
    ]

def create_terminal(
    db: Session,
    airport_id: int,
    terminal_type_id: int,
    terminal_code: str,
    terminal_size: float | None,
) -> dict:
    existing = repo.get_terminal_by_airport_and_code(db, airport_id, terminal_code)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Terminal '{terminal_code}' already exists in this airport"
        )
    
    obj = repo.create_terminal(db, airport_id, terminal_type_id, terminal_code, terminal_size)
    return {"terminalId": obj.terminal_id, "terminalCode": obj.terminal_code}

def update_terminal(
    db: Session,
    terminal_id: int,
    terminal_type_id: int,
    terminal_code: str,
    terminal_size: float | None,
) -> dict:
    obj = repo.get_terminal(db, terminal_id) 
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal not found")

    duplicate = repo.get_terminal_by_airport_and_code(db, obj.airport_id, terminal_code)
    if duplicate and duplicate.terminal_id != terminal_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Code '{terminal_code}' is already assigned to another terminal"
        )

    updated = repo.update_terminal(db, terminal_id, terminal_type_id, terminal_code, terminal_size)
    return {"terminalId": updated.terminal_id, "terminalCode": updated.terminal_code}

def delete_terminal(db: Session, terminal_id: int) -> dict:
    if not repo.delete_terminal(db, terminal_id):
        raise HTTPException(status_code=404, detail="Terminal not found")
    return {"deleted": True}

def get_all_terminal_types(db: Session) -> list:
    return [
        {
            'terminalTypeId': t.terminal_type_id,
            'terminalTypeName': t.terminal_type_name,
        }
        for t in repo.get_all_terminal_types(db)
    ]


def get_gates_for_terminal(db: Session, terminal_id: int) -> list:
    return [
        {
            "gateId": g.gate_id,
            "gateCode": g.gate_code,
            "terminalId": g.terminal_id,
        }
        for g in repo.get_gates_for_terminal(db, terminal_id)
    ]


def create_gate(db: Session, terminal_id: int, gate_code: str) -> dict:
    existing = repo.get_gate_by_terminal_and_code(db, terminal_id, gate_code)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Gate '{gate_code}' already exists in this terminal"
        )
    
    obj = repo.create_gate(db, terminal_id, gate_code)
    return {"gateId": obj.gate_id, "gateCode": obj.gate_code}

def update_gate(db: Session, gate_id: int, gate_code: str) -> dict:
    current_gate = repo.get_gate(db, gate_id)
    if not current_gate:
        raise HTTPException(status_code=404, detail="Gate not found")
        
    duplicate = repo.get_gate_by_terminal_and_code(db, current_gate.terminal_id, gate_code)
    if duplicate and duplicate.gate_id != gate_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Gate '{gate_code}' is already used by another gate in this terminal"
        )

    obj = repo.update_gate(db, gate_id, gate_code)
    return {"gateId": obj.gate_id, "gateCode": obj.gate_code}

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def delete_gate(db: Session, gate_id: int):
    try:
        if not repo.delete_gate(db, gate_id):
            raise HTTPException(status_code=404, detail="Gate not found")
        return {"deleted": True}
    
    except IntegrityError as e:
        db.rollback()
        
        if "FKFlightOperation_Gate" in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete this gate because it is currently assigned to one or more flight operations. Please unassign it first."
            )
        
        raise HTTPException(
            status_code=400,
            detail="Cannot delete gate due to database constraints."
        )

def get_all_airlines(db: Session) -> list:
    return [
        {
            "airlineId": a.airline_id,
            "airlineName": a.airline_name,
            "iataCode": a.iata_code,
            "countryId": a.country_id,
            "airlineUrl": a.airline_url,
        }
        for a in repo.get_all_airlines(db)
    ]

def create_airline(
    db: Session,
    country_id: int,
    airline_name: str,
    iata_code: str,
    airline_url: str | None,
) -> dict:
    obj = repo.create_airline(db, country_id, airline_name, iata_code, airline_url)
    return {"airlineId": obj.airline_id, "airlineName": obj.airline_name}

def update_airline(
    db: Session,
    airline_id: int,
    country_id: int,
    airline_name: str,
    iata_code: str,
    airline_url: str | None,
) -> dict:
    obj = repo.update_airline(
        db, airline_id, country_id, airline_name, iata_code, airline_url)
    if not obj:
        raise HTTPException(status_code=404, detail="Airline not found")
    return {"airlineId": obj.airline_id, "airlineName": obj.airline_name}

def delete_airline(db: Session, airline_id: int) -> dict:
    if not repo.delete_airline(db, airline_id):
        raise HTTPException(status_code=404, detail="Airline not found")
    return {"deleted": True}


def get_all_airfleets(db: Session) -> list:
    return [
        {
            "airfleetId": a.airfleet_id,
            "aircraftModel": a.aircraft_model,
            "aircraftRangeKm": float(a.aircraft_range_km) if a.aircraft_range_km else None,
            "aircraftSpeed": float(a.aircraft_speed) if a.aircraft_speed else None,
            "seatCapacity": a.seat_capacity,
            "baggageCapacity": float(a.baggage_capacity) if a.baggage_capacity else None,
            "aircraftFuelConsumption": float(a.aircraft_fuel_consumption) if a.aircraft_fuel_consumption else None,
            "aircraftUrl": a.aircraft_url,
            "manufacturerId": a.airfleet_manufacturer_id,
            "manufacturerName": a.manufacturer.airfleet_manufacturer_name if a.manufacturer else None,
        }
        for a in repo.get_all_airfleets(db)
    ]

def create_airfleet(
    db: Session,
    airfleet_manufacturer_id: int,
    aircraft_model: str,
    aircraft_range_km: float,
    aircraft_speed: float,
    seat_capacity: int,
    baggage_capacity: float,
    aircraft_fuel_consumption: float | None,
    aircraft_url: str | None,
) -> dict:
    obj = repo.create_airfleet(
        db, airfleet_manufacturer_id, aircraft_model, aircraft_range_km,
        aircraft_speed, seat_capacity, baggage_capacity,
        aircraft_fuel_consumption, aircraft_url)
    return {"airfleetId": obj.airfleet_id, "aircraftModel": obj.aircraft_model}

def update_airfleet(
    db: Session,
    airfleet_id: int,
    airfleet_manufacturer_id: int,
    aircraft_model: str,
    aircraft_range_km: float,
    aircraft_speed: float,
    seat_capacity: int,
    baggage_capacity: float,
    aircraft_fuel_consumption: float | None,
    aircraft_url: str | None,
) -> dict:
    obj = repo.update_airfleet(
        db, airfleet_id, airfleet_manufacturer_id, aircraft_model,
        aircraft_range_km, aircraft_speed, seat_capacity, baggage_capacity,
        aircraft_fuel_consumption, aircraft_url)
    if not obj:
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"airfleetId": obj.airfleet_id, "aircraftModel": obj.aircraft_model}

def delete_airfleet(db: Session, airfleet_id: int) -> dict:
    if not repo.delete_airfleet(db, airfleet_id):
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"deleted": True}


def get_all_manufacturers(db: Session) -> list:
    return [
        {
            "manufacturerId": m.airfleet_manufacturer_id,
            "manufacturerName": m.airfleet_manufacturer_name,
        }
        for m in repo.get_all_manufacturers(db)
    ]

def create_manufacturer(db: Session, name: str) -> dict:
    obj = repo.create_manufacturer(db, name.strip())
    return {"manufacturerId": obj.airfleet_manufacturer_id,
            "manufacturerName": obj.airfleet_manufacturer_name}

def update_manufacturer(db: Session, manufacturer_id: int, name: str) -> dict:
    obj = repo.update_manufacturer(db, manufacturer_id, name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"manufacturerId": obj.airfleet_manufacturer_id,
            "manufacturerName": obj.airfleet_manufacturer_name}

def delete_manufacturer(db: Session, manufacturer_id: int) -> dict:
    if not repo.delete_manufacturer(db, manufacturer_id):
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"deleted": True}


def get_all_routes(db: Session) -> list:
    return [
        {
            "routeId": r.route_id,
            "flightNumber": r.flight_number,
            "airlineId": r.airline_id,
            "airlineName": r.airline.airline_name if r.airline else None,
            "airfleetId": r.airfleet_id,
            "aircraftModel": r.airfleet.aircraft_model if r.airfleet else None,
            "departsAirportId": r.departs_airport_id,
            "departsCode": r.departs_airport.airport_code if r.departs_airport else None,
            "arrivesAirportId": r.arrives_airport_id,
            "arrivesCode": r.arrives_airport.airport_code if r.arrives_airport else None,
            "flightRange": float(r.flight_range) if r.flight_range else None,
            "flightDuration": str(r.flight_duration) if r.flight_duration else None,
        }
        for r in repo.get_all_routes(db)
    ]

def delete_route(db: Session, route_id: int) -> dict:
    if not repo.delete_route(db, route_id):
        raise HTTPException(status_code=404, detail="Route not found")
    return {"deleted": True}


def get_all_countries(db: Session):
    countries = repo.get_all_countries(db)
    return [
        {
            "countryId": c.country_id,
            "countryName": c.country_name
        }
        for c in countries
    ]

def get_all_cities(db: Session):
    cities = repo.get_all_cities(db)
    return [
        {
            "cityId": city.city_id,
            "cityName": city.city_name,
            "countryId": city.country_id  
        }
        for city in cities
    ]


