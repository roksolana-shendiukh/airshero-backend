from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.object_crud_schema import (
    AirportCreateDTO,
    TerminalCreateDTO,
    GateCreateDTO,
    AirlineCreateDTO,
    AirfleetCreateDTO,
    ManufacturerCreateDTO,
)
from app.core.services import object_crud_service as svc

router = APIRouter(prefix="/crud/objects", tags=["Object CRUD"])

_admin = Depends(require_role("systemAdmin"))


@router.get("/countries", dependencies=[_admin])
def list_countries(db: Session = Depends(get_db)):
    return svc.get_all_countries(db)


@router.get("/cities", dependencies=[_admin])
def list_cities(db: Session = Depends(get_db)):
    return svc.get_all_cities(db)


@router.get("/airports", dependencies=[_admin])
def list_airports(db: Session = Depends(get_db)):
    return svc.get_all_airports(db)


@router.post("/airports", dependencies=[_admin])
def add_airport(body: AirportCreateDTO, db: Session = Depends(get_db)):
    return svc.create_airport(
        db,
        body.city_id,
        body.airport_name,
        body.airport_address,
        body.airport_code,
        body.latitude,
        body.longitude,
    )


@router.put("/airports/{airport_id}", dependencies=[_admin])
def edit_airport(airport_id: int, body: AirportCreateDTO, db: Session = Depends(get_db)):
    return svc.update_airport(
        db,
        airport_id,
        body.city_id,
        body.airport_name,
        body.airport_address,
        body.airport_code,
        body.latitude,
        body.longitude,
    )


@router.delete("/airports/{airport_id}", dependencies=[_admin])
def remove_airport(airport_id: int, db: Session = Depends(get_db)):
    return svc.delete_airport(db, airport_id)


@router.get("/airports/{airport_id}/terminals", dependencies=[_admin])
def list_terminals(airport_id: int, db: Session = Depends(get_db)):
    return svc.get_terminals_for_airport(db, airport_id)


@router.post("/airports/{airport_id}/terminals", dependencies=[_admin])
def add_terminal(airport_id: int, body: TerminalCreateDTO, db: Session = Depends(get_db)):
    return svc.create_terminal(
        db,
        airport_id,
        body.terminal_type_id,
        body.terminal_code,
        body.terminal_size,
    )


@router.get("/terminal-types", dependencies=[_admin])
def list_terminal_types(db: Session = Depends(get_db)):
    return svc.get_all_terminal_types(db)


@router.put("/terminals/{terminal_id}", dependencies=[_admin])
def edit_terminal(terminal_id: int, body: TerminalCreateDTO, db: Session = Depends(get_db)):
    return svc.update_terminal(
        db,
        terminal_id,
        body.terminal_type_id,
        body.terminal_code,
        body.terminal_size,
    )


@router.delete("/terminals/{terminal_id}", dependencies=[_admin])
def remove_terminal(terminal_id: int, db: Session = Depends(get_db)):
    return svc.delete_terminal(db, terminal_id)


@router.get("/terminals/{terminal_id}/gates", dependencies=[_admin])
def list_gates(terminal_id: int, db: Session = Depends(get_db)):
    return svc.get_gates_for_terminal(db, terminal_id)


@router.post("/terminals/{terminal_id}/gates", dependencies=[_admin])
def add_gate(terminal_id: int, body: GateCreateDTO, db: Session = Depends(get_db)):
    return svc.create_gate(db, terminal_id, body.gate_code)


@router.put("/gates/{gate_id}", dependencies=[_admin])
def edit_gate(gate_id: int, body: GateCreateDTO, db: Session = Depends(get_db)):
    return svc.update_gate(db, gate_id, body.gate_code)


@router.delete("/gates/{gate_id}", dependencies=[_admin])
def remove_gate(gate_id: int, db: Session = Depends(get_db)):
    return svc.delete_gate(db, gate_id)


@router.get("/airlines", dependencies=[_admin])
def list_airlines(db: Session = Depends(get_db)):
    return svc.get_all_airlines(db)


@router.post("/airlines", dependencies=[_admin])
def add_airline(body: AirlineCreateDTO, db: Session = Depends(get_db)):
    return svc.create_airline(
        db,
        body.country_id,
        body.airline_name,
        body.iata_code,
        body.airline_url,
    )


@router.put("/airlines/{airline_id}", dependencies=[_admin])
def edit_airline(airline_id: int, body: AirlineCreateDTO, db: Session = Depends(get_db)):
    return svc.update_airline(
        db,
        airline_id,
        body.country_id,
        body.airline_name,
        body.iata_code,
        body.airline_url,
    )


@router.delete("/airlines/{airline_id}", dependencies=[_admin])
def remove_airline(airline_id: int, db: Session = Depends(get_db)):
    return svc.delete_airline(db, airline_id)


@router.get("/manufacturers", dependencies=[_admin])
def list_manufacturers(db: Session = Depends(get_db)):
    return svc.get_all_manufacturers(db)


@router.post("/manufacturers", dependencies=[_admin])
def add_manufacturer(body: ManufacturerCreateDTO, db: Session = Depends(get_db)):
    return svc.create_manufacturer(db, body.manufacturer_name)


@router.put("/manufacturers/{manufacturer_id}", dependencies=[_admin])
def edit_manufacturer(manufacturer_id: int, body: ManufacturerCreateDTO, db: Session = Depends(get_db)):
    return svc.update_manufacturer(db, manufacturer_id, body.manufacturer_name)


@router.delete("/manufacturers/{manufacturer_id}", dependencies=[_admin])
def remove_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    return svc.delete_manufacturer(db, manufacturer_id)


@router.get("/airfleets", dependencies=[_admin])
def list_airfleets(db: Session = Depends(get_db)):
    return svc.get_all_airfleets(db)


@router.post("/airfleets", dependencies=[_admin])
def add_airfleet(body: AirfleetCreateDTO, db: Session = Depends(get_db)):
    return svc.create_airfleet(
        db,
        body.airfleet_manufacturer_id,
        body.aircraft_model,
        body.aircraft_range_km,
        body.aircraft_speed,
        body.seat_capacity,
        body.baggage_capacity,
        body.aircraft_fuel_consumption,
        body.aircraft_url,
    )


@router.put("/airfleets/{airfleet_id}", dependencies=[_admin])
def edit_airfleet(airfleet_id: int, body: AirfleetCreateDTO, db: Session = Depends(get_db)):
    return svc.update_airfleet(
        db,
        airfleet_id,
        body.airfleet_manufacturer_id,
        body.aircraft_model,
        body.aircraft_range_km,
        body.aircraft_speed,
        body.seat_capacity,
        body.baggage_capacity,
        body.aircraft_fuel_consumption,
        body.aircraft_url,
    )


@router.delete("/airfleets/{airfleet_id}", dependencies=[_admin])
def remove_airfleet(airfleet_id: int, db: Session = Depends(get_db)):
    return svc.delete_airfleet(db, airfleet_id)


@router.get("/routes", dependencies=[_admin])
def list_routes(db: Session = Depends(get_db)):
    return svc.get_all_routes(db)


@router.delete("/routes/{route_id}", dependencies=[_admin])
def remove_route(route_id: int, db: Session = Depends(get_db)):
    return svc.delete_route(db, route_id)