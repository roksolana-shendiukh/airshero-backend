from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.interfaces.api.dependencies.auth import require_role
from app.interfaces.schemas.reference_crud_schema import (
    CountryDTO,
    CityDTO,
    ClassDTO,
    BaggageTypeDTO,
    BaggageRuleDTO,
    TerminalTypeDTO,
)
from app.core.services import reference_crud_service as svc

router = APIRouter(prefix="/crud/reference", tags=["Reference CRUD"])

_admin = Depends(require_role("systemAdmin"))


@router.get("/countries", dependencies=[_admin])
def list_countries(db: Session = Depends(get_db)):
    return svc.get_all_countries(db)


@router.post("/countries", dependencies=[_admin])
def add_country(body: CountryDTO, db: Session = Depends(get_db)):
    return svc.create_country(db, body.country_name)


@router.put("/countries/{country_id}", dependencies=[_admin])
def edit_country(country_id: int, body: CountryDTO, db: Session = Depends(get_db)):
    return svc.update_country(db, country_id, body.country_name)


@router.delete("/countries/{country_id}", dependencies=[_admin])
def remove_country(country_id: int, db: Session = Depends(get_db)):
    return svc.delete_country(db, country_id)


@router.get("/cities", dependencies=[_admin])
def list_cities(db: Session = Depends(get_db)):
    return svc.get_all_cities(db)


@router.post("/cities", dependencies=[_admin])
def add_city(body: CityDTO, db: Session = Depends(get_db)):
    return svc.create_city(db, body.city_name, body.country_id)


@router.put("/cities/{city_id}", dependencies=[_admin])
def edit_city(city_id: int, body: CityDTO, db: Session = Depends(get_db)):
    return svc.update_city(db, city_id, body.city_name, body.country_id)


@router.delete("/cities/{city_id}", dependencies=[_admin])
def remove_city(city_id: int, db: Session = Depends(get_db)):
    return svc.delete_city(db, city_id)


@router.get("/classes", dependencies=[_admin])
def list_classes(db: Session = Depends(get_db)):
    return svc.get_all_classes(db)


@router.post("/classes", dependencies=[_admin])
def add_class(body: ClassDTO, db: Session = Depends(get_db)):
    return svc.create_class(db, body.class_name)


@router.put("/classes/{class_id}", dependencies=[_admin])
def edit_class(class_id: int, body: ClassDTO, db: Session = Depends(get_db)):
    return svc.update_class(db, class_id, body.class_name)


@router.delete("/classes/{class_id}", dependencies=[_admin])
def remove_class(class_id: int, db: Session = Depends(get_db)):
    return svc.delete_class(db, class_id)


@router.get("/baggage-types", dependencies=[_admin])
def list_baggage_types(db: Session = Depends(get_db)):
    return svc.get_all_baggage_types(db)


@router.post("/baggage-types", dependencies=[_admin])
def add_baggage_type(body: BaggageTypeDTO, db: Session = Depends(get_db)):
    return svc.create_baggage_type(db, body.baggage_type_name)


@router.put("/baggage-types/{baggage_type_id}", dependencies=[_admin])
def edit_baggage_type(baggage_type_id: int, body: BaggageTypeDTO, db: Session = Depends(get_db)):
    return svc.update_baggage_type(db, baggage_type_id, body.baggage_type_name)


@router.delete("/baggage-types/{baggage_type_id}", dependencies=[_admin])
def remove_baggage_type(baggage_type_id: int, db: Session = Depends(get_db)):
    return svc.delete_baggage_type(db, baggage_type_id)


@router.get("/baggage-rules", dependencies=[_admin])
def list_baggage_rules(db: Session = Depends(get_db)):
    return svc.get_all_baggage_rules(db)


@router.post("/baggage-rules", dependencies=[_admin])
def add_baggage_rule(body: BaggageRuleDTO, db: Session = Depends(get_db)):
    return svc.create_baggage_rule(
        db,
        body.baggage_type_id,
        body.baggage_dimension,
        body.baggage_max_weight,
        body.overweight_fee_per_kg,
    )


@router.put("/baggage-rules/{rule_id}", dependencies=[_admin])
def edit_baggage_rule(rule_id: int, body: BaggageRuleDTO, db: Session = Depends(get_db)):
    return svc.update_baggage_rule(
        db,
        rule_id,
        body.baggage_type_id,
        body.baggage_dimension,
        body.baggage_max_weight,
        body.overweight_fee_per_kg,
    )


@router.delete("/baggage-rules/{rule_id}", dependencies=[_admin])
def remove_baggage_rule(rule_id: int, db: Session = Depends(get_db)):
    return svc.delete_baggage_rule(db, rule_id)


@router.get("/terminal-types", dependencies=[_admin])
def list_terminal_types(db: Session = Depends(get_db)):
    return svc.get_all_terminal_types(db)


@router.post("/terminal-types", dependencies=[_admin])
def add_terminal_type(body: TerminalTypeDTO, db: Session = Depends(get_db)):
    return svc.create_terminal_type(db, body.terminal_type_name)


@router.put("/terminal-types/{terminal_type_id}", dependencies=[_admin])
def edit_terminal_type(terminal_type_id: int, body: TerminalTypeDTO, db: Session = Depends(get_db)):
    return svc.update_terminal_type(db, terminal_type_id, body.terminal_type_name)


@router.delete("/terminal-types/{terminal_type_id}", dependencies=[_admin])
def remove_terminal_type(terminal_type_id: int, db: Session = Depends(get_db)):
    return svc.delete_terminal_type(db, terminal_type_id)