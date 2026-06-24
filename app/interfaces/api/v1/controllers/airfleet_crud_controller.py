from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import airfleet_crud_service as svc

router = APIRouter(prefix="/crud/airfleet", tags=["Airfleet CRUD"])

class ManufacturerDTO(BaseModel):
    manufacturerName: str

class AirfleetDTO(BaseModel):
    airfleetManufacturerId: int
    aircraftModel: str
    aircraftRangeKm: float
    aircraftSpeed: float
    seatCapacity: int
    baggageCapacity: float
    aircraftFuelConsumption: Optional[float] = None
    aircraftUrl: Optional[str] = None

class SeatLayoutDTO(BaseModel):
    classId: int
    seatTypeId: int
    seatLayoutRows: int
    seatLayoutColumns: str

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

@router.get("")
def list_airfleets(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_airfleets(db)

@router.get("/{airfleet_id}")
def get_airfleet(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_airfleet(db, airfleet_id)

@router.post("")
def add_airfleet(
    body: AirfleetDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_airfleet(
        db,
        body.airfleetManufacturerId,
        body.aircraftModel,
        body.aircraftRangeKm,
        body.aircraftSpeed,
        body.seatCapacity,
        body.baggageCapacity,
        body.aircraftFuelConsumption,
        body.aircraftUrl,
    )

@router.put("/{airfleet_id}")
def edit_airfleet(
    airfleet_id: int,
    body: AirfleetDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_airfleet(
        db,
        airfleet_id,
        body.airfleetManufacturerId,
        body.aircraftModel,
        body.aircraftRangeKm,
        body.aircraftSpeed,
        body.seatCapacity,
        body.baggageCapacity,
        body.aircraftFuelConsumption,
        body.aircraftUrl,
    )

@router.delete("/{airfleet_id}")
def remove_airfleet(
    airfleet_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_airfleet(db, airfleet_id)

@router.get("/seat-types/all")
def list_seat_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_seat_types(db)

@router.post("/{airfleet_id}/seat-layouts")
def add_seat_layout(
    airfleet_id: int,
    body: SeatLayoutDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_seat_layout(
        db,
        airfleet_id,
        body.classId,
        body.seatTypeId,
        body.seatLayoutRows,
        body.seatLayoutColumns,
    )

@router.put("/seat-layouts/{seat_layout_id}")
def edit_seat_layout(
    seat_layout_id: int,
    body: SeatLayoutDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_seat_layout(
        db,
        seat_layout_id,
        body.classId,
        body.seatTypeId,
        body.seatLayoutRows,
        body.seatLayoutColumns,
    )

@router.delete("/seat-layouts/{seat_layout_id}")
def remove_seat_layout(
    seat_layout_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_seat_layout(db, seat_layout_id)