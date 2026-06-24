from sqlalchemy.orm import Session
from app.infrastructure.database.models.airport_model import Airport
from app.infrastructure.database.models.airport_model import Terminal, TerminalType, Gate
from app.infrastructure.database.models.airline_model import Airline
from app.infrastructure.database.models.airfleet_model import Airfleet, AirfleetManufacturer
from app.infrastructure.database.models.flight_model import Route, Flight
from app.infrastructure.database.models.airport_model import City
from app.infrastructure.database.models.airport_model import Country
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException



def get_all_airports(db: Session) -> list:
    return db.query(Airport).join(City).join(Country).order_by(
        Airport.airport_code).all()

def get_airport(db: Session, airport_id: int) -> Airport | None:
    return db.query(Airport).filter(Airport.airport_id == airport_id).first()

def create_airport(
    db: Session,
    city_id: int,
    airport_name: str,
    airport_address: str,
    airport_code: str,
    latitude: float,
    longitude: float,
) -> Airport:
    obj = Airport(
        city_id=city_id,
        airport_name=airport_name,
        airport_address=airport_address,
        airport_code=airport_code.upper(),
        latitude=latitude,
        longitude=longitude,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_airport(
    db: Session,
    airport_id: int,
    city_id: int,
    airport_name: str,
    airport_address: str,
    airport_code: str,
    latitude: float,
    longitude: float,
) -> Airport | None:
    obj = get_airport(db, airport_id)
    if not obj:
        return None
    obj.city_id = city_id
    obj.airport_name = airport_name
    obj.airport_address = airport_address
    obj.airport_code = airport_code.upper()
    obj.latitude = latitude
    obj.longitude = longitude
    db.commit()
    db.refresh(obj)
    return obj

def delete_airport(db: Session, airport_id: int) -> bool:
    obj = get_airport(db, airport_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_terminal_by_airport_and_code(db: Session, airport_id: int, terminal_code: str) -> Terminal | None:
    return db.query(Terminal).filter(
        Terminal.airport_id == airport_id,
        Terminal.terminal_code == terminal_code
    ).first()

def get_terminals_for_airport(db: Session, airport_id: int) -> list:
    return db.query(Terminal).filter(
        Terminal.airport_id == airport_id).order_by(Terminal.terminal_code).all()

def get_terminal(db: Session, terminal_id: int) -> Terminal | None:
    return db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()

def create_terminal(
    db: Session,
    airport_id: int,
    terminal_type_id: int,
    terminal_code: str,
    terminal_size: float | None,
) -> Terminal:
    obj = Terminal(
        airport_id=airport_id,
        terminal_type_id=terminal_type_id,
        terminal_code=terminal_code,
        terminal_size=terminal_size,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_terminal(
    db: Session,
    terminal_id: int,
    terminal_type_id: int,
    terminal_code: str,
    terminal_size: float | None,
) -> Terminal | None:
    obj = get_terminal(db, terminal_id)
    if not obj:
        return None
    obj.terminal_type_id = terminal_type_id
    obj.terminal_code = terminal_code
    obj.terminal_size = terminal_size
    db.commit()
    db.refresh(obj)
    return obj

def delete_terminal(db: Session, terminal_id: int):
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        return False
        
    try:
        db.delete(terminal)
        db.commit()
        return True
    except IntegrityError:
        db.rollback() 
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete this terminal because its gates are currently assigned to flights."
        )
    
def get_all_terminal_types(db: Session) -> list:
    return db.query(TerminalType).order_by(TerminalType.terminal_type_name).all()

def get_terminal_type(db: Session, terminal_type_id: int) -> TerminalType | None:
    return db.query(TerminalType).filter(
        TerminalType.terminal_type_id == terminal_type_id).first()


def get_gate_by_terminal_and_code(db: Session, terminal_id: int, gate_code: str) -> Gate | None:
    return db.query(Gate).filter(
        Gate.terminal_id == terminal_id,
        Gate.gate_code == gate_code
    ).first()

def get_gates_for_terminal(db: Session, terminal_id: int) -> list:
    return db.query(Gate).filter(
        Gate.terminal_id == terminal_id).order_by(Gate.gate_code).all()

def get_gate(db: Session, gate_id: int) -> Gate | None:
    return db.query(Gate).filter(Gate.gate_id == gate_id).first()

def create_gate(db: Session, terminal_id: int, gate_code: str) -> Gate:
    obj = Gate(terminal_id=terminal_id, gate_code=gate_code)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_gate(db: Session, gate_id: int, gate_code: str) -> Gate | None:
    obj = get_gate(db, gate_id)
    if not obj:
        return None
    obj.gate_code = gate_code
    db.commit()
    db.refresh(obj)
    return obj

def delete_gate(db: Session, gate_id: int) -> bool:
    obj = get_gate(db, gate_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_airlines(db: Session) -> list:
    return db.query(Airline).order_by(Airline.airline_name).all()

def get_airline(db: Session, airline_id: int) -> Airline | None:
    return db.query(Airline).filter(Airline.airline_id == airline_id).first()

def create_airline(
    db: Session,
    country_id: int,
    airline_name: str,
    iata_code: str,
    airline_url: str | None,
) -> Airline:
    obj = Airline(
        country_id=country_id,
        airline_name=airline_name,
        iata_code=iata_code.upper(),
        airline_url=airline_url,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_airline(
    db: Session,
    airline_id: int,
    country_id: int,
    airline_name: str,
    iata_code: str,
    airline_url: str | None,
) -> Airline | None:
    obj = get_airline(db, airline_id)
    if not obj:
        return None
    obj.country_id = country_id
    obj.airline_name = airline_name
    obj.iata_code = iata_code.upper()
    obj.airline_url = airline_url
    db.commit()
    db.refresh(obj)
    return obj

def delete_airline(db: Session, airline_id: int) -> bool:
    obj = get_airline(db, airline_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_airfleets(db: Session) -> list:
    return db.query(Airfleet).join(AirfleetManufacturer).order_by(
        Airfleet.aircraft_model).all()

def get_airfleet(db: Session, airfleet_id: int) -> Airfleet | None:
    return db.query(Airfleet).filter(Airfleet.airfleet_id == airfleet_id).first()

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
) -> Airfleet:
    obj = Airfleet(
        airfleet_manufacturer_id=airfleet_manufacturer_id,
        aircraft_model=aircraft_model,
        aircraft_range_km=aircraft_range_km,
        aircraft_speed=aircraft_speed,
        seat_capacity=seat_capacity,
        baggage_capacity=baggage_capacity,
        aircraft_fuel_consumption=aircraft_fuel_consumption,
        aircraft_url=aircraft_url,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

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
) -> Airfleet | None:
    obj = get_airfleet(db, airfleet_id)
    if not obj:
        return None
    obj.airfleet_manufacturer_id = airfleet_manufacturer_id
    obj.aircraft_model = aircraft_model
    obj.aircraft_range_km = aircraft_range_km
    obj.aircraft_speed = aircraft_speed
    obj.seat_capacity = seat_capacity
    obj.baggage_capacity = baggage_capacity
    obj.aircraft_fuel_consumption = aircraft_fuel_consumption
    obj.aircraft_url = aircraft_url
    db.commit()
    db.refresh(obj)
    return obj

def delete_airfleet(db: Session, airfleet_id: int) -> bool:
    obj = get_airfleet(db, airfleet_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_manufacturers(db: Session) -> list:
    return db.query(AirfleetManufacturer).order_by(
        AirfleetManufacturer.airfleet_manufacturer_name).all()

def get_manufacturer(db: Session, manufacturer_id: int) -> AirfleetManufacturer | None:
    return db.query(AirfleetManufacturer).filter(
        AirfleetManufacturer.airfleet_manufacturer_id == manufacturer_id).first()

def create_manufacturer(db: Session, name: str) -> AirfleetManufacturer:
    obj = AirfleetManufacturer(airfleet_manufacturer_name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_manufacturer(db: Session, manufacturer_id: int,
                        name: str) -> AirfleetManufacturer | None:
    obj = get_manufacturer(db, manufacturer_id)
    if not obj:
        return None
    obj.airfleet_manufacturer_name = name
    db.commit()
    db.refresh(obj)
    return obj

def delete_manufacturer(db: Session, manufacturer_id: int) -> bool:
    obj = get_manufacturer(db, manufacturer_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_routes(db: Session) -> list:
    return (
        db.query(Route)
        .join(Flight, Flight.route_id == Route.route_id)
        .order_by(Flight.flight_number)
        .all()
    )

def get_route(db: Session, route_id: int) -> Route | None:
    return db.query(Route).filter(Route.route_id == route_id).first()

def delete_route(db: Session, route_id: int) -> bool:
    obj = get_route(db, route_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def get_all_countries(db: Session):
    return db.query(Country).order_by(Country.country_name).all()

def get_all_cities(db: Session):
    return db.query(City).order_by(City.city_name).all()

