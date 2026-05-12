from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories import reference_crud_repository as repo


def get_all_countries(db: Session) -> list:
    return [
        {"countryId": c.country_id, "countryName": c.country_name}
        for c in repo.get_all_countries(db)
    ]

def create_country(db: Session, country_name: str) -> dict:
    obj = repo.create_country(db, country_name.strip())
    return {"countryId": obj.country_id, "countryName": obj.country_name}

def update_country(db: Session, country_id: int, country_name: str) -> dict:
    obj = repo.update_country(db, country_id, country_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"countryId": obj.country_id, "countryName": obj.country_name}

def delete_country(db: Session, country_id: int) -> dict:
    if not repo.delete_country(db, country_id):
        raise HTTPException(status_code=404, detail="Country not found")
    return {"deleted": True}


def get_all_cities(db: Session) -> list:
    return [
        {
            "cityId": c.city_id,
            "cityName": c.city_name,
            "countryId": c.country_id,
            "countryName": c.country.country_name if c.country else None,
        }
        for c in repo.get_all_cities(db)
    ]

def create_city(db: Session, city_name: str, country_id: int) -> dict:
    obj = repo.create_city(db, city_name.strip(), country_id)
    return {"cityId": obj.city_id, "cityName": obj.city_name, "countryId": obj.country_id}

def update_city(db: Session, city_id: int, city_name: str, country_id: int) -> dict:
    obj = repo.update_city(db, city_id, city_name.strip(), country_id)
    if not obj:
        raise HTTPException(status_code=404, detail="City not found")
    return {"cityId": obj.city_id, "cityName": obj.city_name, "countryId": obj.country_id}

def delete_city(db: Session, city_id: int) -> dict:
    if not repo.delete_city(db, city_id):
        raise HTTPException(status_code=404, detail="City not found")
    return {"deleted": True}


def get_all_classes(db: Session) -> list:
    return [
        {"classId": c.class_id, "className": c.class_name}
        for c in repo.get_all_classes(db)
    ]

def create_class(db: Session, class_name: str) -> dict:
    obj = repo.create_class(db, class_name.strip())
    return {"classId": obj.class_id, "className": obj.class_name}

def update_class(db: Session, class_id: int, class_name: str) -> dict:
    obj = repo.update_class(db, class_id, class_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"classId": obj.class_id, "className": obj.class_name}

def delete_class(db: Session, class_id: int) -> dict:
    if not repo.delete_class(db, class_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return {"deleted": True}


def get_all_baggage_types(db: Session) -> list:
    return [
        {"baggageTypeId": b.baggage_type_id, "baggageTypeName": b.baggage_type_name}
        for b in repo.get_all_baggage_types(db)
    ]

def create_baggage_type(db: Session, baggage_type_name: str) -> dict:
    obj = repo.create_baggage_type(db, baggage_type_name.strip())
    return {"baggageTypeId": obj.baggage_type_id, "baggageTypeName": obj.baggage_type_name}

def update_baggage_type(db: Session, baggage_type_id: int, baggage_type_name: str) -> dict:
    obj = repo.update_baggage_type(db, baggage_type_id, baggage_type_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Baggage type not found")
    return {"baggageTypeId": obj.baggage_type_id, "baggageTypeName": obj.baggage_type_name}

def delete_baggage_type(db: Session, baggage_type_id: int) -> dict:
    if not repo.delete_baggage_type(db, baggage_type_id):
        raise HTTPException(status_code=404, detail="Baggage type not found")
    return {"deleted": True}


def get_all_baggage_rules(db: Session) -> list:
    return [
        {
            "baggagePricingRuleId": r.baggage_pricing_rule_id,
            "baggageTypeId": r.baggage_type_id,
            "baggageTypeName": r.baggage_type.baggage_type_name if r.baggage_type else None,
            "baggageDimension": r.baggage_dimension,
            "baggageMaxWeight": float(r.baggage_max_weight) if r.baggage_max_weight else None,
            "overweightFeePerKg": float(r.overweight_fee_per_kg) if r.overweight_fee_per_kg else None,
        }
        for r in repo.get_all_baggage_rules(db)
    ]

def create_baggage_rule(
    db: Session,
    baggage_type_id: int,
    baggage_dimension: str | None,
    baggage_max_weight: float,
    overweight_fee_per_kg: float,
) -> dict:
    obj = repo.create_baggage_rule(
        db, baggage_type_id, baggage_dimension,
        baggage_max_weight, overweight_fee_per_kg)
    return {"baggagePricingRuleId": obj.baggage_pricing_rule_id}

def update_baggage_rule(
    db: Session,
    rule_id: int,
    baggage_type_id: int,
    baggage_dimension: str | None,
    baggage_max_weight: float,
    overweight_fee_per_kg: float,
) -> dict:
    obj = repo.update_baggage_rule(
        db, rule_id, baggage_type_id, baggage_dimension,
        baggage_max_weight, overweight_fee_per_kg)
    if not obj:
        raise HTTPException(status_code=404, detail="Baggage rule not found")
    return {"baggagePricingRuleId": obj.baggage_pricing_rule_id}

def delete_baggage_rule(db: Session, rule_id: int) -> dict:
    if not repo.delete_baggage_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Baggage rule not found")
    return {"deleted": True}


def get_all_terminal_types(db: Session) -> list:
    return [
        {"terminalTypeId": t.terminal_type_id, "terminalTypeName": t.terminal_type_name}
        for t in repo.get_all_terminal_types(db)
    ]

def get_terminal_type(db: Session, terminal_type_id: int) -> dict:
    obj = repo.get_terminal_type(db, terminal_type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"terminalTypeId": obj.terminal_type_id, "terminalTypeName": obj.terminal_type_name}

def create_terminal_type(db: Session, terminal_type_name: str) -> dict:
    obj = repo.create_terminal_type(db, terminal_type_name.strip())
    return {"terminalTypeId": obj.terminal_type_id, "terminalTypeName": obj.terminal_type_name}

def update_terminal_type(db: Session, terminal_type_id: int, terminal_type_name: str) -> dict:
    obj = repo.update_terminal_type(db, terminal_type_id, terminal_type_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"terminalTypeId": obj.terminal_type_id, "terminalTypeName": obj.terminal_type_name}

def delete_terminal_type(db: Session, terminal_type_id: int) -> dict:
    if not repo.delete_terminal_type(db, terminal_type_id):
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"deleted": True}


