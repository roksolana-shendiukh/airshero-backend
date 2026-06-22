from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.core.services import reference_crud_service as svc

router = APIRouter(prefix="/crud/reference", tags=["Reference CRUD"])


class CountryDTO(BaseModel):
    countryName: str

class CityDTO(BaseModel):
    cityName: str
    countryId: int

class ClassDTO(BaseModel):
    className: str

class BaggageTypeDTO(BaseModel):
    baggageTypeName: str

class BaggageRuleDTO(BaseModel):
    baggageTypeId: int
    baggageDimension: Optional[str] = None
    baggageMaxWeight: float
    overweightFeePerKg: float

class TerminalTypeDTO(BaseModel):
    terminalTypeName: str


@router.get("/countries")
def list_countries(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_countries(db)

@router.post("/countries")
def add_country(
    body: CountryDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_country(db, body.countryName)

@router.put("/countries/{country_id}")
def edit_country(
    country_id: int,
    body: CountryDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_country(db, country_id, body.countryName)

@router.delete("/countries/{country_id}")
def remove_country(
    country_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_country(db, country_id)


@router.get("/cities")
def list_cities(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_cities(db)

@router.post("/cities")
def add_city(
    body: CityDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_city(db, body.cityName, body.countryId)

@router.put("/cities/{city_id}")
def edit_city(
    city_id: int,
    body: CityDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_city(db, city_id, body.cityName, body.countryId)

@router.delete("/cities/{city_id}")
def remove_city(
    city_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_city(db, city_id)


@router.get("/classes")
def list_classes(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_classes(db)

@router.post("/classes")
def add_class(
    body: ClassDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_class(db, body.className)

@router.put("/classes/{class_id}")
def edit_class(
    class_id: int,
    body: ClassDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_class(db, class_id, body.className)

@router.delete("/classes/{class_id}")
def remove_class(
    class_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_class(db, class_id)


@router.get("/baggage-types")
def list_baggage_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_baggage_types(db)

@router.post("/baggage-types")
def add_baggage_type(
    body: BaggageTypeDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_baggage_type(db, body.baggageTypeName)

@router.put("/baggage-types/{baggage_type_id}")
def edit_baggage_type(
    baggage_type_id: int,
    body: BaggageTypeDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_baggage_type(db, baggage_type_id, body.baggageTypeName)

@router.delete("/baggage-types/{baggage_type_id}")
def remove_baggage_type(
    baggage_type_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_baggage_type(db, baggage_type_id)


@router.get("/baggage-rules")
def list_baggage_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_baggage_rules(db)

@router.post("/baggage-rules")
def add_baggage_rule(
    body: BaggageRuleDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_baggage_rule(
        db, body.baggageTypeId, body.baggageDimension,
        body.baggageMaxWeight, body.overweightFeePerKg)

@router.put("/baggage-rules/{rule_id}")
def edit_baggage_rule(
    rule_id: int,
    body: BaggageRuleDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_baggage_rule(
        db, rule_id, body.baggageTypeId, body.baggageDimension,
        body.baggageMaxWeight, body.overweightFeePerKg)

@router.delete("/baggage-rules/{rule_id}")
def remove_baggage_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_baggage_rule(db, rule_id)


@router.get("/terminal-types")
def list_terminal_types(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.get_all_terminal_types(db)

@router.post("/terminal-types")
def add_terminal_type(
    body: TerminalTypeDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.create_terminal_type(db, body.terminalTypeName)

@router.put("/terminal-types/{terminal_type_id}")
def edit_terminal_type(
    terminal_type_id: int,
    body: TerminalTypeDTO,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.update_terminal_type(db, terminal_type_id, body.terminalTypeName)

@router.delete("/terminal-types/{terminal_type_id}")
def remove_terminal_type(
    terminal_type_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return svc.delete_terminal_type(db, terminal_type_id)





