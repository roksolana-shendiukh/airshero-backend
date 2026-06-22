from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import object_crud_service as svc

router = APIRouter(prefix="/crud/objects", tags=["Object CRUD"])


class AirportDTO(BaseModel):
    cityId: int
    airportName: str
    airportAddress: str
    airportCode: str
    latitude: float
    longitude: float

class TerminalDTO(BaseModel):
    terminalTypeId: int
    terminalCode: str
    terminalSize: Optional[float] = None

class GateDTO(BaseModel):
    gateCode: str

class AirlineDTO(BaseModel):
    countryId: int
    airlineName: str
    iataCode: str
    airlineUrl: Optional[str] = None

class AirfleetDTO(BaseModel):
    airfleetManufacturerId: int
    aircraftModel: str
    aircraftRangeKm: float
    aircraftSpeed: float
    seatCapacity: int
    baggageCapacity: float
    aircraftFuelConsumption: Optional[float] = None
    aircraftUrl: Optional[str] = None

class ManufacturerDTO(BaseModel):
    manufacturerName: str


@router.get("/airports")
def list_airports(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_airports(db)

@router.post("/airports")
def add_airport(
    body: AirportDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_airport(
        db, body.cityId, body.airportName, body.airportAddress,
        body.airportCode, body.latitude, body.longitude)

@router.put("/airports/{airport_id}")
def edit_airport(
    airport_id: int,
    body: AirportDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_airport(
        db, airport_id, body.cityId, body.airportName, body.airportAddress,
        body.airportCode, body.latitude, body.longitude)

@router.delete("/airports/{airport_id}")
def remove_airport(
    airport_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_airport(db, airport_id)


@router.get("/airports/{airport_id}/terminals")
def list_terminals(
    airport_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_terminals_for_airport(db, airport_id)

@router.post("/airports/{airport_id}/terminals")
def add_terminal(
    airport_id: int,
    body: TerminalDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_terminal(
        db, airport_id, body.terminalTypeId,
        body.terminalCode, body.terminalSize)

@router.put("/terminals/{terminal_id}")
def edit_terminal(
    terminal_id: int,
    body: TerminalDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_terminal(
        db, terminal_id, body.terminalTypeId,
        body.terminalCode, body.terminalSize)

@router.delete("/terminals/{terminal_id}")
def remove_terminal(
    terminal_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_terminal(db, terminal_id)

@router.get("/terminal-types")
def list_terminal_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_terminal_types(db)


@router.get("/terminals/{terminal_id}/gates")
def list_gates(
    terminal_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_gates_for_terminal(db, terminal_id)

@router.post("/terminals/{terminal_id}/gates")
def add_gate(
    terminal_id: int,
    body: GateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_gate(db, terminal_id, body.gateCode)

@router.put("/gates/{gate_id}")
def edit_gate(
    gate_id: int,
    body: GateDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_gate(db, gate_id, body.gateCode)

@router.delete("/gates/{gate_id}")
def remove_gate(
    gate_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_gate(db, gate_id)


@router.get("/airlines")
def list_airlines(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_airlines(db)

@router.post("/airlines")
def add_airline(
    body: AirlineDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_airline(
        db, body.countryId, body.airlineName,
        body.iataCode, body.airlineUrl)

@router.put("/airlines/{airline_id}")
def edit_airline(
    airline_id: int,
    body: AirlineDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_airline(
        db, airline_id, body.countryId, body.airlineName,
        body.iataCode, body.airlineUrl)

@router.delete("/airlines/{airline_id}")
def remove_airline(
    airline_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_airline(db, airline_id)


@router.get("/airfleets")
def list_airfleets(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_airfleets(db)

@router.post("/airfleets")
def add_airfleet(
    body: AirfleetDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_airfleet(
        db, body.airfleetManufacturerId, body.aircraftModel,
        body.aircraftRangeKm, body.aircraftSpeed, body.seatCapacity,
        body.baggageCapacity, body.aircraftFuelConsumption, body.aircraftUrl)

@router.put("/airfleets/{airfleet_id}")
def edit_airfleet(
    airfleet_id: int,
    body: AirfleetDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_airfleet(
        db, airfleet_id, body.airfleetManufacturerId, body.aircraftModel,
        body.aircraftRangeKm, body.aircraftSpeed, body.seatCapacity,
        body.baggageCapacity, body.aircraftFuelConsumption, body.aircraftUrl)

@router.delete("/airfleets/{airfleet_id}")
def remove_airfleet(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_airfleet(db, airfleet_id)


@router.get("/manufacturers")
def list_manufacturers(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_manufacturers(db)

@router.post("/manufacturers")
def add_manufacturer(
    body: ManufacturerDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_manufacturer(db, body.manufacturerName)

@router.put("/manufacturers/{manufacturer_id}")
def edit_manufacturer(
    manufacturer_id: int,
    body: ManufacturerDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_manufacturer(db, manufacturer_id, body.manufacturerName)

@router.delete("/manufacturers/{manufacturer_id}")
def remove_manufacturer(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_manufacturer(db, manufacturer_id)


@router.get("/routes")
def list_routes(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_routes(db)

@router.delete("/routes/{route_id}")
def remove_route(
    route_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_route(db, route_id)


@router.get("/cities")
def list_cities(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_cities(db)

@router.get("/countries")
def list_countries(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_countries(db)

